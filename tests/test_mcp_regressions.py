"""Regression checks for the consolidated stdio plotting worker."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("boxplotr_worker", ROOT / "boxplotr_mcp_server.py")
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class MCPRegressionTests(unittest.TestCase):
    def test_tool_discovery(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "boxplotr_mcp_server.py")],
            input=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}) + "\n",
            capture_output=True, text=True, check=True,
        )
        tool = json.loads(result.stdout)["result"]["tools"][0]
        self.assertEqual(tool["name"], "generate_boxplot")
        styling = tool["inputSchema"]["properties"]["styling"]["properties"]
        for option in ("transparent_background", "unfilled_shapes"):
            self.assertEqual(styling[option]["type"], "boolean")
            self.assertFalse(styling[option]["default"])

    def test_transparency_options_reject_non_booleans(self):
        for option in ("transparent_background", "unfilled_shapes"):
            with self.subTest(option=option), self.assertRaisesRegex(ValueError, "must be booleans"):
                worker.generate_plot({"data": "A\n1\n2", "output_path": "/tmp/unused.png",
                                      "styling": {option: "false"}})

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is required")
    def test_transparent_shapes_in_both_engines(self):
        available = subprocess.run(
            ["Rscript", "-e", 'p <- c("beeswarm","vioplot","beanplot","sm","ggplot2","RColorBrewer"); quit(status=if(all(vapply(p,requireNamespace,logical(1),quietly=TRUE))) 0 else 1)'],
            capture_output=True,
        )
        if available.returncode:
            self.skipTest("R plotting packages are not installed")
        with tempfile.TemporaryDirectory() as directory:
            for engine in ("classic", "ggplot2"):
                for kind in ("boxplot", "violin", "beanplot"):
                    with self.subTest(engine=engine, plot_type=kind):
                        output = Path(directory) / f"{engine}-{kind}.svg"
                        worker.generate_plot({
                            "data": "A,B\n1,2\n2,3\n3,4\n4,5\n5,6\n6,7",
                            "visualization": {"plot_engine": engine, "plot_type": kind, "style_guide": "economist"},
                            "styling": {"transparent_background": True, "unfilled_shapes": True},
                            "output_path": str(output),
                        })
                        svg = output.read_bytes()
                        root = ET.fromstring(svg)
                        # R/Cairo versions emit either presentation attributes or CSS styles.
                        paths = [el for el in root.iter() if el.tag.endswith("path") and
                                 ("stroke" in el.attrib or "stroke:" in el.attrib.get("style", ""))]
                        self.assertTrue(paths, "Editable vector outlines are missing")
                        self.assertTrue(any(el.attrib.get("fill") == "none" or
                                            "fill:none" in el.attrib.get("style", "").replace(" ", "")
                                            for el in paths))
                        if engine == "ggplot2" or kind == "boxplot":
                            for path in paths:
                                css_fill = re.search(r"(?:^|;)fill:([^;]+)", path.attrib.get("style", "").replace(" ", ""))
                                fill = path.attrib.get("fill", css_fill.group(1) if css_fill else "none")
                                self.assertEqual(fill, "none", "An exported shape still has a fill")
                        self.assertNotIn(b"89.411765%", svg, "Economist background is still painted")

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is required")
    def test_both_render_paths_use_tukey_whiskers(self):
        scripts = []

        def capture(command, **kwargs):
            scripts.append(Path(command[1]).read_text())
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(worker.subprocess, "run", side_effect=capture):
                worker.generate_plot({"data": "A\n1\n2", "output_path": str(Path(directory) / "test.png")})
        self.assertEqual(scripts[0].count("range = my_range"), 2)
        coefficients = re.findall(r'my_range <- switch\("tukey", tukey = (-?[0-9.]+)', scripts[0])
        self.assertEqual(len(coefficients), 1)
        # Evaluate each actual template coefficient against the standard R
        # Tukey result, including a point that must be classified as an outlier.
        for coefficient in coefficients:
            code = (
                f'source({json.dumps(str(ROOT / "boxplot_stats_Function.R"))}); '
                f'x <- c(1:10, 100); actual <- myboxplot.stats(x, coef={coefficient}); '
                'expected <- grDevices::boxplot.stats(x); '
                'stopifnot(isTRUE(all.equal(unname(actual$stats), expected$stats)), '
                'identical(actual$out, expected$out))'
            )
            subprocess.run(["Rscript", "-e", code], check=True, capture_output=True, text=True)

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is required")
    def test_render_formats_in_both_engines(self):
        available = subprocess.run(
            ["Rscript", "-e", 'p <- c("beeswarm","vioplot","beanplot","sm","ggplot2","RColorBrewer"); quit(status=if(all(vapply(p,requireNamespace,logical(1),quietly=TRUE))) 0 else 1)'],
            capture_output=True,
        )
        if available.returncode:
            self.skipTest("R plotting packages are not installed")
        signatures = {"png": b"\x89PNG\r\n\x1a\n", "pdf": b"%PDF", "svg": b"<?xml"}
        with tempfile.TemporaryDirectory() as directory:
            for engine in ("classic", "ggplot2"):
                for extension, signature in signatures.items():
                    with self.subTest(engine=engine, format=extension):
                        output = Path(directory) / f"{engine}.{extension}"
                        worker.generate_plot({
                            "data": "Control,Treatment\n1,2\n2,3\n3,4\n4,5\n100,6",
                            "visualization": {"plot_engine": engine, "style_guide": "nature"},
                            "styling": {"title": 'A "quoted" title'},
                            "output_path": str(output),
                        })
                        self.assertTrue(output.read_bytes().startswith(signature))


if __name__ == "__main__":
    unittest.main()
