#!/usr/bin/env python3
"""Issue, list, and revoke BoxPlotR MCP API keys."""
import argparse
import hashlib
import json
import os
import secrets
import tempfile
from pathlib import Path

KEYS_PATH = Path("/etc/boxplotr-mcp/keys.json")


def load_keys():
    return json.loads(KEYS_PATH.read_text(encoding="utf-8")) if KEYS_PATH.exists() else {}


def save_keys(keys):
    existing = KEYS_PATH.stat() if KEYS_PATH.exists() else None
    fd, temporary = tempfile.mkstemp(dir=KEYS_PATH.parent, prefix="keys.", text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(keys, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.chmod(temporary, 0o640)
        if existing:
            os.chown(temporary, existing.st_uid, existing.st_gid)
        os.replace(temporary, KEYS_PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


parser = argparse.ArgumentParser(description="Manage BoxPlotR MCP API keys")
commands = parser.add_subparsers(dest="command", required=True)
issue = commands.add_parser("issue", help="Create a key and display it once")
issue.add_argument("label", help="Unique non-sensitive user or organisation label")
revoke = commands.add_parser("revoke", help="Immediately revoke a key")
revoke.add_argument("label")
commands.add_parser("list", help="List labels; secret values are never displayed")
args = parser.parse_args()
keys = load_keys()

if args.command == "list":
    print("\n".join(sorted(keys)))
elif args.command == "revoke":
    if args.label not in keys:
        raise SystemExit(f"Unknown key label: {args.label}")
    del keys[args.label]
    save_keys(keys)
    print(f"Revoked {args.label}")
else:
    if args.label in keys:
        raise SystemExit(f"Key label already exists: {args.label}")
    raw_key = "bpr_" + secrets.token_urlsafe(32)
    keys[args.label] = hashlib.sha256(raw_key.encode()).hexdigest()
    save_keys(keys)
    print(raw_key)
