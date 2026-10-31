import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import layoff_monitor as m


class RecoveryTests(unittest.TestCase):
    def test_dry_run_never_reads_slack_credentials_or_writes_state(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"state.json"
            path.write_text("{}")
            with mock.patch.object(m, "STATE_FILE", path), mock.patch.object(m, "read_secrets", side_effect=AssertionError("credentials must not be read")), mock.patch.object(m, "process_warn", return_value=([], True)), mock.patch.object(m, "process_news", return_value=([], True)):
                self.assertEqual(0, m.main(["--dry-run"]))
            self.assertEqual("{}", path.read_text())

    def test_failed_baseline_preserves_the_original_file(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"state.json"
            original = '{"warn_initialized": true, "news_initialized": true}'
            path.write_text(original)
            with mock.patch.object(m, "STATE_FILE", path), mock.patch.object(m, "process_warn", return_value=([], True)), mock.patch.object(m, "process_news", return_value=([], True)), mock.patch.object(m, "post_slack") as send:
                self.assertEqual(1, m.main(["--seed-only"]))
                send.assert_not_called()
            self.assertEqual(original, path.read_text())

    def test_seed_reloads_warn_and_suppresses_all_delivery(self):
        cfg = m.load_config()

        def warn(state, config):
            self.assertFalse(state["warn_initialized"])
            self.assertEqual({}, state["warn_files"])
            config["_warn_fetch_successes"] = 1
            state["warn_initialized"] = True
            return ["unexpected legacy alert"], True

        def news(state, config, suppressed):
            self.assertFalse(state["news_initialized"])
            config["_news_fetch_successes"] = len(m.build_news_feeds(config))
            state["news_initialized"] = True
            return [], True

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/"state.json"
            path.write_text(json.dumps({"warn_initialized": True, "news_initialized": True,
                                       "warn_files": {"2026": {"etag": "old"}}, "warn_events": {"old": "version"}}))
            with mock.patch.object(m, "STATE_FILE", path), mock.patch.object(m, "load_config", return_value=cfg), mock.patch.object(m, "process_warn", side_effect=warn), mock.patch.object(m, "process_news", side_effect=news), mock.patch.object(m, "read_secrets", side_effect=AssertionError("credentials must not be read")), mock.patch.object(m, "post_slack") as send:
                self.assertEqual(0, m.main(["--seed-only"]))
                send.assert_not_called()
            self.assertEqual({"old": "version"}, json.loads(path.read_text())["warn_events"])

    def test_live_workflow_requires_activation(self):
        workflow = (Path(__file__).parents[1]/".github/workflows/monitor.yml").read_text()
        self.assertIn("vars.MONITOR_ENABLED == 'true'", workflow)
        self.assertIn("default: check", workflow)


if __name__ == "__main__":
    unittest.main()
