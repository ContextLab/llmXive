import numpy as np
import pandas as pd
from typing import Tuple, List, Optional

from config import get_cli_threshold, get_outlier_threshold
from utils.logging import log_step, log_error


def compute_moving_average_zscore(
    df: pd.DataFrame,
    column: str = "pupil_diameter",
    window_size: int = 100
) -> pd.DataFrame:
    """
    Compute a moving average of the specified column and return its z-score.

    Args:
        df: Input DataFrame with time-series data.
        column: Name of the column to process (default: 'pupil_diameter').
        window_size: Size of the rolling window for the moving average.

    Returns:
        DataFrame with the original data and a new column '_zscore'.
    """
    log_step("cli_engine", "compute_moving_average_zscore", f"Computing z-scores with window={window_size}")

    if column not in df.columns:
        log_error("cli_engine", "compute_moving_average_zscore", f"Column '{column}' not found in DataFrame")
        raise ValueError(f"Column '{column}' not found in DataFrame")

    # Compute rolling mean and std
    rolling_mean = df[column].rolling(window=window_size, min_periods=1).mean()
    rolling_std = df[column].rolling(window=window_size, min_periods=1).std()

    # Handle division by zero if std is 0
    rolling_std = rolling_std.replace(0, np.nan).fillna(1.0)

    # Compute z-score
    df = df.copy()
    df['_zscore'] = (df[column] - rolling_mean) / rolling_std

    return df


def identify_high_load_windows(
    df: pd.DataFrame,
    zscore_column: str = "_zscore",
    threshold: Optional[float] = None
) -> pd.DataFrame:
    """
    Identify windows where the CLI (z-score) exceeds a threshold.

    Args:
        df: Input DataFrame with z-score column.
        zscore_column: Name of the z-score column (default: '_zscore').
        threshold: CLI threshold (default: from config via get_cli_threshold()).

    Returns:
        DataFrame with a new boolean column 'is_high_load'.
    """
    log_step("cli_engine", "identify_high_load_windows", f"Identifying high load windows with threshold={threshold}")

    if threshold is None:
        threshold = get_cli_threshold()

    if zscore_column not in df.columns:
        log_error("cli_engine", "identify_high_load_windows", f"Column '{zscore_column}' not found in DataFrame")
        raise ValueError(f"Column '{zscore_column}' not found in DataFrame")

    df = df.copy()
    df['is_high_load'] = df[zscore_column] > threshold

    return df


def compute_outlier_flags(
    df: pd.DataFrame,
    zscore_column: str = "_zscore",
    threshold: Optional[float] = None
) -> pd.DataFrame:
    """
    Flag windows as outliers if their z-score is > 3 SD from the mean (absolute value).

    Args:
        df: Input DataFrame with z-score column.
        zscore_column: Name of the z-score column (default: '_zscore').
        threshold: Outlier threshold in SD units (default: from config via get_outlier_threshold()).

    Returns:
        DataFrame with a new boolean column 'is_outlier'.
    """
    log_step("cli_engine", "compute_outlier_flags", f"Computing outlier flags with threshold={threshold}")

    if threshold is None:
        threshold = get_outlier_threshold()

    if zscore_column not in df.columns:
        log_error("cli_engine", "compute_outlier_flags", f"Column '{zscore_column}' not found in DataFrame")
        raise ValueError(f"Column '{zscore_column}' not found in DataFrame")

    df = df.copy()
    # Flag absolute z-score > threshold
    df['is_outlier'] = df[zscore_column].abs() > threshold

    return df


def process_window_data(
    df: pd.DataFrame,
    window_size: int = 100,
    cli_threshold: Optional[float] = None,
    outlier_threshold: Optional[float] = None
) -> pd.DataFrame:
    """
    Full pipeline: compute z-scores, identify high-load windows, and flag outliers.

    Args:
        df: Input DataFrame with time-series data.
        window_size: Rolling window size for z-score calculation.
        cli_threshold: Threshold for high-load identification.
        outlier_threshold: Threshold for outlier flagging.

    Returns:
        Processed DataFrame with '_zscore', 'is_high_load', and 'is_outlier' columns.
    """
    log_step("cli_engine", "process_window_data", "Starting full window processing pipeline")

    # Step 1: Compute z-scores
    df = compute_moving_average_zscore(df, window_size=window_size)

    # Step 2: Identify high-load windows
    df = identify_high_load_windows(df, threshold=cli_threshold)

    # Step 3: Flag outliers
    df = compute_outlier_flags(df, threshold=outlier_threshold)

    log_step("cli_engine", "process_window_data", "Pipeline completed successfully")
    return df