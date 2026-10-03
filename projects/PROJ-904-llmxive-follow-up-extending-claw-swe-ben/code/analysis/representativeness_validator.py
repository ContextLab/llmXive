"""
Representativeness Validator for T054.

Implements a Kolmogorov-Smirnov (KS) test to compare the distribution of
`line_count` in the filtered dataset against a sample from the raw dataset.
Ensures the filtered set is representative of the full population.
"""
import os
import sys
import logging
import argparse
import hashlib
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import numpy as np
from scipy import stats

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def load_parquet_dataset(path: Path) -> pd.DataFrame:
    """
    Load a Parquet dataset into a Pandas DataFrame.

    Args:
        path: Path to the Parquet file.

    Returns:
        DataFrame containing the dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be read.
    """
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")

    try:
        df = pd.read_parquet(path)
        logger.info(f"Loaded {len(df)} rows from {path}")
        return df
    except Exception as e:
        logger.error(f"Failed to read Parquet file {path}: {e}")
        raise

def calculate_line_counts(df: pd.DataFrame, column_name: str = "line_count") -> np.ndarray:
    """
    Extract line counts from a DataFrame.

    Args:
        df: The DataFrame containing the data.
        column_name: The name of the column containing line counts.

    Returns:
        Numpy array of line counts.

    Raises:
        ValueError: If the column is missing or contains non-numeric data.
    """
    if column_name not in df.columns:
        raise ValueError(f"Column '{column_name}' not found in DataFrame. Available: {list(df.columns)}")

    counts = df[column_name].dropna().values
    if not np.issubdtype(counts.dtype, np.number):
        raise ValueError(f"Column '{column_name}' contains non-numeric data.")

    logger.info(f"Extracted {len(counts)} line counts from '{column_name}'")
    return counts

def get_issue_types(df: pd.DataFrame, column_name: str = "issue_type") -> Optional[pd.Series]:
    """
    Extract issue types from a DataFrame if available.

    Args:
        df: The DataFrame.
        column_name: The column name for issue types.

    Returns:
        Series of issue types or None if column missing.
    """
    if column_name in df.columns:
        return df[column_name]
    return None

def perform_ks_test(filtered_counts: np.ndarray, raw_counts: np.ndarray) -> Tuple[float, float]:
    """
    Perform the Kolmogorov-Smirnov test.

    Args:
        filtered_counts: Line counts from the filtered dataset.
        raw_counts: Line counts from the raw dataset sample.

    Returns:
        Tuple of (KS statistic, p-value).
    """
    if len(filtered_counts) == 0 or len(raw_counts) == 0:
        raise ValueError("Cannot perform KS test with empty arrays.")

    ks_stat, p_value = stats.ks_2samp(filtered_counts, raw_counts)
    return ks_stat, p_value

def validate_representativeness(
    filtered_path: Path,
    raw_path: Path,
    column_name: str = "line_count",
    threshold: float = 0.1
) -> bool:
    """
    Main validation logic.

    Loads both datasets, extracts line counts, performs KS test, and logs results.

    Args:
        filtered_path: Path to the filtered Parquet file.
        raw_path: Path to the raw Parquet file (or sample thereof).
        column_name: Name of the column to compare.
        threshold: KS statistic threshold for warning (default 0.1).

    Returns:
        True if representative (KS <= threshold), False otherwise.
    """
    logger.info(f"Starting representativeness validation...")
    logger.info(f"Filtered dataset: {filtered_path}")
    logger.info(f"Raw dataset: {raw_path}")
    logger.info(f"Comparison column: {column_name}")
    logger.info(f"KS Threshold: {threshold}")

    # Load datasets
    try:
        df_filtered = load_parquet_dataset(filtered_path)
        df_raw = load_parquet_dataset(raw_path)
    except Exception as e:
        logger.error(f"Failed to load datasets: {e}")
        return False

    # Extract counts
    try:
        counts_filtered = calculate_line_counts(df_filtered, column_name)
        counts_raw = calculate_line_counts(df_raw, column_name)
    except Exception as e:
        logger.error(f"Failed to extract line counts: {e}")
        return False

    # Perform KS test
    try:
        ks_stat, p_value = perform_ks_test(counts_filtered, counts_raw)
    except Exception as e:
        logger.error(f"KS test failed: {e}")
        return False

    # Log results
    logger.info("-" * 40)
    logger.info(f"KS Statistic: {ks_stat:.6f}")
    logger.info(f"P-value: {p_value:.6f}")
    logger.info("-" * 40)

    # Check threshold
    if ks_stat > threshold:
        logger.warning(
            f"WARNING: KS statistic ({ks_stat:.4f}) > threshold ({threshold}). "
            "The filtered set may NOT be representative of the full population."
        )
        return False
    else:
        logger.info(
            f"SUCCESS: KS statistic ({ks_stat:.4f}) <= threshold ({threshold}). "
            "The filtered set appears representative."
        )
        return True

def main():
    """
    CLI entry point for T054.

    Usage:
        python code/analysis/representativeness_validator.py \
            --filtered data/filtered_swe_bench_v1.parquet \
            --raw data/raw_swe_bench_v1.parquet
    """
    parser = argparse.ArgumentParser(
        description="T054: Validate representativeness of filtered dataset via KS test."
    )
    parser.add_argument(
        "--filtered",
        type=str,
        required=True,
        help="Path to the filtered Parquet file (e.g., data/filtered_swe_bench_v1.parquet)"
    )
    parser.add_argument(
        "--raw",
        type=str,
        required=True,
        help="Path to the raw Parquet file (e.g., data/raw_swe_bench_v1.parquet)"
    )
    parser.add_argument(
        "--column",
        type=str,
        default="line_count",
        help="Column name to compare (default: line_count)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.1,
        help="KS statistic threshold for warning (default: 0.1)"
    )

    args = parser.parse_args()

    filtered_path = Path(args.filtered)
    raw_path = Path(args.raw)

    # Ensure paths are relative to project root if they are not absolute
    if not filtered_path.is_absolute():
        filtered_path = DATA_DIR / filtered_path
    if not raw_path.is_absolute():
        raw_path = DATA_DIR / raw_path

    success = validate_representativeness(
        filtered_path=filtered_path,
        raw_path=raw_path,
        column_name=args.column,
        threshold=args.threshold
    )

    # Exit with code 0 if valid, 1 if not (or on error)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()