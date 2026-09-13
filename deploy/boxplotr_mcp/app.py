import asyncio
import contextvars
import csv
import hashlib
import hmac
import ipaddress
import io
import json
import os
import secrets
import sqlite3
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Image
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

APP_DIR = Path("/srv/shiny-server/boxplotr")
STATE_DIR = Path("/var/lib/boxplotr-mcp")
DB_PATH = STATE_DIR / "usage.sqlite3"
KEYS_PATH = Path("/etc/boxplotr-mcp/keys.json")
MAX_DATASET_BYTES = 5 * 1024 * 1024
DAILY_LIMIT = 20
MAX_CONCURRENT = 10
EXECUTION_TIMEOUT = 120
OUTPUT_TTL_SECONDS = 3600
MAX_ROWS = 100000
MAX_COLUMNS = 100
MAX_OUTPUT_BYTES = 15 * 1024 * 1024
IDENTITY_SECRET = os.environ.get("MCP_IDENTITY_SECRET", "").encode()
GA4_MEASUREMENT_ID = os.environ.get("GA4_MEASUREMENT_ID", "")
GA4_API_SECRET = os.environ.get("GA4_API_SECRET", "")

sys.path.insert(0, str(APP_DIR))
from boxplotr_mcp_server import generate_plot as legacy_generate_plot  # noqa: E402

client_key_id = contextvars.ContextVar("client_key_id", default="unknown")
slots = asyncio.Semaphore(MAX_CONCURRENT)


def utc_day() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def load_keys() -> dict[str, str]:
    with KEYS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def verify_key(raw_key: str) -> str | None:
    digest = hashlib.sha256(raw_key.encode()).hexdigest()
    for key_id, stored_digest in load_keys().items():
        if secrets.compare_digest(digest, stored_digest):
            return key_id
    with database() as connection:
        row = connection.execute(
            "SELECT key_id FROM api_keys WHERE digest=? AND active=1", (digest,)
        ).fetchone()
    return row[0] if row else None


def anonymous_client_id(request: Request) -> str:
    """Return a privacy-safe quota ID for a client arriving through Apache.

    Apache appends the connecting address to X-Forwarded-For. Using the
    rightmost value prevents a caller-supplied leftmost value from bypassing
    the daily quota. The raw address is never persisted or sent to analytics.
    """
    forwarded_for = request.headers.get("x-forwarded-for", "")
    address = forwarded_for.rsplit(",", 1)[-1].strip() if forwarded_for else ""
    if not address:
        address = request.client.host if request.client else "unknown"
    try:
        address = ipaddress.ip_address(address).compressed
    except ValueError:
        address = "unknown"
    if not IDENTITY_SECRET:
        raise RuntimeError("MCP_IDENTITY_SECRET is not configured")
    digest = hmac.new(IDENTITY_SECRET, address.encode(), hashlib.sha256).hexdigest()
    return f"anonymous:{digest[:32]}"


def database() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS daily_usage (key_id TEXT, day TEXT, calls INTEGER NOT NULL, PRIMARY KEY(key_id, day))"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS events (timestamp TEXT, key_id TEXT, success INTEGER, duration_ms INTEGER, input_bytes INTEGER, rows INTEGER, columns_count INTEGER, plot_type TEXT, plot_engine TEXT, output_format TEXT, error_type TEXT)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS api_keys (key_id TEXT PRIMARY KEY, digest TEXT UNIQUE NOT NULL, email_hash TEXT UNIQUE, created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 0)"
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_digest ON api_keys(digest)")
    return connection


def reserve_daily_call(key_id: str) -> int:
    with database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT calls FROM daily_usage WHERE key_id=? AND day=?", (key_id, utc_day())
        ).fetchone()
        used = row[0] if row else 0
        if used >= DAILY_LIMIT:
            raise RuntimeError("Daily limit reached: 20 plot generations per UTC day")
        remaining = DAILY_LIMIT - used - 1
        connection.execute(
            "INSERT INTO daily_usage(key_id, day, calls) VALUES(?,?,1) ON CONFLICT(key_id,day) DO UPDATE SET calls=calls+1",
            (key_id, utc_day()),
        )
        return remaining


def validate_data(values: str) -> tuple[int, int]:
    if "\x00" in values:
        raise ValueError("Dataset contains a NUL byte")
    lines = values.splitlines()
    delimiter = "\t" if lines and "\t" in lines[0] else ","
    parsed = [row for row in csv.reader(io.StringIO(values), delimiter=delimiter) if any(cell.strip() for cell in row)]
    if len(parsed) < 2 or not parsed[0]:
        raise ValueError("Dataset must contain a header and at least one data row")
    columns, rows = len(parsed[0]), len(parsed) - 1
    if rows > MAX_ROWS or columns > MAX_COLUMNS:
        raise ValueError(f"Dataset is limited to {MAX_ROWS} rows and {MAX_COLUMNS} columns")
    if any(len(row) != columns for row in parsed):
        raise ValueError("Every dataset row must have the same number of columns")
    if any(not name.strip() or len(name) > 100 for name in parsed[0]):
        raise ValueError("Column names must be non-empty and at most 100 characters")
    for row in parsed[1:]:
        for cell in row:
            if not cell.strip() or cell.strip().upper() == "NA":
                continue
            try:
                value = float(cell)
            except ValueError as exc:
                raise ValueError("Data cells must be numeric, blank, or NA") from exc
            if not (-1.7976931348623157e308 <= value <= 1.7976931348623157e308):
                raise ValueError("Data cells must contain finite numeric values")
    return rows, columns

def validate_text(value: str, field: str) -> None:
    if len(value) > 200 or any(ord(char) < 32 and char not in "\t\n\r" for char in value):
        raise ValueError(f"{field} must be at most 200 characters and contain no control characters")


def record_event(**event) -> None:
    with database() as connection:
        connection.execute(
            "INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                event["timestamp"], event["key_id"], int(event["success"]), event["duration_ms"],
                event["input_bytes"], event["rows"], event["columns"], event["plot_type"],
                event["plot_engine"], event["output_format"], event.get("error_type"),
            ),
        )


def send_ga4_event(event: dict) -> None:
    """Send privacy-safe operational telemetry; failures never affect users."""
    if not GA4_MEASUREMENT_ID or not GA4_API_SECRET:
        return
    anonymous_client = hashlib.sha256(
        f"boxplotr-mcp:{event['key_id']}".encode()
    ).hexdigest()[:32]
    payload = {
        "client_id": f"mcp.{anonymous_client}",
        "non_personalized_ads": True,
        "events": [{
            "name": "mcp_plot_generated" if event["success"] else "mcp_plot_failed",
            "params": {
                "app_name": "boxplotr",
                "interface": "mcp",
                "plot_type": event["plot_type"],
                "plot_engine": event["plot_engine"],
                "output_format": event["output_format"],
                "success": int(event["success"]),
                "duration_ms": event["duration_ms"],
                "dataset_bytes": event["input_bytes"],
                "dataset_rows": event["rows"],
                "dataset_columns": event["columns"],
                "error_type": event.get("error_type") or "none",
                "engagement_time_msec": max(1, event["duration_ms"]),
            },
        }],
    }
    request = urllib.request.Request(
        "https://www.google-analytics.com/mp/collect?"
        f"measurement_id={GA4_MEASUREMENT_ID}&api_secret={GA4_API_SECRET}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            response.read()
    except (OSError, urllib.error.URLError):
        pass


def cleanup_outputs() -> None:
    cutoff = time.time() - OUTPUT_TTL_SECONDS
    for path in (STATE_DIR / "output").glob("boxplotr-*.*"):
        try:
            if path.stat().st_mtime < cutoff:
                path.unlink()
        except FileNotFoundError:
            pass


mcp = FastMCP(
    "BoxPlotR",
    instructions="Generate publication-quality box, violin, and bean plots without submitting data through the website.",
    stateless_http=True,
    json_response=True,
    streamable_http_path="/",
    max_request_body_size=6 * 1024 * 1024,
)


@mcp.tool(description="Generate a publication-quality box, violin, or bean plot from column-oriented CSV or TSV data.")
async def generate_boxplot(
    values: str,
    plot_type: str = "boxplot",
    plot_engine: str = "ggplot2",
    style_guide: str = "none",
    orientation: str = "vertical",
    log_scale: bool = False,
    title: str = "",
    x_label: str = "",
    y_label: str = "",
    colors: list[str] | None = None,
    show_points: bool = False,
    add_means: bool = False,
    output_format: str = "png",
) -> list:
    started = time.monotonic()
    key_id = client_key_id.get()
    encoded_size = len(values.encode("utf-8"))
    success = False
    error_type = None
    if encoded_size > MAX_DATASET_BYTES:
        raise ValueError("Dataset exceeds the 5 MB limit")
    rows, columns = validate_data(values)
    if plot_type not in {"boxplot", "violin", "beanplot"}: raise ValueError("Unsupported plot_type")
    if plot_engine not in {"ggplot2", "classic"}: raise ValueError("Unsupported plot_engine")
    if style_guide not in {"none", "nature", "science", "economist", "ft"}: raise ValueError("Unsupported style_guide")
    if orientation not in {"vertical", "horizontal"}: raise ValueError("Unsupported orientation")
    for field, value in (("title", title), ("x_label", x_label), ("y_label", y_label)): validate_text(value, field)
    if colors is not None and (len(colors) > MAX_COLUMNS or any(not isinstance(c, str) or len(c) not in {4, 7, 9} or not c.startswith("#") or any(ch not in "0123456789abcdefABCDEF" for ch in c[1:]) for c in colors)):
        raise ValueError("colors must be hexadecimal CSS colours")
    if output_format not in {"png", "svg", "pdf"}:
        raise ValueError("output_format must be png, svg, or pdf")
    if rows < 1 or columns < 1:
        raise ValueError("Dataset must contain a header and at least one data row")
    remaining = reserve_daily_call(key_id)
    cleanup_outputs()
    output_path = STATE_DIR / "output" / f"boxplotr-{secrets.token_hex(16)}.{output_format}"
    arguments = {
        "data_config": {"values": values},
        "visualization": {
            "plot_type": plot_type, "plot_engine": plot_engine, "style_guide": style_guide,
            "orientation": orientation, "log_scale": log_scale,
        },
        "styling": {"title": title, "xlab": x_label, "ylab": y_label, "colors": colors or []},
        "overlays": {"show_points": show_points, "add_means": add_means},
        "output_path": str(output_path),
    }
    try:
        async with slots:
            await asyncio.wait_for(asyncio.to_thread(legacy_generate_plot, arguments), EXECUTION_TIMEOUT)
        if not output_path.is_file() or output_path.stat().st_size > MAX_OUTPUT_BYTES:
            raise RuntimeError("Generated output is missing or exceeds the 15 MB limit")
        success = True
        content = [f"Plot generated. {remaining} of 20 calls remain today."]
        if output_format == "png":
            content.append(Image(path=str(output_path)))
        else:
            import base64
            content.append({"type": "resource", "mimeType": {"svg":"image/svg+xml","pdf":"application/pdf"}[output_format], "data": base64.b64encode(output_path.read_bytes()).decode()})
        return content
    except Exception as exc:
        error_type = type(exc).__name__
        raise
    finally:
        event = dict(
            timestamp=datetime.now(timezone.utc).isoformat(), key_id=key_id, success=success,
            duration_ms=round((time.monotonic()-started)*1000), input_bytes=encoded_size,
            rows=rows, columns=columns, plot_type=plot_type, plot_engine=plot_engine,
            output_format=output_format, error_type=error_type,
        )
        record_event(**event)
        await asyncio.to_thread(send_ga4_event, event)


class ClientIdentityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)
        authorization = request.headers.get("authorization", "")
        if authorization:
            if not authorization.startswith("Bearer "):
                return JSONResponse({"error": "Unsupported authorization scheme"}, status_code=401)
            key_id = verify_key(authorization[7:].strip())
            if not key_id:
                return JSONResponse({"error": "Invalid API key"}, status_code=403)
        else:
            key_id = anonymous_client_id(request)
        token = client_key_id.set(key_id)
        try:
            return await call_next(request)
        finally:
            client_key_id.reset(token)


async def health(_request: Request):
    return JSONResponse({"status":"ok","service":"boxplotr-mcp","authentication":"optional","anonymous_quota_scope":"hashed_client_ip","max_concurrent":MAX_CONCURRENT,"daily_limit":DAILY_LIMIT,"max_dataset_bytes":MAX_DATASET_BYTES})


app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/mcp", app=mcp.streamable_http_app()),
    ],
    lifespan=lambda _app: mcp.session_manager.run(),
)
app.add_middleware(ClientIdentityMiddleware)
