"""
group_comparison.py

Produces descriptive comparison statistics between alternating and
non‑alternating knots (means, variances, Cohen's d, etc.).  The output is
written to ``docs/reproducibility/group_comparison.md``.
"""

import json
from pathlib import Path

import pandas as pd
import numpy as np

from reproducibility.logs import log_operation, get_logger
from analysis.data_quantities import load_cleaned_knots_data

REPORT_PATH = Path("docs/reproducibility/group_comparison.md")


def _cohens_d(x: pd.Series, y: pd.Series) -> float:
    """Calculate Cohen's d for two samples."""
    nx = len(x)
    ny = len(y)
    dof = nx + ny - 2
    pooled_std = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / dof)
    if pooled_std == 0:
        return 0.0
    return (x.mean() - y.mean()) / pooled_std


def compute_group_stats(df: pd.DataFrame) -> dict:
    """Return a dictionary with statistics for alternating vs non‑alternating groups."""
    if "alternating" not in df.columns:
        raise ValueError("Dataset must contain an 'alternating' column.")
    alt = df[df["alternating"] == True]
    non_alt = df[df["alternating"] == False]

    stats = {
        "alternating": {
            "count": int(alt.shape[0]),
            "crossing_mean": round(float(alt["crossing_number"].mean()), 3),
            "braid_mean": round(float(alt["braid_index"].mean()), 3),
            "crossing_var": round(float(alt["crossing_number"].var()), 3),
            "braid_var": round(float(alt["braid_index"].var()), 3),
        },
        "non_alternating": {
            "count": int(non_alt.shape[0]),
            "crossing_mean": round(float(non_alt["crossing_number"].mean()), 3),
            "braid_mean": round(float(non_alt["braid_index"].mean()), 3),
            "crossing_var": round(float(non_alt["crossing_number"].var()), 3),
            "braid_var": round(float(non_alt["braid_index"].var()), 3),
        },
    }

    # Cohen's d for crossing number and braid index.
    stats["cohens_d_crossing"] = round(
        _cohens_d(alt["crossing_number"], non_alt["crossing_number"]), 4
    )
    stats["cohens_d_braid"] = round(
        _cohens_d(alt["braid_index"], non_alt["braid_index"]), 4
    )
    return stats


def generate_report(stats: dict) -> str:
    """Render a Markdown report from the statistics dictionary."""
    lines = [
        "# Group Comparison Report",
        "",
        "## Alternating Knots",
        f"- Count: {stats['alternating']['count']}",
        f"- Mean crossing number: {stats['alternating']['crossing_mean']}",
        f"- Mean braid index: {stats['alternating']['braid_mean']}",
        f"- Crossing variance: {stats['alternating']['crossing_var']}",
        f"- Braid variance: {stats['alternating']['braid_var']}",
        "",
        "## Non‑Alternating Knots",
        f"- Count: {stats['non_alternating']['count']}",
        f"- Mean crossing number: {stats['non_alternating']['crossing_mean']}",
        f"- Mean braid index: {stats['non_alternating']['braid_mean']}",
        f"- Crossing variance: {stats['non_alternating']['crossing_var']}",
        f"- Braid variance: {stats['non_alternating']['braid_var']}",
        "",
        "## Effect Sizes",
        f"- Cohen's d (crossing number): {stats['cohens_d_crossing']}",
        f"- Cohen's d (braid index): {stats['cohens_d_braid']}",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    logger = get_logger()
    log_operation(operation="group_comparison_start", logger=logger)

    df = load_cleaned_knots_data()
    stats = compute_group_stats(df)
    report_md = generate_report(stats)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_md, encoding="utf-8")

    log_operation(
        operation="group_comparison_complete",
        output_file=str(REPORT_PATH),
        status="success",
        logger=logger,
    )


if __name__ == "__main__":
    main()
