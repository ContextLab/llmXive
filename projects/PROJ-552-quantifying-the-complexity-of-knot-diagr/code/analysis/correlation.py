"""Correlation analysis between core knot invariants.

The module computes Pearson and Spearman correlations between the
crossing number and braid index, and writes a short markdown report to
``docs/reproducibility/correlation_metrics.md``.
"""
from __future__ import annotations

import pandas as pd
from pathlib import Path

from analysis._utils import load_cleaned_knots
from reproducibility.logs import get_logger, log_operation

from scipy.stats import spearmanr


def compute_correlations(df: pd.DataFrame) -> dict:
    """Return Pearson and Spearman correlation statistics."""
    logger = get_logger(__name__)
    logger.debug("Computing Pearson correlation")
    pearson_r = df["crossing_number"].corr(df["braid_index"])

    logger.debug("Computing Spearman correlation")
    spearman_r, spearman_p = spearmanr(df["crossing_number"], df["braid_index"])

    result = {
        "pearson_r": float(pearson_r),
        "spearman_rho": float(spearman_r),
        "spearman_p": float(spearman_p),
    }
    logger.info("Correlation results", **result)
    return result


def generate_report(corr: dict) -> None:
    """Write a markdown report summarising the correlation metrics."""
    output_path = Path("docs/reproducibility/correlation_metrics.md")
    logger = get_logger(__name__)
    logger.debug("Generating correlation report", output=str(output_path))

    md = (
        "# Correlation Metrics\n\n"
        "This report summarises the relationship between the crossing number\n"
        "and braid index for the processed knot dataset.\n\n"
        "| Metric | Value |\n"
        "|--------|-------|\n"
        f"| Pearson r | {corr['pearson_r']:.4f} |\n"
        f"| Spearman rho | {corr['spearman_rho']:.4f} |\n"
        f"| Spearman p‑value | {corr['spearman_p']:.4e} |\n"
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    logger.info("Correlation report written", path=str(output_path))


@log_operation
def main() -> None:  # pragma: no cover
    logger = get_logger(__name__)
    logger.info("Starting correlation analysis")
    df = load_cleaned_knots()
    corr = compute_correlations(df)
    generate_report(corr)
    logger.info("Correlation analysis completed")


if __name__ == "__main__":
    main()
