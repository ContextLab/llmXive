"""Group‑wise comparison of alternating vs. non‑alternating knots.

The script computes basic descriptive statistics for the two groups
and writes a markdown summary to
``docs/reproducibility/group_comparison_report.md``.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import numpy as np

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation


def compute_group_stats(df: pd.DataFrame) -> dict:
    """Return mean and std for crossing number and braid index per group."""
    logger = get_logger(__name__)
    groups = {}
    for label, group_df in df.groupby("alternating"):
        stats = {
            "count": int(len(group_df)),
            "crossing_number_mean": float(group_df["crossing_number"].mean()),
            "crossing_number_std": float(group_df["crossing_number"].std(ddof=0)),
            "braid_index_mean": float(group_df["braid_index"].mean()),
            "braid_index_std": float(group_df["braid_index"].std(ddof=0)),
        }
        groups[str(label)] = stats
        logger.debug("Group stats", group=label, stats=stats)
    return groups


def generate_report(stats: dict) -> None:
    """Write a markdown report of the group statistics."""
    output_path = Path("docs/reproducibility/group_comparison_report.md")
    logger = get_logger(__name__)
    logger.debug("Generating group comparison report", output=str(output_path))

    lines = [
        "# Group Comparison Report",
        "",
        "Statistics are provided for alternating (`True`) and "
        "non‑alternating (`False`) knot subsets.",
        "",
    ]
    for group, s in stats.items():
        lines.extend(
            [
                f"## Alternating = {group}",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Count | {s['count']} |",
                f"| Crossing number – mean | {s['crossing_number_mean']:.4f} |",
                f"| Crossing number – std | {s['crossing_number_std']:.4f} |",
                f"| Braid index – mean | {s['braid_index_mean']:.4f} |",
                f"| Braid index – std | {s['braid_index_std']:.4f} |",
                "",
            ]
        )
    md = "\n".join(lines)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    logger.info("Group comparison report written", path=str(output_path))


@log_operation
def main() -> None:  # pragma: no cover
    logger = get_logger(__name__)
    logger.info("Starting group comparison analysis")
    df = load_cleaned_knots()
    stats = compute_group_stats(df)
    generate_report(stats)
    logger.info("Group comparison analysis completed")


if __name__ == "__main__":
    main()
