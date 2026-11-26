"""Pure computation for macro_snapshot. No I/O, unit-testable."""

from __future__ import annotations

from datetime import date as calendar_date
from typing import Any, Dict, List, Tuple


def _month_number(observed: str) -> int:
    day = calendar_date.fromisoformat(observed)
    return day.year * 12 + day.month


def _indicator(series: List[Tuple[str, float]], ind: Dict[str, Any]) -> Dict[str, Any] | None:
    if not series:
        return None
    date, val = series[-1]
    if ind.get("yoy"):
        # A missing release does not move the annual comparison to another month.
        by_month = {_month_number(observed): price for observed, price in series}
        month = _month_number(date)
        year_ago = by_month.get(month - 12)
        if not year_ago:
            return None
        value = round((val / year_ago - 1) * 100, 1)
        prev_value = by_month.get(month - 1)
        prev_base = by_month.get(month - 13)
        prev_yoy = round((prev_value / prev_base - 1) * 100, 1) if prev_value is not None and prev_base else None
        change = round(value - prev_yoy, 1) if prev_yoy is not None else None
    else:
        value = round(val, 2)
        change = round(val - series[-2][1], 2) if len(series) >= 2 else None
    return {
        "id": ind["id"],
        "label": ind["label"],
        "unit": ind.get("unit", ""),
        "value": value,
        "change": change,
        "as_of": date,
        "curve": bool(ind.get("curve")),
    }


def build_board(series_map: Dict[str, List[Tuple[str, float]]], cfg: Dict[str, Any], as_of: str) -> Dict[str, Any]:
    inds = cfg.get("indicators", [])
    out: List[Dict[str, Any]] = []
    missing = []
    missing_yoy_base = []
    for ind in inds:
        series = series_map.get(ind["id"], [])
        got = _indicator(series, ind)
        if got:
            out.append(got)
        elif series and ind.get("yoy"):
            missing_yoy_base.append(f'{ind["id"]} ({series[-1][0][:7]})')
        else:
            missing.append(ind["id"])

    # Embed a short recent series for indicators flagged chart:true (for a line chart).
    n_points = int(cfg.get("chart_points", 90))
    chart_series: Dict[str, Any] = {}
    for ind in inds:
        if ind.get("chart"):
            s = series_map.get(ind["id"], [])
            if s:
                chart_series[ind["id"]] = {
                    "label": ind.get("label", ind["id"]),
                    "points": [[d, round(v, 3)] for d, v in s[-n_points:]],
                }

    curve = next((i["value"] for i in out if i.get("curve")), None)
    if curve is None:
        regime = "unknown"
    elif curve < 0:
        regime = "inverted-curve (late-cycle caution)"
    elif curve < 0.5:
        regime = "flat-curve"
    else:
        regime = "normal-curve"

    limitations = []
    if missing:
        limitations.append("FRED series unavailable: " + ", ".join(sorted(missing)) + ".")
    if missing_yoy_base:
        limitations.append("No usable same-month prior-year observation for " + ", ".join(missing_yoy_base) + ".")
    status = "unavailable" if not out else "partial" if limitations else "active"
    notes = " ".join(limitations) or ("No FRED series available." if not out else None)

    return {
        "as_of": as_of,
        "indicators": out,
        "yield_curve": curve,
        "regime": regime,
        "chart_series": chart_series,
        "_status": status,
        "_notes": notes,
    }
