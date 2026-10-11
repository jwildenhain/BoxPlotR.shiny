"""Verify transparent options reach the worker and analytics stays privacy-safe."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "deploy/boxplotr_mcp/app.py"
if not APP_PATH.exists():
    APP_PATH = Path("/opt/boxplotr-mcp/app.py")
sys.path.insert(0, str(APP_PATH.parent))
spec = importlib.util.spec_from_file_location("boxplotr_gateway", APP_PATH)
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


class GatewayAnalyticsTests(unittest.TestCase):
    def test_ga4_payload_reports_export_options_without_dataset(self):
        event = dict(key_id="private-client", success=True, plot_type="boxplot",
                     plot_engine="ggplot2", output_format="pdf", duration_ms=200,
                     input_bytes=30, rows=5, columns=2, transparent_background=True,
                     unfilled_shapes=True)
        with patch.object(gateway, "GA4_MEASUREMENT_ID", "G-TEST"), \
             patch.object(gateway, "GA4_API_SECRET", "test-only"), \
             patch.object(gateway.urllib.request, "urlopen") as send:
            send.return_value.__enter__.return_value = MagicMock()
            gateway.send_ga4_event(event)
        payload = json.loads(send.call_args.args[0].data)
        self.assertRegex(payload["client_id"], r"^\d+\.\d+$")
        params = payload["events"][0]["params"]
        self.assertGreater(params["session_id"], 0)
        self.assertEqual(payload["events"][0]["name"], "mcp_plot_generated")
        self.assertEqual(params["transparent_background"], 1)
        self.assertEqual(params["unfilled_shapes"], 1)
        self.assertNotIn("private-client", json.dumps(payload))
        for private_field in ("values", "title", "colors", "ip_address", "key_id"):
            self.assertNotIn(private_field, params)

    def test_analytics_failure_does_not_break_exports(self):
        with patch.object(gateway, "GA4_MEASUREMENT_ID", "G-TEST"), \
             patch.object(gateway, "GA4_API_SECRET", "test-only"), \
             patch.object(gateway.urllib.request, "urlopen", side_effect=OSError("offline")):
            gateway.send_ga4_user_activity("boxplotr")


if __name__ == "__main__":
    unittest.main()
