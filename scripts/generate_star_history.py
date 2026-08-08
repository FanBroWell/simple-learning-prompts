"""Generate a self-hosted SVG chart from GitHub's stargazer timestamps."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import tempfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Optional, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GITHUB_API_VERSION = "2022-11-28"
GITHUB_ACCEPT = "application/vnd.github.star+json"
USER_AGENT = "simple-learning-prompts-star-history"
REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def parse_timestamp(value: str) -> datetime:
    """Parse a timezone-aware ISO 8601 timestamp and convert it to UTC."""
    if not isinstance(value, str):
        raise ValueError("Timestamp must be a string")
    normalized_value = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized_value)
    except ValueError as error:
        raise ValueError("Timestamp must be a valid ISO 8601 value") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def build_daily_series(
    stars: Iterable[Mapping[str, object]], today: Optional[date] = None
) -> list[Tuple[date, int]]:
    """Return daily cumulative star counts, including dates with no new stars."""
    if today is None:
        today = date.today()
    if isinstance(today, datetime) or not isinstance(today, date):
        raise ValueError("today must be a date")

    daily_counts: Counter[date] = Counter()
    for star in stars:
        try:
            timestamp = parse_timestamp(star["starred_at"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Each star must include a valid starred_at timestamp") from error
        daily_counts[timestamp.date()] += 1

    if not daily_counts:
        return []

    first_day = min(daily_counts)
    if today < first_day:
        raise ValueError("today cannot be earlier than the first star")

    total = 0
    series = []
    current_day = first_day
    while current_day <= today:
        total += daily_counts[current_day]
        series.append((current_day, total))
        current_day += timedelta(days=1)
    return series


def _format_number(value: int) -> str:
    return f"{value:,}"


def render_svg(
    series: Sequence[Tuple[date, int]], repository: str, width: int = 800, height: int = 450
) -> str:
    """Render a deterministic, accessible light/dark SVG star history chart."""
    if width < 240 or height < 180:
        raise ValueError("SVG dimensions are too small")

    escaped_repository = html.escape(str(repository), quote=True)
    title = f"{escaped_repository} Star History"
    total_stars = series[-1][1] if series else 0
    left, right, top, bottom = 72, 36, 58, 78
    chart_width = width - left - right
    chart_height = height - top - bottom
    baseline = top + chart_height
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="chart-title chart-desc">'
        ),
        "<style>"
        ".chart-bg{fill:#ffffff}.grid{stroke:#d0d7de;stroke-width:1}"
        ".label{fill:#57606a;font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}"
        ".heading{fill:#24292f;font:600 20px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}"
        ".summary{fill:#0969da;font:600 14px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}"
        ".star-area{fill:#54aeff;fill-opacity:.22}.star-line{fill:none;stroke:#0969da;stroke-width:3}"
        "@media (prefers-color-scheme: dark){.chart-bg{fill:#0d1117}.grid{stroke:#30363d}"
        ".label{fill:#8b949e}.heading{fill:#f0f6fc}.summary{fill:#58a6ff}"
        ".star-area{fill:#1f6feb;fill-opacity:.35}.star-line{stroke:#58a6ff}}"
        "</style>",
        f"<title id=\"chart-title\">{title}</title>",
        f"<desc id=\"chart-desc\">Daily cumulative GitHub stars for {escaped_repository}.</desc>",
        f'<rect class="chart-bg" width="{width}" height="{height}" rx="12"/>',
        f'<text class="heading" x="{left}" y="30">{title}</text>',
        f'<text class="summary" x="{left}" y="50">{_format_number(total_stars)} Stars</text>',
    ]

    max_count = max(total_stars, 1)
    for index in range(5):
        count = round(max_count * index / 4)
        y = baseline - chart_height * index / 4
        lines.append(f'<line class="grid" x1="{left}" y1="{y:.2f}" x2="{width - right}" y2="{y:.2f}"/>')
        lines.append(f'<text class="label" x="{left - 10}" y="{y + 4:.2f}" text-anchor="end">{_format_number(count)}</text>')

    if not series:
        lines.append(
            f'<text class="label" x="{width / 2:.2f}" y="{top + chart_height / 2:.2f}" text-anchor="middle">No stars yet</text>'
        )
    else:
        point_count = len(series)
        points = []
        for index, (_, count) in enumerate(series):
            x = left + (chart_width * index / max(point_count - 1, 1))
            y = baseline - (chart_height * count / max_count)
            points.append((x, y))
        line_path = "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in points)
        area_path = (
            f"M {points[0][0]:.2f},{baseline:.2f} L "
            + " L ".join(f"{x:.2f},{y:.2f}" for x, y in points)
            + f" L {points[-1][0]:.2f},{baseline:.2f} Z"
        )
        lines.append(f'<path class="star-area" d="{area_path}"/>')
        lines.append(f'<path class="star-line" d="{line_path}"/>')
        date_label_indices = sorted({0, point_count // 2, point_count - 1})
        for index in date_label_indices:
            x, _ = points[index]
            lines.append(
                f'<text class="label" x="{x:.2f}" y="{baseline + 24:.2f}" text-anchor="middle">{series[index][0].isoformat()}</text>'
            )

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _validate_repository(repository: str) -> None:
    if not isinstance(repository, str) or not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError("repository must be exactly owner/name")


def fetch_stargazers(
    repository: str, token: str, opener: Optional[Callable[..., object]] = None
) -> list[dict]:
    """Fetch all timestamped stargazers from GitHub's REST API."""
    _validate_repository(repository)
    if not isinstance(token, str) or not token.strip():
        raise ValueError("A GitHub token is required")
    if opener is None:
        opener = urlopen

    stargazers = []
    page = 1
    while True:
        query = urlencode({"per_page": 100, "page": page})
        request = Request(
            f"https://api.github.com/repos/{repository}/stargazers?{query}",
            headers={
                "Accept": GITHUB_ACCEPT,
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": GITHUB_API_VERSION,
                "User-Agent": USER_AGENT,
            },
        )
        try:
            with opener(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError) as error:
            raise RuntimeError(f"GitHub stargazer request failed: {error}") from error
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RuntimeError("GitHub stargazer response was not valid JSON") from error

        if not isinstance(payload, list):
            raise RuntimeError("GitHub stargazer response must be a list")
        for stargazer in payload:
            if not isinstance(stargazer, dict) or not isinstance(stargazer.get("starred_at"), str):
                raise RuntimeError("GitHub stargazer response is missing starred_at")
            try:
                parse_timestamp(stargazer["starred_at"])
            except ValueError as error:
                raise RuntimeError("GitHub stargazer response has an invalid starred_at") from error
        stargazers.extend(payload)
        if len(payload) < 100:
            return stargazers
        page += 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Fetch star history and write an SVG file atomically."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY"))
    parser.add_argument("--output", default="assets/star-history.svg")
    arguments = parser.parse_args(argv)
    if not arguments.repo:
        raise RuntimeError("A repository is required via --repo or GITHUB_REPOSITORY")

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")

    stars = fetch_stargazers(arguments.repo, token)
    svg = render_svg(build_daily_series(stars), arguments.repo)
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=output.parent
    )
    temporary_output = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as temporary_file:
            temporary_file.write(svg)
        os.replace(temporary_output, output)
    finally:
        if temporary_output.exists():
            temporary_output.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
