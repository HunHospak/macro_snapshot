"""Pure computation for macro_snapshot. No I/O, unit-testable."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _indicator(series: List[Tuple[str, float]], ind: Dict[str, Any]) -> Dict[str, Any] | None:
    if not series:
        return None
    date, val = series[-1]
    if ind.get("yoy"):
        # monthly index -> YoY %. Compare to ~12 observations earlier.
        if len(series) < 13:
            return None
        year_ago = series[-13][1]
        if year_ago == 0:
            return None
        value = round((val / year_ago - 1) * 100, 1)
        prev = series[-14][1] if len(series) >= 14 else None
        prev_yoy = round((series[-2][1] / prev - 1) * 100, 1) if prev else None
        change = round(value - prev_yoy, 1) if prev_yoy is not None else None
    else:
        value = round(val, 2)
        change = round(val - series[-2][1], 2) if len(series) >= 2 else None
    return {
        "id": ind["id"], "label": ind["label"], "unit": ind.get("unit", ""),
        "value": value, "change": change, "as_of": date, "curve": bool(ind.get("curve")),
    }


def build_board(series_map: Dict[str, List[Tuple[str, float]]], cfg: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    inds = cfg.get("indicators", [])
    out: List[Dict[str, Any]] = []
    for ind in inds:
        got = _indicator(series_map.get(ind["id"], []), ind)
        if got:
            out.append(got)

    curve = next((i["value"] for i in out if i.get("curve")), None)
    if curve is None:
        regime = "unknown"
    elif curve < 0:
        regime = "inverted-curve (late-cycle caution)"
    elif curve < 0.5:
        regime = "flat-curve"
    else:
        regime = "normal-curve"

    if not out:
        status, notes = "unavailable", "No FRED series available."
    elif len(out) < max(1, len(inds) // 2):
        status, notes = "partial", "Some FRED series unavailable."
    else:
        status, notes = "active", None

    return {
        "as_of": as_of,
        "indicators": out,
        "yield_curve": curve,
        "regime": regime,
        "_status": status,
        "_notes": notes,
    }
