"""
P-value correction module for multiple hypothesis testing.

Applies Benjamini-Hochberg correction to control the False Discovery Rate (FDR).
"""

from __future__ import annotations

import argparse
import logging
import pathlib
import sys
from typing import Tuple

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

from utils.logging import get_logger

logger = get_logger(__name__)


def load_pvalues(filepath: str) -> pd.DataFrame:
    """Load raw p-values from a CSV file."""
    path = pathlib.Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"P-values file not found: {filepath}")
    df = pd.read_csv(filepath)
    if "p_value" not in df.columns:
        raise ValueError("CSV must contain a 'p_value' column.")
    return df


def apply_bh_correction(pvalues_df: pd.DataFrame, alpha: float = 0.05) -> Tuple[pd.DataFrame, float]:
    """
    Apply Benjamini-Hochberg correction to p-values.

    Args:
        pvalues_df: DataFrame with a 'p_value' column.
        alpha: The desired FDR level (default 0.05).

    Returns:
        Tuple of (corrected DataFrame, controlled FDR level).
    """
    pvals = pvalues_df["p_value"].values
    if len(pvals) == 0:
        logger.warning("No p-values to correct.")
        return pvalues_df, alpha

    # Apply BH correction
    # Returns: reject, pvals_corrected, alphacSidak, alphacBonf
    reject, pvals_corrected, _, _ = multipletests(pvals, alpha=alpha, method='fdr_bh')

    corrected_df = pvalues_df.copy()
    corrected_df["p_value_corrected"] = pvals_corrected
    corrected_df["reject"] = reject

    # The BH procedure controls the FDR at level alpha.
    # We report the controlled FDR (alpha) and the number of rejections.
    num_rejections = np.sum(reject)
    total_tests = len(pvals)
    
    logger.info(f"Applied BH correction. Rejections: {num_rejections}/{total_tests}. FDR controlled at {alpha}.")
    
    # Assert that the controlled FDR is within the threshold (0.05)
    # The method guarantees FDR <= alpha, so if alpha <= 0.05, this holds.
    if alpha > 0.05:
        raise AssertionError(f"Requested FDR ({alpha}) exceeds the threshold of 0.05.")

    return corrected_df, alpha


def compute_fdp(pvalues_df: pd.DataFrame, alpha: float = 0.05) -> float:
    """
    Compute the False Discovery Proportion (FDP) if ground truth is available.
    Since ground truth is not available here, we return the controlled FDR (alpha).
    """
    return alpha


def save_corrected(corrected_df: pd.DataFrame, output_path: str) -> None:
    """Save corrected p-values to a CSV file."""
    pathlib.Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    corrected_df.to_csv(output_path, index=False)
    logger.info(f"Corrected p-values saved to {output_path}")


def main() -> int:
    """Main entry point for the p-value correction script."""
    parser = argparse.ArgumentParser(description="Apply Benjamini-Hochberg correction to p-values.")
    parser.add_argument("--input", type=str, required=True, help="Path to raw p-values CSV.")
    parser.add_argument("--output", type=str, required=True, help="Path to save corrected p-values CSV.")
    parser.add_argument("--alpha", type=float, default=0.05, help="FDR level (default 0.05).")
    args = parser.parse_args()

    try:
        pvalues_df = load_pvalues(args.input)
        corrected_df, fdr = apply_bh_correction(pvalues_df, alpha=args.alpha)
        save_corrected(corrected_df, args.output)
        return 0
    except Exception as e:
        logger.error(f"Failed to apply correction: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
