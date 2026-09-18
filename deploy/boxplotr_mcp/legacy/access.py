"""Self-service API-key issuance for the BoxPlotR MCP service."""
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone

from starlette.requests import Request
from starlette.responses import HTMLResponse

DB_PATH = "/var/lib/boxplotr-mcp/usage.sqlite3"
TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")
TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")
REQUEST_HASH_SECRET = os.environ.get("REQUEST_HASH_SECRET", "")
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", "BoxPlotR <noreply@chemgrid.org>")
EXPECTED_HOSTNAME = "boxplotr.chemgrid.org"
EXPECTED_ACTION = "request_mcp_key"
EMAIL_DAILY_LIMIT = 50
EMAIL_MONTHLY_LIMIT = 1000
IP_DAILY_LIMIT = 5
EMAIL_COOLDOWN_DAYS = 30
FORM_BODY_LIMIT = 16 * 1024
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def database():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("CREATE TABLE IF NOT EXISTS api_keys (key_id TEXT PRIMARY KEY, digest TEXT UNIQUE NOT NULL, email_hash TEXT UNIQUE, created_at TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 0)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_api_keys_digest ON api_keys(digest)")
    connection.execute("CREATE TABLE IF NOT EXISTS key_requests (id TEXT PRIMARY KEY, email_hash TEXT NOT NULL, ip_hash TEXT NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL, provider_id TEXT)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_key_requests_email ON key_requests(email_hash, created_at)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_key_requests_ip ON key_requests(ip_hash, created_at)")
    connection.execute("CREATE TABLE IF NOT EXISTS email_sends (id TEXT PRIMARY KEY, created_at TEXT NOT NULL, status TEXT NOT NULL)")
    return connection


def keyed_hash(value):
    if not REQUEST_HASH_SECRET:
        raise RuntimeError("Self-service key requests are not configured")
    return hmac.new(REQUEST_HASH_SECRET.encode(), value.encode(), hashlib.sha256).hexdigest()


def client_ip(request):
    forwarded = request.headers.get("x-forwarded-for", "")
    candidate = forwarded.split(",", 1)[0].strip() if forwarded else ""
    return candidate or (request.client.host if request.client else "unknown")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def validate_turnstile(token, remote_ip):
    if not TURNSTILE_SECRET_KEY or len(token) > 2048:
        return False
    payload = urllib.parse.urlencode({
        "secret": TURNSTILE_SECRET_KEY,
        "response": token,
        "remoteip": remote_ip,
        "idempotency_key": str(uuid.uuid4()),
    }).encode()
    request = urllib.request.Request(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded", "User-Agent": "BoxPlotR-MCP/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.loads(response.read())
    except (OSError, ValueError, urllib.error.URLError):
        return False
    return bool(
        result.get("success")
        and result.get("hostname") == EXPECTED_HOSTNAME
        and result.get("action") == EXPECTED_ACTION
    )


def reserve_request(email_hash, ip_hash):
    now = utc_now()
    request_id = str(uuid.uuid4())
    with database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        daily = connection.execute("SELECT count(*) FROM email_sends WHERE created_at >= datetime('now','-1 day')").fetchone()[0]
        monthly = connection.execute("SELECT count(*) FROM email_sends WHERE created_at >= datetime('now','-1 month')").fetchone()[0]
        if daily >= EMAIL_DAILY_LIMIT or monthly >= EMAIL_MONTHLY_LIMIT:
            raise ValueError("The daily or monthly email safety limit has been reached. Please try later.")
        recent_email = connection.execute("SELECT 1 FROM key_requests WHERE email_hash=? AND created_at >= datetime('now',?) AND status IN ('pending','sent') LIMIT 1", (email_hash, f"-{EMAIL_COOLDOWN_DAYS} days")).fetchone()
        if recent_email:
            raise ValueError("A key has already been requested for this email recently. Check your inbox or contact the administrator.")
        recent_ip = connection.execute("SELECT count(*) FROM key_requests WHERE ip_hash=? AND created_at >= datetime('now','-1 day')", (ip_hash,)).fetchone()[0]
        if recent_ip >= IP_DAILY_LIMIT:
            raise ValueError("Too many requests from this network today. Please try tomorrow.")
        connection.execute("INSERT INTO key_requests VALUES(?,?,?,?,?,NULL)", (request_id, email_hash, ip_hash, now, "pending"))
        connection.execute("INSERT INTO email_sends VALUES(?,?,?)", (request_id, now, "reserved"))
    return request_id


def create_pending_key(request_id, email_hash):
    raw_key = "bpr_" + secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw_key.encode()).hexdigest()
    key_id = "self-" + email_hash[:16]
    with database() as connection:
        connection.execute("INSERT OR REPLACE INTO api_keys(key_id,digest,email_hash,created_at,active) VALUES(?,?,?,?,0)", (key_id, digest, email_hash, utc_now()))
    return key_id, raw_key


def send_key_email(recipient, raw_key, request_id):
    if not RESEND_API_KEY:
        raise RuntimeError("Email delivery is not configured")
    text = f"""Your BoxPlotR MCP API key\n\nEndpoint: https://mcp.chemgrid.org/boxplotr/\nAPI key: {raw_key}\n\nKeep this key private. It permits 20 plot generations per UTC day. Datasets are limited to 5 MiB.\n\nCodex setup:\nexport BOXPLOTR_MCP_API_KEY=\"{raw_key}\"\ncodex mcp add boxplotr --url https://mcp.chemgrid.org/boxplotr/ --bearer-token-env-var BOXPLOTR_MCP_API_KEY\n\nIf you did not request this key, delete this message and contact the BoxPlotR administrator.\n"""
    payload = json.dumps({"from": RESEND_FROM, "to": [recipient], "subject": "Your BoxPlotR MCP API key", "text": text}).encode()
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json", "User-Agent": "BoxPlotR-MCP/1.0", "Idempotency-Key": request_id},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        result = json.loads(response.read())
    return result.get("id", "unknown")


def finish_request(request_id, key_id, provider_id=None, success=False):
    with database() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("UPDATE key_requests SET status=?,provider_id=? WHERE id=?", ("sent" if success else "failed", provider_id, request_id))
        connection.execute("UPDATE email_sends SET status=? WHERE id=?", ("sent" if success else "failed", request_id))
        connection.execute("UPDATE api_keys SET active=? WHERE key_id=?", (1 if success else 0, key_id))


def page(message="", error=False):
    notice = f'<div class="notice {"error" if error else "success"}">{html.escape(message)}</div>' if message else ""
    disabled = "" if TURNSTILE_SITE_KEY and RESEND_API_KEY else "disabled"
    return HTMLResponse(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Request a BoxPlotR MCP key</title><script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script><style>body{{font-family:Inter,system-ui,sans-serif;background:#f0f7ff;color:#0f172a;margin:0;padding:32px}}main{{max-width:640px;margin:auto;background:white;padding:32px;border-radius:18px;box-shadow:0 12px 35px #0f172a14}}h1{{margin-top:0}}label{{font-weight:600;display:block;margin:20px 0 8px}}input[type=email]{{width:100%;box-sizing:border-box;padding:12px;border:1px solid #94a3b8;border-radius:8px;font-size:16px}}button{{margin-top:20px;background:#0284c7;color:white;border:0;border-radius:8px;padding:12px 18px;font-weight:700}}button:disabled{{opacity:.45}}.notice{{padding:12px;border-radius:8px;margin:16px 0}}.error{{background:#fee2e2}}.success{{background:#dcfce7}}small{{color:#475569;line-height:1.5;display:block}}</style></head><body><main><h1>Request a BoxPlotR MCP API key</h1><p>A personal key provides up to 20 plot generations per UTC day.</p>{notice}<form method="post" action="/mcp-access/request"><label for="email">Email address</label><input id="email" name="email" type="email" maxlength="254" autocomplete="email" required><label>Human verification</label><div class="cf-turnstile" data-sitekey="{html.escape(TURNSTILE_SITE_KEY)}" data-action="{EXPECTED_ACTION}" data-theme="light"></div><label><input type="checkbox" name="privacy" value="accepted" required> I agree that my email address may be used to deliver and administer my API key.</label><button type="submit" {disabled}>Email my API key</button></form><small>Your email is used only for key delivery, abuse prevention, and access administration. It is converted to a keyed one-way hash in the service database. The address and raw key are sent to Resend for delivery but are not sent to Google Analytics. Requests are limited to one per email every {EMAIL_COOLDOWN_DAYS} days and {IP_DAILY_LIMIT} per network per day. Service-wide email limits are {EMAIL_DAILY_LIMIT}/day and {EMAIL_MONTHLY_LIMIT}/month.</small></main></body></html>""", headers={"Cache-Control":"no-store", "X-Robots-Tag":"noindex, nofollow"})


async def access_page(_request: Request):
    return page()


async def request_key(request: Request):
    body = await request.body()
    if len(body) > FORM_BODY_LIMIT:
        return page("Request too large.", True)
    form = urllib.parse.parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True)
    email = form.get("email", [""])[0].strip().lower()
    token = form.get("cf-turnstile-response", [""])[0]
    if form.get("privacy", [""])[0] != "accepted" or len(email) > 254 or not EMAIL_PATTERN.fullmatch(email):
        return page("Enter a valid email address and accept the privacy notice.", True)
    remote_ip = client_ip(request)
    if not await __import__("asyncio").to_thread(validate_turnstile, token, remote_ip):
        return page("Human verification failed or expired. Please try again.", True)
    email_hash, ip_hash = keyed_hash(email), keyed_hash(remote_ip)
    try:
        request_id = reserve_request(email_hash, ip_hash)
        key_id, raw_key = create_pending_key(request_id, email_hash)
        provider_id = await __import__("asyncio").to_thread(send_key_email, email, raw_key, request_id)
        finish_request(request_id, key_id, provider_id, True)
    except (ValueError, RuntimeError) as exc:
        return page(str(exc), True)
    except (OSError, urllib.error.HTTPError, urllib.error.URLError):
        if "request_id" in locals() and "key_id" in locals():
            finish_request(request_id, key_id, success=False)
        return page("Email delivery is temporarily unavailable. Please contact the administrator.", True)
    return page("Your API key has been emailed. Check your inbox and spam folder.")
