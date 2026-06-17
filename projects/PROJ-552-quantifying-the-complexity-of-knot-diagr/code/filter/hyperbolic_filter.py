"""
Filter out non‑hyperbolic knots (volume <= 0) and log the exclusions.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

from reproducibility.logs import get_logger, log_operation

CLEANED_PATH = Path("data/processed/knots_cleaned.csv")
FILTERED_PATH = Path("data/processed/knots_hyperbolic.csv")
EXCLUSION_LOG = Path("docs/reproducibility/excluded_knots.md")


@log_operation
def load_cleaned_knots() -> List[dict]:
    """Load the cleaned CSV produced by ``DataSaver``."""
    import pandas as pd

    df = pd.read_csv(CLEANED_PATH)
    return df.to_dict(orient="records")


@log_operation
def parse_hyperbolic_volume(volume_str: str) -> float:
    """Convert the volume field to a float; missing or non‑numeric values become 0.0."""
    try:
        return float(volume_str)
    except Exception:
        return 0.0


@log_operation
def filter_hyperbolic_knots(records: List[dict]) -> Tuple[List[dict], List[dict]]:
    """Return (hyperbolic_records, excluded_records)."""
    hyperbolic = []
    excluded = []
    for rec in records:
        vol = parse_hyperbolic_volume(str(rec.get("volume", "")))
        if vol > 0:
            hyperbolic.append(rec)
        else:
            excluded.append(rec)
    return hyperbolic, excluded


@log_operation
def save_filtered_knots(hyperbolic: List[dict]) -> None:
    """Write the hyperbolic subset to ``FILTERED_PATH``."""
    if not hyperbolic:
        return
    with FILTERED_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=hyperbolic[0].keys())
        writer.writeheader()
        writer.writerows(hyperbolic)


@log_operation
def log_excluded_knots(excluded: List[dict]) -> None:
    """Append a Markdown table of excluded knots to the documentation."""
    EXCLUSION_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EXCLUSION_LOG.open("a", encoding="utf-8") as f:
        f.write("\\n## Excluded Non‑Hyperbolic Knots\\n\\n")
        f.write("| name | volume |\\n")
        f.write("|------|--------|\\n")
        for rec in excluded:
            f.write(f"| {rec.get('name', '')} | {rec.get('volume', '')} |\\n")


@log_operation
def verify_exclusion_count(expected: int) -> bool:
    """Simple sanity check used by the test suite."""
    if not EXCLUSION_LOG.exists():
        return False
    with EXCLUSION_LOG.open() as f:
        lines = f.readlines()
    # Count table rows (skip header lines)
    count = sum(1 for line in lines if line.startswith("| ") and not line.startswith("| name"))
    return count == expected


@log_operation
def main() -> None:  # pragma: no cover
    """Run the hyperbolic filter as a script."""
    records = load_cleaned_knots()
    hyperbolic, excluded = filter_hyperbolic_knots(records)
    save_filtered_knots(hyperbolic)
    log_excluded_knots(excluded)
    get_logger().log("hyperbolic_filter_completed", parameters={"kept": len(hyperbolic), "excluded": len(excluded)})
