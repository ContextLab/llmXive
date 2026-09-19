"""
Preprocessing pipeline for CDC FluView ILI data.

This module handles:
1. Loading raw ILI data
2. Removing missing weeks (NaNs)
3. Log-transforming the ILI percentages
4. Standardizing the data (zero mean, unit variance)
5. Calculating the total number of consecutive window pairs (N)
6. Saving the processed data and configuration metrics.

Dependencies:
- code/config.yaml
- data/raw/fluview_ili.csv (produced by T012a)
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from typing import Tuple, Optional, Dict, Any

# Import logging setup from sibling module
try:
    from logging_setup import setup_logging
except ImportError:
    # Fallback if run directly without package context
    def setup_logging(name: str) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

# Import config loading
try:
    from main import load_config
except ImportError:
    # Fallback for direct execution
    import yaml
    def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

logger = setup_logging(__name__)


def load_ili_data(filepath: str) -> pd.DataFrame:
    """
    Load the raw ILI data from CSV.

    Args:
        filepath: Path to the raw CSV file (e.g., data/raw/fluview_ili.csv)

    Returns:
        DataFrame with columns: 'week', 'ili_percent', 'outbreak_flag' (if available)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found: {filepath}")

    logger.info(f"Loading raw data from {filepath}")
    df = pd.read_csv(filepath)

    # Standardize column names based on verified source recipe
    # Expected columns from verified source: 'epiweek', 'ili', 'outbreak'
    # Or standard FluView: 'YEAR', 'WEEK', '% WEIGHTED ILI'
    # We map to a canonical schema for processing

    canonical_cols = {}

    # Map EpiWeek/ILI if present (from verified source)
    if 'epiweek' in df.columns:
        canonical_cols['week'] = 'epiweek'
    elif 'YEAR' in df.columns and 'WEEK' in df.columns:
        # Construct week ID: Year-WW
        df['week'] = df['YEAR'].astype(str) + '-W' + df['WEEK'].astype(str).str.zfill(2)
        canonical_cols['week'] = 'week'
    else:
        raise ValueError("Could not identify week column in raw data")

    if 'ili' in df.columns:
        canonical_cols['ili_percent'] = 'ili'
    elif '% WEIGHTED ILI' in df.columns:
        canonical_cols['ili_percent'] = '% WEIGHTED ILI'
    else:
        raise ValueError("Could not identify ILI percentage column in raw data")

    # Select and rename canonical columns
    result = df[[canonical_cols['week'], canonical_cols['ili_percent']]].copy()
    result = result.rename(columns=canonical_cols)

    # Ensure numeric types
    result['ili_percent'] = pd.to_numeric(result['ili_percent'], errors='coerce')

    # Sort by week to ensure time-series order
    result = result.sort_values('week').reset_index(drop=True)

    logger.info(f"Loaded {len(result)} records. Columns: {list(result.columns)}")
    return result


def remove_missing_weeks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows where ILI data is missing (NaN).
    Logs the count of removed rows.

    Args:
        df: DataFrame with 'ili_percent' column

    Returns:
        Cleaned DataFrame
    """
    initial_count = len(df)
    df_clean = df.dropna(subset=['ili_percent'])
    removed_count = initial_count - len(df_clean)

    if removed_count > 0:
        logger.warning(f"Removed {removed_count} rows with missing ILI data.")
    else:
        logger.info("No missing weeks found.")

    return df_clean.reset_index(drop=True)


def log_transform(df: pd.DataFrame, epsilon: float = 1e-9) -> pd.DataFrame:
    """
    Apply log transformation to ILI percentages.
    Adds a small epsilon to avoid log(0).

    Args:
        df: DataFrame with 'ili_percent'
        epsilon: Small constant to prevent log(0)

    Returns:
        DataFrame with 'log_ili' column
    """
    df = df.copy()
    # Ensure non-negative before log (ILI should be >= 0)
    df['ili_percent'] = df['ili_percent'].clip(lower=0)
    df['log_ili'] = np.log1p(df['ili_percent'] + epsilon)
    logger.info("Applied log1p transformation to ILI data.")
    return df


def standardize(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize the log-transformed ILI data (zero mean, unit variance).
    Raises ValueError if variance is zero (constant series).

    Args:
        df: DataFrame with 'log_ili'

    Returns:
        DataFrame with 'z_ili' column
    """
    df = df.copy()
    mean_val = df['log_ili'].mean()
    std_val = df['log_ili'].std()

    if std_val == 0:
        raise ValueError(
            f"Zero variance detected in log_ili series (std={std_val}). "
            "Cannot standardize constant data. Check for data issues or constant segments."
        )

    df['z_ili'] = (df['log_ili'] - mean_val) / std_val
    logger.info(f"Standardized data: mean={mean_val:.4f}, std={std_val:.4f}")
    return df


def calculate_window_pairs(N_total: int, window_size: int, stride: int = 1) -> int:
    """
    Calculate the total number of consecutive window pairs (N) for the MMD test.

    A 'window pair' consists of two adjacent windows of length `window_size`.
    We slide these pairs across the time series with `stride`.

    Formula:
    Total positions for a single window of size W in series of length L: L - W + 1
    A pair of windows requires 2*W data points.
    Number of pairs = Total positions for a pair - 1 (since we compare adjacent)
    Actually, simpler logic:
    Let L be series length.
    Window 1: [0, W)
    Window 2: [W, 2W)
    ...
    We slide the starting position of the pair by `stride`.
    The last valid pair ends at index L.
    Start index of a pair can range from 0 to L - 2*W.
    Number of steps = floor((L - 2*W) / stride) + 1

    Args:
        N_total: Length of the preprocessed time series (L)
        window_size: Size of one window (W)
        stride: Step size between consecutive pairs

    Returns:
        Total number of consecutive window pairs (N)
    """
    min_length = 2 * window_size
    if N_total < min_length:
        logger.warning(f"Series length {N_total} is too short for window_size {window_size}. "
                       f"Minimum required length is {min_length}. Returning 0 pairs.")
        return 0

    # Max start index for the first window of a pair
    max_start_idx = N_total - 2 * window_size
    # Number of pairs = floor(max_start_idx / stride) + 1
    num_pairs = (max_start_idx // stride) + 1
    return num_pairs


def save_processed_data(df: pd.DataFrame, output_path: str):
    """
    Save the processed DataFrame to CSV.

    Args:
        df: Processed DataFrame
        output_path: Path to save the CSV (e.g., data/processed/ili_processed.csv)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")


def save_mmd_config(N: int, config: Dict[str, Any], output_path: str):
    """
    Save the MMD configuration, including the calculated total window pairs (N).

    Args:
        N: Total number of consecutive window pairs
        config: Original configuration dictionary
        output_path: Path to save the JSON config (e.g., data/processed/mmd_config.json)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Prepare the config object
    mmd_config = {
        "total_window_pairs": N,
        "window_size": config.get('window_size', 12),
        "stride": config.get('stride', 1),
        "permutations": config.get('permutations', 1000),
        "alpha": config.get('alpha', 0.01),
        "min_permutations": config.get('min_permutations', 100),
        "time_budget_minutes": config.get('time_budget_minutes', 30)
    }

    with open(output_path, 'w') as f:
        json.dump(mmd_config, f, indent=2)

    logger.info(f"Saved MMD configuration (N={N}) to {output_path}")


def preprocess_pipeline():
    """
    Execute the full preprocessing pipeline:
    1. Load raw data
    2. Remove missing weeks
    3. Log transform
    4. Standardize
    5. Calculate N (total window pairs)
    6. Save processed data and mmd_config.json

    This function enforces the strict ordering: T013 -> T013a -> T014.
    T013a is the calculation of N and writing to mmd_config.json.
    """
    config = load_config()
    window_size = config.get('window_size', 12)
    stride = config.get('stride', 1)

    # Paths
    raw_path = "data/raw/fluview_ili.csv"
    processed_path = "data/processed/ili_processed.csv"
    config_output_path = "data/processed/mmd_config.json"

    # T013: Preprocessing steps
    logger.info("Starting preprocessing pipeline...")
    df = load_ili_data(raw_path)
    df = remove_missing_weeks(df)
    df = log_transform(df)
    df = standardize(df)

    # T013a: Calculate N and save config
    series_length = len(df)
    N = calculate_window_pairs(series_length, window_size, stride)
    logger.info(f"Calculated total window pairs (N): {N} from series length {series_length}")

    if N == 0:
        logger.error("Calculated N=0. The dataset is too short for the configured window size. "
                     "Cannot proceed with MMD detection.")
        # Save the config anyway to reflect the failure state, or raise?
        # Per task, we write N to config.
        save_mmd_config(N, config, config_output_path)
        raise ValueError("Insufficient data for MMD detection (N=0).")

    save_processed_data(df, processed_path)
    save_mmd_config(N, config, config_output_path)

    logger.info("Preprocessing pipeline completed successfully.")
    return df, N


def main():
    """Entry point for the preprocessing script."""
    try:
        preprocess_pipeline()
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()