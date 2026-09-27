"""Benjamini-Hochberg correction for multiple comparisons."""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Import the project's custom logger factory (defined in utils/logging.py)
from utils.logging import get_logger


def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def setup_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """Set up a standard logging.Logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def run_benjamini_hochberg(
    p_values: np.ndarray,
    alpha: float = 0.05,
    method: str = "indep"
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.

    Uses statsmodels.stats.multitest.multipletests.

    Args:
        p_values: Array of raw p-values.
        alpha: Significance level (default 0.05).
        method: Method for correction ('indep' for independent tests,
                'neg' for non-positive dependent tests).

    Returns:
        Tuple of (reject, p_corrected, p_corrected_lower, p_corrected_upper)
        as returned by statsmodels.
    """
    from statsmodels.stats.multitest import multipletests

    if len(p_values) == 0:
        return np.array([]), np.array([]), np.array([]), np.array([])

    reject, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method=method)
    
    # statsmodels returns (reject, p_corrected, _, _)
    # We return the corrected p-values and the rejection mask
    return reject, p_corrected, np.array([]), np.array([])


def main() -> int:
    """Main entry point for Benjamini-Hochberg correction task."""
    logger = setup_logger("benjamini_hochberg")
    logger.info("Starting Benjamini-Hochberg correction pipeline.")

    # Paths
    input_file = "data/analysis/raw_correlation_results.csv"
    output_file = "data/analysis/bh_corrected_pvalues.csv"
    config_path = "code/config.yaml"

    # Load config to get alpha if specified
    try:
        config = load_config(config_path)
        alpha = config.get("alpha", 0.05)
    except Exception as e:
        logger.warning(f"Could not load config for alpha, using default 0.05: {e}")
        alpha = 0.05

    # Validate input file exists
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please ensure T020a (Raw Correlation Calculation) has been run successfully.")
        return 1

    try:
        # Load raw correlation results
        df = pd.read_csv(input_file)
        logger.info(f"Loaded {len(df)} raw correlation results from {input_file}")

        # Verify required columns
        required_cols = ["p_value"]
        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            logger.error(f"Missing required columns in {input_file}: {missing_cols}")
            return 1

        # Extract p-values
        p_values = df["p_value"].values

        # Apply BH correction
        reject, p_corrected, _, _ = run_benjamini_hochberg(p_values, alpha=alpha)

        # Create output DataFrame
        output_df = df.copy()
        output_df["p_corrected"] = p_corrected
        output_df["reject_bh"] = reject

        # Save to disk
        output_df.to_csv(output_file, index=False)
        logger.info(f"Successfully wrote BH-corrected results to {output_file}")
        logger.info(f"Significant findings at alpha={alpha}: {sum(reject)} out of {len(reject)}")

        return 0

    except Exception as e:
        logger.error(f"Error during BH correction: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
