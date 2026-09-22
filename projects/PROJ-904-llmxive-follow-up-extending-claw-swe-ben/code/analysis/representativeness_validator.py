"""
RepresentativenessValidator module.

Performs Kolmogorov-Smirnov (KS) tests to compare the distribution of
line counts and issue types in the filtered dataset vs. the full raw dataset.
Fails the run if the p-value < 0.05, indicating insufficient representativeness.
"""

import os
import sys
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import get_data_dir, get_output_dir, set_global_seeds
from utils.logger import setup_logger, log_error, AnalysisError

logger = setup_logger("RepresentativenessValidator")


def load_parquet_dataset(path: Path) -> pd.DataFrame:
    """
    Load a parquet dataset from disk.

    Args:
        path: Path to the parquet file.

    Returns:
        DataFrame containing the dataset.

    Raises:
        AnalysisError: If the file does not exist or cannot be read.
    """
    if not path.exists():
        raise AnalysisError(f"Dataset file not found: {path}")

    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded dataset from {path}: {len(df)} rows")
        return df
    except Exception as e:
        log_error(logger, f"Failed to load dataset from {path}", e)
        raise AnalysisError(f"Failed to load dataset: {e}")


def calculate_line_counts(df: pd.DataFrame, context_col: str = "context") -> np.ndarray:
    """
    Calculate line counts for each instance in the dataset.

    Args:
        df: DataFrame containing the dataset.
        context_col: Name of the column containing context data.

    Returns:
        Array of line counts.
    """
    if context_col not in df.columns:
        # If context is not a direct column, assume 'relevant_files' or similar structure
        # For this implementation, we assume a 'line_count' column exists if context is complex
        if 'line_count' in df.columns:
            logger.info("Using 'line_count' column directly.")
            return df['line_count'].values
        else:
            # Fallback: estimate based on string length if it's a string context
            logger.warning(f"Column '{context_col}' not found or not numeric. Estimating line counts.")
            # This is a heuristic fallback; in a real scenario, we'd parse the structure
            if context_col in df.columns:
                return df[context_col].astype(str).apply(lambda x: x.count('\n') + 1).values
            else:
                raise AnalysisError(f"Cannot calculate line counts. Missing column '{context_col}' or 'line_count'.")

    return df[context_col].apply(lambda x: len(x.split('\n')) if isinstance(x, str) else 0).values


def get_issue_types(df: pd.DataFrame, type_col: str = "issue_type") -> np.ndarray:
    """
    Extract issue types from the dataset for categorical comparison.

    Args:
        df: DataFrame containing the dataset.
        type_col: Name of the column containing issue types.

    Returns:
        Array of issue types (encoded as integers for KS test).
    """
    if type_col not in df.columns:
        # Fallback: try 'category' or 'type'
        for fallback in ['category', 'type', 'label']:
            if fallback in df.columns:
                logger.info(f"Using '{fallback}' column for issue types.")
                type_col = fallback
                break
        else:
            raise AnalysisError(f"Cannot find issue type column. Expected '{type_col}' or fallbacks.")

    # Encode categorical types as integers for KS test
    unique_types = df[type_col].unique()
    type_map = {t: i for i, t in enumerate(unique_types)}
    return df[type_col].map(type_map).values


def perform_ks_test(
    sample_data: np.ndarray,
    population_data: np.ndarray,
    test_name: str
) -> Tuple[float, float]:
    """
    Perform a Kolmogorov-Smirnov test.

    Args:
        sample_data: Data from the filtered (sample) dataset.
        population_data: Data from the full (population) dataset.
        test_name: Name of the metric being tested (for logging).

    Returns:
        Tuple of (KS statistic, p-value).
    """
    if len(sample_data) == 0 or len(population_data) == 0:
        raise AnalysisError(f"Cannot perform KS test on empty data for {test_name}")

    ks_stat, p_value = stats.ks_2samp(sample_data, population_data)
    logger.info(f"KS Test for {test_name}: Statistic={ks_stat:.4f}, p-value={p_value:.4f}")
    return ks_stat, p_value


def validate_representativeness(
    raw_path: Path,
    filtered_path: Path,
    alpha: float = 0.05
) -> bool:
    """
    Validate that the filtered dataset is representative of the raw dataset.

    Args:
        raw_path: Path to the raw dataset parquet file.
        filtered_path: Path to the filtered dataset parquet file.
        alpha: Significance level for the KS test.

    Returns:
        True if the filtered dataset is representative (p-value >= alpha).

    Raises:
        AnalysisError: If the representativeness check fails (p-value < alpha).
    """
    logger.info("Starting representativeness validation...")

    # Load datasets
    raw_df = load_parquet_dataset(raw_path)
    filtered_df = load_parquet_dataset(filtered_path)

    # Check required columns
    required_cols = ['line_count', 'issue_type'] # Assuming these exist based on T012 logic
    missing_raw = [c for c in required_cols if c not in raw_df.columns]
    missing_filtered = [c for c in required_cols if c not in filtered_df.columns]

    if missing_raw:
        # Try to calculate if missing
        if 'line_count' not in raw_df.columns:
            logger.info("Calculine line counts for raw dataset...")
            raw_df['line_count'] = calculate_line_counts(raw_df)
        if 'issue_type' not in raw_df.columns:
            # Fallback logic if column is missing entirely
            logger.warning("Issue type column missing in raw dataset. Using a placeholder.")
            raw_df['issue_type'] = 'unknown'

    if missing_filtered:
        if 'line_count' not in filtered_df.columns:
            logger.info("Calculating line counts for filtered dataset...")
            filtered_df['line_count'] = calculate_line_counts(filtered_df)
        if 'issue_type' not in filtered_df.columns:
            logger.warning("Issue type column missing in filtered dataset. Using a placeholder.")
            filtered_df['issue_type'] = 'unknown'


    # 1. Test Line Counts Distribution
    logger.info("Comparing line count distributions...")
    try:
        ks_stat_lines, p_val_lines = perform_ks_test(
            filtered_df['line_count'].values,
            raw_df['line_count'].values,
            "Line Counts"
        )
    except Exception as e:
        log_error(logger, "Line count KS test failed", e)
        raise AnalysisError(f"Line count KS test failed: {e}")

    # 2. Test Issue Types Distribution
    logger.info("Comparing issue type distributions...")
    try:
        # Encode types
        all_types = set(raw_df['issue_type'].unique()) | set(filtered_df['issue_type'].unique())
        type_map = {t: i for i, t in enumerate(all_types)}
        raw_types = raw_df['issue_type'].map(type_map).values
        filt_types = filtered_df['issue_type'].map(type_map).values

        ks_stat_types, p_val_types = perform_ks_test(
            filt_types,
            raw_types,
            "Issue Types"
        )
    except Exception as e:
        log_error(logger, "Issue type KS test failed", e)
        raise AnalysisError(f"Issue type KS test failed: {e}")

    # Check significance
    logger.info(f"Significance level (alpha): {alpha}")
    if p_val_lines < alpha:
        msg = f"Insufficient Context-Bound Data: Line count distribution differs significantly (p={p_val_lines:.4f} < {alpha})."
        logger.error(msg)
        raise AnalysisError(msg)

    if p_val_types < alpha:
        msg = f"Insufficient Context-Bound Data: Issue type distribution differs significantly (p={p_val_types:.4f} < {alpha})."
        logger.error(msg)
        raise AnalysisError(msg)

    logger.info("Representativeness validation PASSED.")
    return True


def main():
    """
    Main entry point for the RepresentativenessValidator.
    """
    parser = argparse.ArgumentParser(description="Validate representativeness of filtered dataset.")
    parser.add_argument("--raw-path", type=str, required=True, help="Path to raw dataset parquet file.")
    parser.add_argument("--filtered-path", type=str, required=True, help="Path to filtered dataset parquet file.")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance level for KS test.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")

    args = parser.parse_args()

    set_global_seeds(args.seed)
    raw_path = Path(args.raw_path)
    filtered_path = Path(args.filtered_path)

    try:
        validate_representativeness(raw_path, filtered_path, args.alpha)
        logger.info("Validation successful. Exiting with code 0.")
        sys.exit(0)
    except AnalysisError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(logger, "Unexpected error during validation", e)
        sys.exit(1)


if __name__ == "__main__":
    main()