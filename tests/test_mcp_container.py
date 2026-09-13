#!/usr/bin/env python3
import base64
import json
import sys
import urllib.request

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"

def post(payload):
    request = urllib.request.Request(
        BASE_URL + "/mcp/", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream", "X-Forwarded-For": "127.0.0.1"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=130) as response:
        return json.load(response)

with urllib.request.urlopen(BASE_URL + "/health", timeout=5) as response:
    health = json.load(response)
assert health["status"] == "ok"
assert health["max_concurrent"] == 10
assert health["daily_limit"] == 20

initialized = post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"docker-ci","version":"1"}}})
assert initialized["result"]["serverInfo"]["name"] == "BoxPlotR"

generated = post({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"generate_boxplot","arguments":{"values":"Control,Treatment\n1,2\n2,4\n3,5","plot_type":"boxplot","plot_engine":"ggplot2","colors":["#2563EB","#16A34A"],"title":"Docker MCP test","output_format":"png"}}})
content = generated["result"]["content"]
assert [item["type"] for item in content] == ["text", "image"]
png = base64.b64decode(content[1]["data"])
assert png.startswith(b"\x89PNG\r\n\x1a\n")

rejected = post({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"generate_boxplot","arguments":{"values":"A,B\n1,2","colors":["red\"); system(\"id\"); #"]}}})
assert rejected["result"]["isError"] is True
assert "hexadecimal CSS colours" in rejected["result"]["content"][0]["text"]
print("BoxPlotR MCP container health, protocol, rendering, and injection checks passed")
