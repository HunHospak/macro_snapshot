"""Measured FRED public observation tables / optional CSV. No proxy substitution."""

from __future__ import annotations

import datetime as dt
import logging
import math
import html
import re
import urllib.request
import urllib.error
from typing import Any, Dict, List, Tuple

import requests

_LOG = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/csv,text/plain,*/*",
}


def parse_fred_csv(text: str) -> List[Tuple[str, float]]:
    """Parse fredgraph.csv into [(date, value)] with missing values ('.') skipped. Pure."""
    out: List[Tuple[str, float]] = []
    for i, line in enumerate(text.splitlines()):
        parts = line.split(",")
        if len(parts) < 2:
            continue
        if i == 0 and not parts[0][:4].isdigit():  # header row (DATE/observation_date,...)
            continue
        date, raw = parts[0].strip(), parts[1].strip()
        if not date or raw in ("", "."):
            continue
        try:
            dt.date.fromisoformat(date)
            value = float(raw)
            if math.isfinite(value):
                out.append((date, value))
        except ValueError:
            continue
    return out


def parse_fred_table(text: str) -> List[Tuple[str, float]]:
    """Read explicit date/value cells from the official observation table."""
    pairs = re.findall(r"<th[^>]*>\s*(\d{4}-\d{2}-\d{2})\s*</th>\s*<td[^>]*>\s*([^<]+)\s*</td>", text)
    # Daily series put later observations in an explicit data container, not
    # table cells. Read those literal rows too; never execute page JavaScript.
    extra = re.search(r'<div id="extra-rows">(.*?)</div>', text, re.S)
    if extra:
        pairs.extend(re.findall(r"#(\d{4}-\d{2}-\d{2})\|[ \t]*([^#\r\n]+)", extra.group(1)))
    csv = "date,value\n" + "\n".join(f"{date},{html.unescape(value).strip()}" for date, value in pairs)
    return sorted(parse_fred_csv(csv))


def _fetch_table(url: str, timeout: float) -> str | None:
    request = urllib.request.Request(
        url, headers={"User-Agent": "ArkenLabs-macro-snapshot/1.0 (+https://arkenlabs.eu)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read(2_000_001)
        if len(content) > 2_000_000:
            _LOG.warning("FRED observation table exceeds size budget")
            return None
        return content.decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError) as exc:
        _LOG.warning("FRED observation table failed: %s", type(exc).__name__)
        return None


def _fetch(url: str, timeout: float = 35.0) -> str | None:
    try:
        r = requests.get(url, timeout=timeout, headers=_HEADERS)
    except requests.RequestException as exc:
        _LOG.warning("FRED download failed: %s", type(exc).__name__)
        return None
    if r.status_code != 200:
        _LOG.warning("FRED download HTTP %s", r.status_code)
        return None
    return r.text or None


def gather(cfg: Dict[str, Any]) -> Dict[str, Any]:
    tmpl = cfg["fred_csv_url"]
    series: Dict[str, List[Tuple[str, float]]] = {}
    sources: Dict[str, str] = {}
    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=int(cfg.get("fred_lookback_days", 730)))
    for ind in cfg.get("indicators", []):
        sid = ind["id"]
        timeout = float(cfg.get("fred_timeout_seconds", 35))
        if cfg.get("fred_data_url"):
            sources[sid] = cfg["fred_data_url"].format(id=sid)
            text = _fetch_table(sources[sid], timeout)
            observations = parse_fred_table(text or "")
        else:
            sources[sid] = tmpl.format(id=sid, start=start.isoformat(), end=today.isoformat())
            text = _fetch(sources[sid], timeout=timeout)
            observations = parse_fred_csv(text or "")
        series[sid] = [(date, value) for date, value in observations if start.isoformat() <= date <= today.isoformat()]
    return {"series": series, "source_urls": sources}
