"""Generate a ready-to-post social snippet from the latest feed."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    feed = json.loads((ROOT / "out" / "macro_snapshot.json").read_text(encoding="utf-8"))
    d = feed["data"]
    lines = [f"Macro snapshot — {d.get('as_of')} ({d.get('regime')})"]
    for i in d.get("indicators", []):
        ch = "" if i.get("change") is None else f" ({'+' if i['change'] >= 0 else ''}{i['change']})"
        lines.append(f"  {i['label']}: {i['value']}{i['unit']}{ch}")
    lines.append("FRED data · not investment advice · arkenlabs.eu")
    text = "\n".join(lines)
    (ROOT / "out" / "post.txt").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
