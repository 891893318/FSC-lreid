#!/usr/bin/env python3
"""Summarize anchor sensitivity runs into a compact TSV table."""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


SEEN_MAP_RE = re.compile(r"Average mAP on Seen dataset:\s*([0-9.]+)%")
SEEN_R1_RE = re.compile(r"Average R1 on Seen dataset:\s*([0-9.]+)%")
UNSEEN_MAP_RE = re.compile(r"Average mAP on unSeen dataset:\s*([0-9.]+)%")
UNSEEN_R1_RE = re.compile(r"Average R1 on unSeen dataset:\s*([0-9.]+)%")


def last_match(pattern: re.Pattern[str], text: str) -> str:
    matches = pattern.findall(text)
    return matches[-1] if matches else ""


def read_manifest(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    with path.open(newline="") as handle:
        return {
            row["name"]: row
            for row in csv.DictReader(handle, delimiter="\t")
            if row.get("name")
        }


def summarize(root: Path) -> list[dict[str, str]]:
    manifest = read_manifest(root / "manifest.tsv")
    rows = []
    for log_path in sorted((root / "launch").glob("*.log")):
        name = log_path.name.split("_setting", 1)[0]
        meta = manifest.get(name, {})
        text = log_path.read_text(errors="replace")
        rows.append(
            {
                "name": name,
                "setting": meta.get("setting", ""),
                "seed": meta.get("seed", ""),
                "gpu": meta.get("gpu", ""),
                "anchor_count": meta.get("anchor_count", ""),
                "wording": meta.get("wording", ""),
                "seen_mAP": last_match(SEEN_MAP_RE, text),
                "seen_R1": last_match(SEEN_R1_RE, text),
                "unseen_mAP": last_match(UNSEEN_MAP_RE, text),
                "unseen_R1": last_match(UNSEEN_R1_RE, text),
                "done": "yes" if "Queue done" in text or re.search(r"\] DONE ", text) else "no",
                "launch_log": str(log_path),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root",
        nargs="?",
        default="reproduce/anchor_sensitivity",
        help="anchor sensitivity reproduce root",
    )
    args = parser.parse_args()

    rows = summarize(Path(args.root))
    fields = [
        "name",
        "setting",
        "seed",
        "gpu",
        "anchor_count",
        "wording",
        "seen_mAP",
        "seen_R1",
        "unseen_mAP",
        "unseen_R1",
        "done",
        "launch_log",
    ]
    writer = csv.DictWriter(sys.stdout, fieldnames=fields, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)


if __name__ == "__main__":
    main()
