"""
correlation.py

Computes Pearson and Spearman correlation coefficients between the crossing
number and braid index of prime knots.  The results are written to
``docs/reproducibility/correlation_metrics.md``.
"""

import json
from pathlib import Path

import pandas as pd
from scipy.stats import pearsonr, spearmanr

from reproducibility.logs import log_operation, get_logger
from analysis.data_quantities import load_cleaned_knots_data

REPORT_PATH = Path("docs/reproducibility/correlation_metrics.md")


def compute_correlations(df: pd.DataFrame) -> dict:
    """Return Pearson and Spearman correlation results."""
    # Ensure the required columns exist.
    if "crossing_number" not in df.columns or "braid_index" not in df.columns:
        raise ValueError("Dataset must contain 'crossing_number' and 'braid_index' columns.")
    x = df["crossing_number"]
    y = df["braid_index"]
    pearson_r, _ = pearsonr(x, y)
    spearman_r, _ = spearmanr(x, y)
    return {
        "pearson_r": round(float(pearson_r), 4),
        "spearman_r": round(float(spearman_r), 4),
    }


def generate_report(correlations: dict) -> str:
    """Create a Markdown report summarising the correlation metrics."""
    lines = [
        "# Correlation Metrics",
        "",
        "The following table summarises the relationship between crossing number "
        "and braid index for the processed knot dataset.",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Pearson r | {correlations['pearson_r']} |",
        f"| Spearman ρ | {correlations['spearman_r']} |",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    logger = get_logger()
    log_operation(operation="correlation_start", logger=logger)

    df = load_cleaned_knots_data()
    correlations = compute_correlations(df)
    report_md = generate_report(correlations)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_md, encoding="utf-8")

    log_operation(
        operation="correlation_complete",
        output_file=str(REPORT_PATH),
        status="success",
        logger=logger,
    )


if __name__ == "__main__":
    main()
