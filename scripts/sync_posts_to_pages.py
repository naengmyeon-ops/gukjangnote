#!/usr/bin/env python3
import pathlib
import shutil
import re

BASE = pathlib.Path(__file__).resolve().parents[1]
SRC = BASE / "posts"
DST = BASE / "site" / "_posts"


def normalize_name(path: pathlib.Path) -> str:
    # Jekyll: YYYY-MM-DD-title.md
    name = path.name
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", name)
    if m:
        date, slug = m.groups()
        slug = re.sub(r"[^a-z0-9-]", "-", slug.lower())
        slug = re.sub(r"-+", "-", slug).strip("-") or "daily-market-brief"
        return f"{date}-{slug}.md"
    return name


def main():
    DST.mkdir(parents=True, exist_ok=True)
    count = 0
    for f in sorted(SRC.glob("*.md")):
        out = DST / normalize_name(f)
        shutil.copyfile(f, out)
        count += 1
    print(f"synced {count} post(s) -> {DST}")


if __name__ == "__main__":
    main()
