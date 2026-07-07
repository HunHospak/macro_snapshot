# macro_snapshot

Independent ArkenLabs satellite. Publishes a small macro dashboard from **FRED** (keyless CSV):
Treasury yields, the 10Y-2Y curve, fed funds, unemployment and CPI YoY, plus a simple regime read.

## Produces `out/macro_snapshot.json`

`data`:
- `indicators` — `{id, label, unit, value, change, as_of, curve}`
- `yield_curve` — 10Y-2Y spread
- `regime` — normal-curve / flat-curve / inverted-curve (late-cycle caution)

## Data source (no key)

`https://fred.stlouisfed.org/graph/fredgraph.csv?id=<SERIES>` — Federal Reserve (FRED).

## Run locally

```bash
pip install -r requirements.txt
python src/build_feed.py && python scripts/post_text.py
```

## Publish

GitHub Actions publishes `out/` to `gh-pages` (weekdays + manual dispatch). No secrets.

## Not investment advice

Informational macro data.
