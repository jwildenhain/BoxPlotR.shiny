#!/usr/bin/env python3
"""Exercise real HTTP MCP responses, including embedded vector attachments."""
import argparse
import base64
import json
import urllib.request
import xml.etree.ElementTree as ET


def run(mcp_url, health_url, engines):
    def post(payload):
        request = urllib.request.Request(
            mcp_url, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=130) as response:
            return json.load(response)

    with urllib.request.urlopen(health_url, timeout=5) as response:
        health = json.load(response)
    assert health["status"] == "ok"
    assert health["max_concurrent"] == 10
    assert health["daily_limit"] == 20
    assert health["max_dataset_bytes"] == 5 * 1024 * 1024
    assert health["authentication"] == "optional"

    initialized = post({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-06-18", "capabilities": {},
        "clientInfo": {"name": "boxplotr-contract-test", "version": "1"},
    }})
    assert initialized["result"]["serverInfo"]["name"] == "BoxPlotR"
    tools = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
    schema = next(t for t in tools if t["name"] == "generate_boxplot")["inputSchema"]
    assert "output_format" in schema["properties"]
    assert "output_path" not in schema["properties"]

    for engine in engines:
        for separator in (",", "\t"):
            values = "\n".join(separator.join(row) for row in [
                ["Control", "Treatment"], ["1", "2"], ["2", "4"], ["3", "5"], ["100", "6"],
            ])
            for extension, mime in [("png", "image/png"), ("svg", "image/svg+xml"), ("pdf", "application/pdf")]:
                result = post({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {
                    "name": "generate_boxplot", "arguments": {
                        "values": values, "plot_type": "boxplot", "plot_engine": engine,
                        "style_guide": "nature", "colors": ["#2563EB", "#16A34A"],
                        "title": 'MCP test: "CSV and TSV"', "show_points": True,
                        "add_means": True, "output_format": extension,
                    },
                }})["result"]
                assert not result.get("isError"), result
                content = result["content"]
                expected_type = "image" if extension == "png" else "resource"
                assert [item["type"] for item in content] == ["text", expected_type], content
                if extension == "png":
                    attachment = content[1]
                    data = base64.b64decode(attachment["data"], validate=True)
                    assert data.startswith(b"\x89PNG\r\n\x1a\n")
                else:
                    attachment = content[1]["resource"]
                    assert attachment["uri"].endswith("." + extension)
                    data = base64.b64decode(attachment["blob"], validate=True)
                    if extension == "svg":
                        assert ET.fromstring(data).tag == "{http://www.w3.org/2000/svg}svg"
                    else:
                        assert data.startswith(b"%PDF") and b"%%EOF" in data[-1024:]
                assert attachment["mimeType"] == mime
                assert len(data) > 100
                print(f"PASS {engine} {'TSV' if separator == chr(9) else 'CSV'} {extension}: {expected_type} ({len(data)} bytes)", flush=True)

    matrix_cases = [
        ("boxplot", "classic", "png", "none", "vertical", False, "tukey"),
        ("boxplot", "ggplot2", "svg", "nature", "horizontal", True, "spear"),
        ("violin", "classic", "pdf", "science", "horizontal", False, "altman"),
        ("violin", "ggplot2", "png", "economist", "vertical", True, "tukey"),
        ("beanplot", "classic", "svg", "ft", "vertical", True, "spear"),
        ("beanplot", "ggplot2", "pdf", "none", "horizontal", False, "altman"),
    ]
    for request_id, (plot_type, engine, extension, style, orientation, log_scale, whisker_type) in enumerate(matrix_cases, 10):
        result = post({"jsonrpc": "2.0", "id": request_id, "method": "tools/call", "params": {
            "name": "generate_boxplot", "arguments": {
                "values": "Control,Treatment\n1,2\n2,4\n3,5\n4,6",
                "plot_type": plot_type, "plot_engine": engine,
                "style_guide": style, "orientation": orientation,
                "log_scale": log_scale, "whisker_type": whisker_type,
                "colors": ["#176B87", "#D97706"],
                "title": f"{plot_type} {engine} {extension}", "show_points": True,
                "add_means": plot_type == "boxplot", "output_format": extension,
            },
        }})["result"]
        assert not result.get("isError"), result
        content = result["content"]
        if extension == "png":
            data = base64.b64decode(content[1]["data"], validate=True)
            assert content[1]["mimeType"] == "image/png"
            assert data.startswith(b"\x89PNG\r\n\x1a\n")
        else:
            resource = content[1]["resource"]
            data = base64.b64decode(resource["blob"], validate=True)
            assert resource["mimeType"] == {"svg": "image/svg+xml", "pdf": "application/pdf"}[extension]
            assert ET.fromstring(data).tag == "{http://www.w3.org/2000/svg}svg" if extension == "svg" else data.startswith(b"%PDF")
        print(f"PASS matrix {plot_type} {engine} {extension} {style} {orientation} log={log_scale} whiskers={whisker_type}", flush=True)

    rejected_whiskers = post({"jsonrpc": "2.0", "id": 20, "method": "tools/call", "params": {
        "name": "generate_boxplot", "arguments": {"values": "A,B\n1,2", "whisker_type": "unsupported"},
    }})
    assert rejected_whiskers["result"]["isError"] is True
    assert "whisker_type" in rejected_whiskers["result"]["content"][0]["text"]

    rejected = post({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
        "name": "generate_boxplot", "arguments": {"values": "A,B\n1,2", "colors": ['red"); system("id"); #']},
    }})
    assert rejected["result"]["isError"] is True
    assert "hexadecimal CSS colours" in rejected["result"]["content"][0]["text"]
    print("PASS health, tool schema, initialization, and invalid-input rejection")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url", nargs="?", default="http://127.0.0.1:8765")
    parser.add_argument("--mcp-url")
    parser.add_argument("--health-url")
    parser.add_argument("--engines", nargs="+", choices=["classic", "ggplot2"], default=["classic", "ggplot2"])
    args = parser.parse_args()
    run(args.mcp_url or args.base_url.rstrip("/") + "/mcp/",
        args.health_url or args.base_url.rstrip("/") + "/health", args.engines)
