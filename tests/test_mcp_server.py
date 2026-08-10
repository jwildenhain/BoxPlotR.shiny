import importlib.util
import os
import tempfile
import unittest

MODULE_PATH = os.path.join(os.path.dirname(__file__), "..", "boxplotr_mcp_server.py")
spec = importlib.util.spec_from_file_location("boxplotr_mcp_server", MODULE_PATH)
boxplotr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boxplotr)


class GeneratePlotTests(unittest.TestCase):
    def base_arguments(self, output_path, engine="classic"):
        return {
            "data_config": {"values": "SampleA,SampleB\n1,2\n2,4\n4,8\n8,16"},
            "visualization": {
                "plot_type": "boxplot",
                "plot_engine": engine,
                "orientation": "vertical",
                "log_scale": False,
            },
            "styling": {"title": "Regression test", "colors": ["#88CCEE", "#CC6677"]},
            "overlays": {"show_points": True, "notch": True},
            "output_path": output_path,
        }

    def test_generates_classic_and_ggplot_pngs(self):
        with tempfile.TemporaryDirectory() as tmp:
            for engine in ("classic", "ggplot2"):
                output = os.path.join(tmp, f"{engine}.png")
                self.assertEqual(boxplotr.generate_plot(self.base_arguments(output, engine)), output)
                self.assertGreater(os.path.getsize(output), 1000)

    def test_quoted_text_is_data_not_r_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "safe.png")
            sentinel = os.path.join(tmp, "injected.txt")
            args = self.base_arguments(output, "ggplot2")
            args["styling"]["title"] = f'Plot"); writeLines("owned", "{sentinel}"); #'
            args["styling"]["colors"] = ['red"); writeLines("owned", "' + sentinel + '"); #']
            self.assertEqual(boxplotr.generate_plot(args), output)
            self.assertGreater(os.path.getsize(output), 1000)
            self.assertFalse(os.path.exists(sentinel))

    def test_rejects_invalid_enum_and_output_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = self.base_arguments(os.path.join(tmp, "plot.png"))
            args["visualization"]["plot_engine"] = 'ggplot2"); system("id"); #'
            with self.assertRaisesRegex(ValueError, "Invalid plot_engine"):
                boxplotr.generate_plot(args)
            args = self.base_arguments(os.path.join(tmp, "plot.pdf"))
            with self.assertRaisesRegex(ValueError, "must end in .png"):
                boxplotr.generate_plot(args)


if __name__ == "__main__":
    unittest.main()
