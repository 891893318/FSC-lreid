#!/usr/bin/env python3
"""Summarize K25/default anchor results over seeds 0--6."""
from __future__ import annotations

import argparse
import re
import statistics
import sys
from pathlib import Path


PATTERNS = {
    "seen_mAP": re.compile(r"Average mAP on Seen dataset:\s*([0-9.]+)%"),
    "seen_R1": re.compile(r"Average R1 on Seen dataset:\s*([0-9.]+)%"),
    "unseen_mAP": re.compile(r"Average mAP on unSeen dataset:\s*([0-9.]+)%"),
    "unseen_R1": re.compile(r"Average R1 on unSeen dataset:\s*([0-9.]+)%"),
}


def last_value(pattern: re.Pattern[str], text: str) -> str:
    matches = pattern.findall(text)
    return matches[-1] if matches else ""


def log_for_seed(seed: int, seed0_root: Path, repeat_root: Path) -> Path:
    if seed == 0:
        return seed0_root / "launch" / "K25_default_setting2_seed0.log"
    return repeat_root / "launch" / f"K25_default_s{seed}_setting2_seed{seed}.log"


def parse_log(path: Path) -> dict[str, str]:
    if not path.exists():
        return {key: "" for key in PATTERNS} | {"done": "no", "log": str(path)}
    text = path.read_text(errors="replace")
    row = {key: last_value(pattern, text) for key, pattern in PATTERNS.items()}
    row["done"] = "yes" if re.search(r"\] DONE ", text) else "no"
    row["log"] = str(path)
    return row


def fmt_mean_std(values: list[float]) -> str:
    if not values:
        return ""
    if len(values) == 1:
        return f"{values[0]:.1f}"
    return f"{statistics.mean(values):.2f}+-{statistics.stdev(values):.2f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed0-root", default="reproduce/anchor_sensitivity")
    parser.add_argument("--repeat-root", default="reproduce/anchor_seed_repeats")
    parser.add_argument("--seeds", default="0,1,2,3,4,5,6")
    args = parser.parse_args()

    seeds = [int(item) for item in args.seeds.split(",") if item.strip()]
    rows = []
    for seed in seeds:
        path = log_for_seed(seed, Path(args.seed0_root), Path(args.repeat_root))
        row = {"seed": str(seed)} | parse_log(path)
        rows.append(row)

    fields = ["seed", "seen_mAP", "seen_R1", "unseen_mAP", "unseen_R1", "done", "log"]
    print("\t".join(fields))
    for row in rows:
        print("\t".join(row[field] for field in fields))

    metric_values = {}
    for key in PATTERNS:
        metric_values[key] = [
            float(row[key]) for row in rows
            if row[key] and row["done"] == "yes"
        ]
    print("")
    print("metric\tmean+-std_completed")
    for key in ["seen_mAP", "seen_R1", "unseen_mAP", "unseen_R1"]:
        print(f"{key}\t{fmt_mean_std(metric_values[key])}")

    incomplete = [row["seed"] for row in rows if row["done"] != "yes"]
    if incomplete:
        print("", file=sys.stderr)
        print("Incomplete seeds: {}".format(",".join(incomplete)), file=sys.stderr)


if __name__ == "__main__":
    main()
