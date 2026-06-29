"""
Validation module: Compute split‑half reliability for agency‑score marker items.
Adds comprehensive logging for each step and logs warnings if reliability
thresholds are not met (FR‑008).
"""
from __future__ import annotations

import pathlib
from typing import List

import numpy as np
import pandas as pd

from logging.pipeline_logger import get_logger, log_dict

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
RELIABILITY_THRESHOLD = 0.80  # Minimum acceptable reliability

# ----------------------------------------------------------------------
# Logger
# ----------------------------------------------------------------------
_logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def compute_split_half_reliability(
    data_path: pathlib.Path,
) -> float:
    """
    Compute the Spearman‑Brown split‑half reliability for marker items.

    Parameters
    ----------
    data_path: pathlib.Path
        Path to a CSV file containing marker item scores. The file must
        contain only numeric columns representing individual items.

    Returns
    -------
    float
        Reliability coefficient (0‑1). If the computation fails, returns
        ``np.nan`` and logs a warning.
    """
    _logger.info("Starting split‑half reliability computation.")
    try:
        df = pd.read_csv(data_path)
        _logger.debug(f"Loaded data with shape {df.shape} from {data_path}.")
    except Exception as exc:
        _logger.error(f"Failed to read data for reliability: {exc}")
        raise

    # Ensure we have at least two columns to split
    if df.shape[1] < 2:
        _logger.warning(
            "Insufficient columns for split‑half reliability; need at least two."
        )
        return float("nan")

    # Randomly split columns into two halves
    cols = list(df.columns)
    np.random.shuffle(cols)
    half = len(cols) // 2
    left_cols = cols[:half]
    right_cols = cols[half : half * 2]

    left_score = df[left_cols].mean(axis=1)
    right_score = df[right_cols].mean(axis=1)

    # Compute Pearson correlation between halves
    corr = left_score.corr(right_score)
    _logger.debug(f"Half‑score correlation: {corr}")

    # Apply Spearman‑Brown prophecy formula
    reliability = (2 * corr) / (1 + corr) if corr is not None else float("nan")
    log_dict(
        {
            "event": "split_half_reliability_computed",
            "reliability": reliability,
            "data_path": str(data_path),
        }
    )
    _logger.info(f"Computed split‑half reliability: {reliability:.4f}")

    if np.isnan(reliability) or reliability < RELIABILITY_THRESHOLD:
        _logger.warning(
            f"Reliability {reliability:.4f} below threshold {RELIABILITY_THRESHOLD:.2f}"
        )
    return float(reliability)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def parse_args() -> pathlib.Path:
    """Parse command‑line arguments and return the path to the data file."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Compute split‑half reliability for agency marker items."
    )
    parser.add_argument(
        "data_path",
        type=pathlib.Path,
        help="Path to CSV file containing marker item scores.",
    )
    args = parser.parse_args()
    return args.data_path

def main() -> None:
    """CLI entry point."""
    data_path = parse_args()
    reliability = compute_split_half_reliability(data_path)
    print(f"Split‑half reliability: {reliability:.4f}")
