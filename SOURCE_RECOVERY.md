# FRED recovery (2026-10-02)

CSV downloads stalled upstream, including bounded requests. Default ingestion now
uses the official keyless FRED observation tables at `fred.stlouisfed.org/data/<id>`.
Only explicit date/value table cells and literal rows in the official `extra-rows`
data container are parsed. Daily series must include that container to avoid
truncating their history to the oldest table rows. No JavaScript is executed;
no page summaries, proxies, API credentials or fabricated values are used. The exact source URLs
are included in the feed. HTML downloads have a 2 MB size budget and 35-second
read timeout. Transport failures log their exception class, never credentials.

Observations are restricted to the last 730 days and exclude future/invalid dates
and nonfinite values. This retains monthly YoY and 90-point daily chart inputs;
existing formulas are unchanged. Explicit legacy CSV configuration remains supported
with bounded `cosd`/`coed` requests. Any missing configured indicator makes the feed
partial with missing IDs in notes; zero indicators remains unavailable.

Individual indicator `as_of` is the actual FRED observation/reference date, not the
feed generation time. This is current auxiliary research, not a historical PIT vintage.
