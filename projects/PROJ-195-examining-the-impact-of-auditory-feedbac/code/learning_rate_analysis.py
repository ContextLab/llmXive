"""
Task T032: Implement global learning rate proxy calculation.

Calculates the learning rate slope for each subject using Ordinary Least Squares (OLS)
regression of mean Reaction Time (RT) against trial index.

Input:  data/processed/behavioral_metrics.csv (columns: subject_id, mean_rt, trial_index)
Output: data/processed/learning_rates.csv (columns: subject_id, slope, intercept, r_squared)

Constraint: Regression is performed on ALL trials combined, ignoring condition labels,
to satisfy the "independent of condition" requirement (FR-005).
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "behavioral_metrics.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "learning_rates.csv"


def setup_logging() -> logging.Logger:
    """Configure logging for the analysis script."""
    logger = logging.getLogger("learning_rate_analysis")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        ))
        logger.addHandler(handler)
    return logger


def load_behavioral_metrics(input_path: Path, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Load the behavioral metrics CSV.

    Args:
        input_path: Path to behavioral_metrics.csv
        logger: Logger instance

    Returns:
        DataFrame with columns: subject_id, mean_rt, trial_index

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If required columns are missing
    """
    if logger:
        logger.info(f"Loading behavioral metrics from {input_path}")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T031 has generated data/processed/behavioral_metrics.csv")

    df = pd.read_csv(input_path)

    required_cols = {"subject_id", "mean_rt", "trial_index"}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Input file missing required columns: {missing}. "
                         f"Found columns: {list(df.columns)}")

    if logger:
        logger.info(f"Loaded {len(df)} rows. Subjects: {df['subject_id'].nunique()}")

    return df


def calculate_ols_slope(trial_indices: np.ndarray, rt_values: np.ndarray) -> Tuple[float, float, float]:
    """
    Perform OLS regression of RT against trial index.

    Args:
        trial_indices: Array of trial indices (independent variable)
        rt_values: Array of mean RT values (dependent variable)

    Returns:
        Tuple of (slope, intercept, r_squared)
    """
    if len(trial_indices) < 2:
        # Cannot fit a line with fewer than 2 points
        return np.nan, np.nan, np.nan

    slope, intercept, r_value, p_value, std_err = stats.linregress(trial_indices, rt_values)
    r_squared = r_value ** 2

    return slope, intercept, r_squared


def compute_learning_rates(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Compute learning rate slope for each subject.

    Args:
        df: DataFrame with subject_id, mean_rt, trial_index
        logger: Logger instance

    Returns:
        DataFrame with subject_id, slope, intercept, r_squared
    """
    if logger:
        logger.info("Computing learning rate slopes per subject...")

    results = []

    # Group by subject and calculate slope
    # Note: FR-005 requires "global learning rate slope (independent of condition)"
    # The input data is already aggregated (mean_rt per trial_index per subject),
    # so we simply regress mean_rt against trial_index for all available trials.
    grouped = df.groupby("subject_id")

    for subject_id, group in grouped:
        trials = group["trial_index"].to_numpy()
        rts = group["mean_rt"].to_numpy()

        slope, intercept, r_sq = calculate_ols_slope(trials, rts)

        results.append({
            "subject_id": subject_id,
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_sq
        })

    result_df = pd.DataFrame(results)

    if logger:
        logger.info(f"Computed slopes for {len(result_df)} subjects.")
        # Log some stats about the slopes
        valid_slopes = result_df["slope"].dropna()
        if len(valid_slopes) > 0:
            logger.info(f"Slope stats - Mean: {valid_slopes.mean():.4f}, "
                        f"Std: {valid_slopes.std():.4f}, "
                        f"Min: {valid_slopes.min():.4f}, "
                        f"Max: {valid_slopes.max():.4f}")

    return result_df


def save_learning_rates(result_df: pd.DataFrame, output_path: Path, logger: Optional[logging.Logger] = None) -> None:
    """
    Save the learning rates to CSV.

    Args:
        result_df: DataFrame with results
        output_path: Path to save the CSV
        logger: Logger instance
    """
    if logger:
        logger.info(f"Saving learning rates to {output_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    result_df.to_csv(output_path, index=False)

    if logger:
        logger.info("Save complete.")


def main() -> None:
    """Main entry point for T032."""
    logger = setup_logging()
    logger.info("Starting T032: Global Learning Rate Proxy Calculation")

    try:
        # 1. Load input data
        df = load_behavioral_metrics(INPUT_FILE, logger)

        # 2. Compute learning rates (OLS slope of RT vs Trial Index)
        #    This satisfies the "independent of condition" constraint because
        #    we are regressing all trials combined (the input is already aggregated).
        result_df = compute_learning_rates(df, logger)

        # 3. Save output
        save_learning_rates(result_df, OUTPUT_FILE, logger)

        logger.info("T032 completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Data dependency error: {e}")
        logger.error("Ensure T031 (behavioral metric extraction) has been executed first.")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()