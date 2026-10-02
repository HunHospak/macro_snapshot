import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import providers
from compute import build_board


class RecoveryTests(unittest.TestCase):
    def test_parser_rejects_nonfinite_invalid_dates_and_missing_values(self):
        raw = "observation_date,DGS10\n2026-09-30,4.5\n2026-09-31,4\n2026-09-29,NaN\n2026-09-28,inf\n2026-09-27,.\n"
        self.assertEqual(providers.parse_fred_csv(raw), [("2026-09-30", 4.5)])

    def test_bounded_request_retains_only_past_recent_observations(self):
        class Clock(dt.datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2026, 10, 2, tzinfo=dt.timezone.utc)

        cfg = {
            "fred_csv_url": "https://example/{id}?start={start}&end={end}",
            "indicators": [{"id": "DGS10"}],
            "fred_lookback_days": 730,
        }
        with (
            patch.object(providers.dt, "datetime", Clock),
            patch.object(
                providers, "_fetch", return_value="date,value\n1970-01-01,1\n2026-09-30,4\n2099-01-01,9\n"
            ) as fetch,
        ):
            result = providers.gather(cfg)
        self.assertEqual(result["series"]["DGS10"], [("2026-09-30", 4.0)])
        self.assertIn("end=2026-10-02", fetch.call_args.args[0])
        self.assertEqual(fetch.call_args.kwargs["timeout"], 35)

    def test_any_missing_indicator_is_partial_not_active(self):
        cfg = {"indicators": [{"id": "A", "label": "A"}, {"id": "B", "label": "B"}]}
        result = build_board({"A": [("2026-09-30", 4.0)]}, cfg, "2026-10-02")
        self.assertEqual(result["_status"], "partial")
        self.assertIn("B", result["_notes"])

    def test_official_table_parser_uses_only_explicit_finite_observations(self):
        text = (
            '<table><tr><th scope="row">2026-09-30</th><td>4.5</td></tr>'
            "<tr><th>2026-09-29</th><td>4.4</td></tr>"
            "<tr><th>2026-09-28</th><td>NaN</td></tr></table><script>value=999</script>"
        )
        self.assertEqual(providers.parse_fred_table(text), [("2026-09-29", 4.4), ("2026-09-30", 4.5)])
        self.assertEqual(providers.parse_fred_table("<html>No observations</html>"), [])

    def test_embedded_daily_observations_are_not_truncated_to_old_table_rows(self):
        text = '<th>1965-11-01</th><td>4.43</td><div id="extra-rows">#2026-09-30|5.29\n#2026-09-29|.\n</div>'
        self.assertEqual(providers.parse_fred_table(text), [("1965-11-01", 4.43), ("2026-09-30", 5.29)])

    def test_transport_failure_is_explicit_empty_series(self):
        with patch.object(providers.requests, "get", side_effect=providers.requests.ReadTimeout):
            self.assertIsNone(providers._fetch("https://example.com"))


if __name__ == "__main__":
    unittest.main()
