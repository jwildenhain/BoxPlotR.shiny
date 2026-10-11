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
    for option in ("transparent_background", "unfilled_shapes"):
        assert schema["properties"][option]["type"] == "boolean"
        assert schema["properties"][option]["default"] is False
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

    # Use a coloured style to catch backgrounds that override transparency.
    for engine in engines:
        result = post({"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {
            "name": "generate_boxplot", "arguments": {
                "values": "A,B\n1,2\n2,3\n3,4\n4,5", "plot_engine": engine,
                "style_guide": "economist", "output_format": "svg",
                "transparent_background": True, "unfilled_shapes": True,
            },
        }})["result"]
        assert not result.get("isError"), result
        svg = base64.b64decode(result["content"][1]["resource"]["blob"], validate=True)
        root = ET.fromstring(svg)
        assert b"89.411765%" not in svg, "Economist background is still painted"
        paths = [el for el in root.iter() if el.tag.endswith("path") and ("stroke" in el.attrib or "stroke:" in el.attrib.get("style", ""))]
        assert any(el.attrib.get("fill") == "none" or "fill:none" in el.attrib.get("style", "").replace(" ", "") for el in paths), "Missing editable unfilled paths"
        for path in paths:
            fill = path.attrib.get("fill")
            if fill is not None:
                assert fill == "none", "An HTTP-exported box still has a fill"
            else:
                assert "fill:none" in path.attrib.get("style", "").replace(" ", ""), "An HTTP-exported box still has a fill"
        print(f"PASS {engine} transparent, unfilled HTTP SVG", flush=True)

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
