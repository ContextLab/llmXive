"""
Validation script for the attachment‑proxy extraction accuracy.

This script compares the automatically computed attachment anxiety and
avoidance scores against a manually annotated validation set of 20 users.
It computes Cohen's κ for each score (treated as a binary classification
using a threshold of 0.5) and records the average κ.  If the average κ is
below 0.8 the script aborts with a ``RuntimeError`` indicating that the
validation has failed.

The script writes a YAML file ``data/validation/attachment_proxy_kappa.yaml``
containing the κ value and a ``pass`` flag.

Expected inputs:
  * Automated scores: ``data/processed/attachment_scores.parquet``
    (produced by ``src.features.attachment_proxy``).
  * Manual annotations: ``data/validation/attachment_proxy_manual.parquet``
    (must contain the same ``user_id`` column and the two score columns
    ``attachment_anxiety_score`` and ``attachment_avoidance_score``).

The script is invoked directly via the test suite or the quick‑start
pipeline; it returns exit code 0 on success and 1 on failure.
"""

import sys
import logging
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score

# Project utilities
from llmxive_toolkit import paths, get_logger
from src.utils.logging import (
    log_stage_start,
    log_stage_end,
    log_error_context,
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
AUTOMATED_PATH = paths.data("processed", "attachment_scores.parquet")
MANUAL_PATH = paths.data("validation", "attachment_proxy_manual.parquet")
OUTPUT_PATH = paths.data("validation", "attachment_proxy_kappa.yaml")
KAPPA_THRESHOLD = 0.80
# Binary threshold for turning a continuous score into a class label.
SCORE_THRESHOLD = 0.5

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _load_scores(path: Path, required_columns: set) -> pd.DataFrame:
    """
    Load a Parquet file and verify that the required columns exist.

    Parameters
    ----------
    path : Path
        Path to the Parquet file.
    required_columns : set
        Columns that must be present in the DataFrame.

    Returns
    -------
    pd.DataFrame
    """
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    df = pd.read_parquet(path)
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(
            f"File {path} is missing required columns: {missing}"
        )
    return df


def _binarize(series: pd.Series) -> pd.Series:
    """
    Convert a continuous 0‑1 score series into a binary label using
    ``SCORE_THRESHOLD``. Values >= threshold become 1, otherwise 0.
    """
    return (series >= SCORE_THRESHOLD).astype(int)


def _compute_average_kappa(
    auto_df: pd.DataFrame, manual_df: pd.DataFrame
) -> float:
    """
    Compute Cohen's κ for anxiety and avoidance scores separately,
    then return the arithmetic mean of the two κ values.

    Both DataFrames must contain ``user_id`` and the two score columns.
    """
    # Align on user_id
    merged = pd.merge(
        auto_df,
        manual_df,
        on="user_id",
        suffixes=("_auto", "_manual"),
        how="inner",
    )
    if merged.empty:
        raise RuntimeError("No overlapping user IDs between automated and manual sets.")

    # Binarise the scores
    anxiety_auto = _binarize(merged["attachment_anxiety_score_auto"])
    anxiety_manual = _binarize(merged["attachment_anxiety_score_manual"])

    avoidance_auto = _binarize(merged["attachment_avoidance_score_auto"])
    avoidance_manual = _binarize(merged["attachment_avoidance_score_manual"])

    kappa_anxiety = cohen_kappa_score(anxiety_manual, anxiety_auto)
    kappa_avoidance = cohen_kappa_score(avoidance_manual, avoidance_auto)

    logger.info(f"Cohen κ (anxiety): {kappa_anxiety:.4f}")
    logger.info(f"Cohen κ (avoidance): {kappa_avoidance:.4f}")

    return (kappa_anxiety + kappa_avoidance) / 2.0


# ----------------------------------------------------------------------
# Main validation routine
# ----------------------------------------------------------------------


def validate_attachment_proxy() -> dict:
    """
    Perform the validation of the attachment‑proxy extraction.

    Returns
    -------
    dict
        Dictionary with keys ``kappa`` (float) and ``pass`` (bool).
    """
    log_stage_start(logger, "validate_attachment_proxy")

    required_cols = {
        "user_id",
        "attachment_anxiety_score",
        "attachment_avoidance_score",
    }

    # Load automated and manual scores
    auto_df = _load_scores(AUTOMATED_PATH, required_cols)
    manual_df = _load_scores(MANUAL_PATH, required_cols)

    # Compute average κ
    avg_kappa = _compute_average_kappa(auto_df, manual_df)

    passed = avg_kappa >= KAPPA_THRESHOLD
    if not passed:
        raise RuntimeError(
            f"Attachment Proxy Validation Failed: κ={avg_kappa:.4f} < {KAPPA_THRESHOLD}"
        )

    # Prepare report
    report = {
        "kappa": round(avg_kappa, 4),
        "pass": passed,
    }

    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Write YAML report
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(report, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Attachment‑proxy validation report written to {OUTPUT_PATH}")

    log_stage_end(logger, "validate_attachment_proxy", success=True)

    return report


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> int:
    """
    Command‑line entry point used by the quickstart and tests.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on failure.
    """
    try:
        validate_attachment_proxy()
        print("Attachment‑proxy validation passed.")
        return 0
    except Exception as exc:
        log_error_context(logger, "Attachment‑proxy validation failed", error=exc)
        print(f"Attachment‑proxy validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())