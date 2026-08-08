"""Tests for the self-hosted GitHub star history generator."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from scripts import generate_star_history as generator


class Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


class RawResponse(Response):
    def __init__(self, payload):
        self.payload = payload


class ParseTimestampTests(unittest.TestCase):
    def test_parses_github_timestamp_and_normalizes_to_utc(self):
        parsed = generator.parse_timestamp("2026-02-03T01:30:00+02:00")
        self.assertEqual(parsed.isoformat(), "2026-02-02T23:30:00+00:00")

    def test_rejects_non_string_naive_and_invalid_timestamps(self):
        for value in (None, 2, "2026-02-03T01:30:00", "not-a-timestamp"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    generator.parse_timestamp(value)


class DailySeriesTests(unittest.TestCase):
    def test_aggregates_stars_fills_gaps_and_calculates_cumulative_counts(self):
        series = generator.build_daily_series(
            [
                {"starred_at": "2026-01-01T22:00:00Z"},
                {"starred_at": "2026-01-02T01:00:00+02:00"},
                {"starred_at": "2026-01-03T10:00:00Z"},
            ],
            today=date(2026, 1, 4),
        )
        self.assertEqual(
            series,
            [
                (date(2026, 1, 1), 2),
                (date(2026, 1, 2), 2),
                (date(2026, 1, 3), 3),
                (date(2026, 1, 4), 3),
            ],
        )

    def test_returns_empty_series_when_there_are_no_stars(self):
        self.assertEqual(generator.build_daily_series([], today=date(2026, 1, 1)), [])

    def test_defaults_to_the_current_utc_date(self):
        observed_timezones = []

        class HostLocalDate(date):
            @classmethod
            def today(cls):
                return cls(2026, 1, 2)

        class UtcDateTime(datetime):
            @classmethod
            def now(cls, timezone_value=None):
                observed_timezones.append(timezone_value)
                return cls(2026, 1, 3, tzinfo=generator.timezone.utc)

            def date(self):
                return HostLocalDate(self.year, self.month, self.day)

        with patch.object(generator, "date", HostLocalDate), patch.object(
            generator, "datetime", UtcDateTime
        ):
            self.assertEqual(
                generator.build_daily_series([{"starred_at": "2026-01-01T00:00:00Z"}]),
                [(date(2026, 1, 1), 1), (date(2026, 1, 2), 1), (date(2026, 1, 3), 1)],
            )
        self.assertEqual(observed_timezones, [generator.timezone.utc])

    def test_rejects_invalid_today_values(self):
        stars = [{"starred_at": "2026-01-02T00:00:00Z"}]
        for invalid_today in (date(2026, 1, 1), "2026-01-02", datetime(2026, 1, 2)):
            with self.subTest(today=invalid_today):
                with self.assertRaises(ValueError):
                    generator.build_daily_series(stars, today=invalid_today)


class RenderSvgTests(unittest.TestCase):
    def test_renders_accessible_deterministic_chart_with_escaped_repository(self):
        series = [(date(2026, 1, 1), 1), (date(2026, 1, 2), 3)]
        svg = generator.render_svg(series, "owner/<repo&>")
        self.assertEqual(svg, generator.render_svg(series, "owner/<repo&>"))
        self.assertIn('role="img"', svg)
        self.assertIn("owner/&lt;repo&amp;&gt; Star History", svg)
        self.assertIn("3 Stars", svg)
        self.assertIn('class="star-area"', svg)
        self.assertIn('class="star-line"', svg)
        self.assertIn("2026-01-01", svg)
        self.assertIn(">3<", svg)
        self.assertIn("prefers-color-scheme: dark", svg)

    def test_renders_empty_state_without_data_paths(self):
        svg = generator.render_svg([], "owner/repo")
        self.assertIn("0 Stars", svg)
        self.assertIn("No stars yet", svg)
        self.assertNotIn('class="star-area"', svg)
        self.assertNotIn('class="star-line"', svg)

    def test_uses_unique_integer_y_axis_labels_for_low_star_totals(self):
        svg = generator.render_svg([(date(2026, 1, 1), 1)], "owner/repo")
        y_axis_labels = re.findall(
            r'<text class="label" x="62"[^>]*text-anchor="end">([^<]+)</text>', svg
        )
        self.assertEqual(y_axis_labels, ["0", "1"])

    def test_renders_a_visible_marker_for_a_one_point_series(self):
        svg = generator.render_svg([(date(2026, 1, 1), 1)], "owner/repo")
        self.assertIn('class="star-point"', svg)


class FetchStargazersTests(unittest.TestCase):
    def test_fetches_pages_with_required_request_headers_and_timeout(self):
        requests = []
        pages = [
            [{"starred_at": "2026-01-01T00:00:00Z"}] * 100,
            [{"starred_at": "2026-01-02T00:00:00Z"}],
        ]

        def opener(request, timeout):
            requests.append((request, timeout))
            return Response(pages[len(requests) - 1])

        stars = generator.fetch_stargazers("owner/repo", "secret", opener=opener)
        self.assertEqual(len(stars), 101)
        self.assertEqual(len(requests), 2)
        self.assertIn("per_page=100&page=1", requests[0][0].full_url)
        self.assertIn("per_page=100&page=2", requests[1][0].full_url)
        self.assertEqual(requests[0][1], 30)
        self.assertEqual(requests[0][0].get_header("Accept"), "application/vnd.github.star+json")
        self.assertEqual(requests[0][0].get_header("Authorization"), "Bearer secret")
        self.assertEqual(requests[0][0].get_header("X-github-api-version"), "2022-11-28")
        self.assertEqual(requests[0][0].get_header("User-agent"), "simple-learning-prompts-star-history")

    def test_rejects_invalid_repository_missing_token_and_missing_timestamp(self):
        with self.assertRaises(ValueError):
            generator.fetch_stargazers("owner/repo/extra", "token")
        with self.assertRaises(ValueError):
            generator.fetch_stargazers("owner/repo", "")
        with self.assertRaises(RuntimeError):
            generator.fetch_stargazers(
                "owner/repo", "token", opener=lambda _request, timeout: Response([{}])
            )
        with self.assertRaises(RuntimeError):
            generator.fetch_stargazers(
                "owner/repo", "token", opener=lambda _request, timeout: Response([{"starred_at": "bad"}])
            )

    def test_converts_network_errors_to_readable_runtime_errors(self):
        def broken_opener(_request, timeout):
            raise URLError("connection refused")

        with self.assertRaisesRegex(RuntimeError, "GitHub"):
            generator.fetch_stargazers("owner/repo", "token", opener=broken_opener)

    def test_converts_http_errors_to_readable_runtime_errors(self):
        def broken_opener(_request, timeout):
            raise HTTPError("https://api.github.com", 500, "server error", {}, None)

        with self.assertRaisesRegex(RuntimeError, "GitHub"):
            generator.fetch_stargazers("owner/repo", "token", opener=broken_opener)

    def test_rejects_malformed_json_responses(self):
        with self.assertRaisesRegex(RuntimeError, "valid JSON"):
            generator.fetch_stargazers(
                "owner/repo", "token", opener=lambda _request, timeout: RawResponse(b"not json")
            )

    def test_fetches_an_empty_followup_page_for_exact_page_sizes(self):
        requests = []
        pages = [[{"starred_at": "2026-01-01T00:00:00Z"}] * 100, []]

        def opener(request, timeout):
            requests.append(request)
            return Response(pages[len(requests) - 1])

        stars = generator.fetch_stargazers("owner/repo", "token", opener=opener)
        self.assertEqual(len(stars), 100)
        self.assertEqual(len(requests), 2)
        self.assertIn("page=2", requests[1].full_url)


class MainTests(unittest.TestCase):
    def test_main_generates_svg_using_patched_fetcher(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "nested" / "history.svg"
            original_replace = os.replace
            replacements = []

            def capture_replace(source, destination):
                replacements.append((Path(source), Path(destination)))
                original_replace(source, destination)

            with patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=False):
                with patch.object(
                    generator,
                    "fetch_stargazers",
                    return_value=[{"starred_at": "2026-01-01T00:00:00Z"}],
                ) as fetch, patch.object(generator.os, "replace", side_effect=capture_replace):
                    result = generator.main(["--repo", "owner/repo", "--output", str(output)])
            self.assertEqual(result, 0)
            fetch.assert_called_once_with("owner/repo", "token")
            self.assertIn("owner/repo Star History", output.read_text(encoding="utf-8"))
            self.assertEqual(replacements[0][1], output)
            self.assertEqual(replacements[0][0].parent, output.parent)
            self.assertTrue(replacements[0][0].name.endswith(".tmp"))
            self.assertNotEqual(replacements[0][0].name, "history.svg.tmp")
            self.assertFalse(list(output.parent.glob("*.tmp")))

    def test_main_ignores_a_temporary_file_disappearing_during_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "history.svg"
            original_exists = Path.exists
            original_unlink = Path.unlink

            def temporary_file_appears_present(path):
                if path.name.endswith(".tmp"):
                    return True
                return original_exists(path)

            def temporary_file_vanishes_before_unlink(path, *args, **kwargs):
                if path.name.endswith(".tmp"):
                    raise FileNotFoundError
                return original_unlink(path, *args, **kwargs)

            with patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=False), patch.object(
                generator, "fetch_stargazers", return_value=[]
            ), patch.object(Path, "exists", new=temporary_file_appears_present), patch.object(
                Path, "unlink", new=temporary_file_vanishes_before_unlink
            ):
                self.assertEqual(generator.main(["--repo", "owner/repo", "--output", str(output)]), 0)
            self.assertTrue(output.exists())

    def test_main_keeps_existing_output_and_removes_temp_file_after_a_write_failure(self):
        class FailingWritableFile:
            def __init__(self, descriptor):
                self.descriptor = descriptor

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                os.close(self.descriptor)
                return False

            def write(self, _contents):
                raise OSError("write failed")

        def failing_fdopen(descriptor, *args, **kwargs):
            return FailingWritableFile(descriptor)

        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "history.svg"
            output.write_text("previous chart", encoding="utf-8")
            with patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=False), patch.object(
                generator, "fetch_stargazers", return_value=[]
            ), patch.object(generator.os, "fdopen", side_effect=failing_fdopen):
                with self.assertRaisesRegex(OSError, "write failed"):
                    generator.main(["--repo", "owner/repo", "--output", str(output)])
            self.assertEqual(output.read_text(encoding="utf-8"), "previous chart")
            self.assertFalse(list(output.parent.glob("*.tmp")))

    def test_main_closes_the_raw_descriptor_when_opening_the_temp_file_fails(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "history.svg"
            temporary_output = Path(temporary_directory) / ".history.svg.test.tmp"
            with patch.dict(os.environ, {"GITHUB_TOKEN": "token"}, clear=False), patch.object(
                generator, "fetch_stargazers", return_value=[]
            ), patch.object(generator.tempfile, "mkstemp", return_value=(99, str(temporary_output))), patch.object(
                generator.os, "fdopen", side_effect=OSError("open failed")
            ), patch.object(generator.os, "close") as close:
                with self.assertRaisesRegex(OSError, "open failed"):
                    generator.main(["--repo", "owner/repo", "--output", str(output)])
            close.assert_called_once_with(99)

    def test_main_requires_a_github_token(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "GITHUB_TOKEN"):
                generator.main(["--repo", "owner/repo"])


if __name__ == "__main__":
    unittest.main()
