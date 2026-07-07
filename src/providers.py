"""Ingest: FRED keyless CSV endpoint. Defensive — failures yield empty series."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

import requests

_HEADERS = {"User-Agent": "arkenlabs-macro-snapshot/1.0"}


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
            out.append((date, float(raw)))
        except ValueError:
            continue
    return out


def _fetch(url: str, timeout: float = 12.0) -> str | None:
    try:
        r = requests.get(url, timeout=timeout, headers=_HEADERS)
    except Exception:
        return None
    return r.text if (r.status_code == 200 and r.text) else None


def gather(cfg: Dict[str, Any]) -> Dict[str, Any]:
    tmpl = cfg["fred_csv_url"]
    series: Dict[str, List[Tuple[str, float]]] = {}
    for ind in cfg.get("indicators", []):
        sid = ind["id"]
        text = _fetch(tmpl.format(id=sid))
        series[sid] = parse_fred_csv(text) if text else []
    return {"series": series}
