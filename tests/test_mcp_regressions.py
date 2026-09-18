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
        self.assertEqual(json.loads(result.stdout)["result"]["tools"][0]["name"], "generate_boxplot")

    @unittest.skipUnless(shutil.which("Rscript"), "Rscript is required")
    def test_both_render_paths_use_tukey_whiskers(self):
        scripts = []

        def capture(command, **kwargs):
            scripts.append(Path(command[1]).read_text())
            return subprocess.CompletedProcess(command, 0, "", "")

        with tempfile.TemporaryDirectory() as directory:
            with patch.object(worker.subprocess, "run", side_effect=capture):
                worker.generate_plot({"data": "A\n1\n2", "output_path": str(Path(directory) / "test.png")})
        coefficients = re.findall(r"range = (-?[0-9.]+)", scripts[0])
        self.assertEqual(len(coefficients), 2)
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
