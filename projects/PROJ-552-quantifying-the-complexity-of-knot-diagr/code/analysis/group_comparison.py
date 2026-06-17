from __future__ import annotations
import json
from pathlib import Path

import pandas as pd
import numpy as np

from reproducibility.logs import get_logger, log_operation

@log_operation
def compute_group_stats(df: pd.DataFrame) -> dict:
    """Compute summary statistics for alternating vs non‑alternating knots."""
    # Normalize column names to lower case
    df = df.rename(columns=lambda c: c.lower())

    # Ensure the 'alternating' column exists
    if "alternating" not in df.columns:
        raise KeyError("Column 'alternating' not found in dataset.")

    # Map various truthy representations to boolean
    df["alternating_bool"] = df["alternating"].astype(str).str.upper().map(
        {"Y": True, "N": False, "TRUE": True, "FALSE": False}
    )

    groups = {"alternating": df[df["alternating_bool"] == True], "non_alternating": df[df["alternating_bool"] == False]}

    stats = {}
    for name, group in groups.items():
        stats[name] = {
            "count": int(group.shape[0]),
            "crossing_number_mean": float(group["crossing_number"].mean()),
            "braid_index_mean": float(group["braid_index"].mean()),
            "volume_mean": float(group["volume"].mean()),
        }
    return stats

@log_operation
def generate_report(stats: dict, output_path: Path) -> None:
    """Write group comparison statistics to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

def main() -> None:
    logger = get_logger()
    logger.info("Running group comparison analysis")
    from analysis._utils import load_cleaned_knots

    df = load_cleaned_knots()
    stats = compute_group_stats(df)
    out_path = Path("data/processed/group_comparison_report.json")
    generate_report(stats, out_path)
    logger.info(f"Group comparison report written to {out_path}")

if __name__ == "__main__":
    main()
