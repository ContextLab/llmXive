import numpy as np
import pandas as pd
from typing import Tuple, List, Optional

from config import get_cli_threshold, get_outlier_threshold
from utils.logging import log_step, log_error


def compute_moving_average_zscore(
    values: np.ndarray, window_size: int = 5
) -> np.ndarray:
    """
    Compute a moving average z-score for a time series of CLI values.

    Args:
        values: 1D array of CLI values.
        window_size: Size of the rolling window for mean/std calculation.

    Returns:
        Array of z-scores corresponding to each point (NaN where window is incomplete).
    """
    if len(values) < window_size:
        log_step("cli_engine", "Window size exceeds data length, returning NaNs.")
        return np.full_like(values, np.nan, dtype=float)

    series = pd.Series(values)
    rolling_mean = series.rolling(window=window_size, center=True).mean()
    rolling_std = series.rolling(window=window_size, center=True).std()

    # Avoid division by zero
    rolling_std = rolling_std.replace(0, np.nan)

    z_scores = (series - rolling_mean) / rolling_std
    return z_scores.values


def identify_high_load_windows(
    z_scores: np.ndarray,
    threshold_std: Optional[float] = None
) -> List[bool]:
    """
    Identify windows where the CLI z-score exceeds a threshold.

    Args:
        z_scores: Array of pre-computed z-scores.
        threshold_std: Number of standard deviations above mean to flag as high load.
                       Defaults to config value (0.5).

    Returns:
        List of booleans indicating high-load status for each window.
    """
    if threshold_std is None:
        threshold_std = get_cli_threshold()

    log_step("cli_engine", f"Identifying high load windows with threshold {threshold_std} SD.")
    return [z > threshold_std for z in z_scores]


def compute_outlier_flags(
    z_scores: np.ndarray,
    threshold_std: Optional[float] = None
) -> List[bool]:
    """
    Flag windows that are statistical outliers for exclusion.

    Outliers are defined as windows where the absolute z-score exceeds a specified
    number of standard deviations from the mean (typically 3.0).

    Args:
        z_scores: Array of pre-computed z-scores.
        threshold_std: Number of standard deviations to consider an outlier.
                       Defaults to config value (3.0).

    Returns:
        List of booleans where True indicates the window should be excluded.
    """
    if threshold_std is None:
        threshold_std = get_outlier_threshold()

    log_step("cli_engine", f"Computing outlier flags with threshold {threshold_std} SD.")
    try:
        flags = [abs(z) > threshold_std for z in z_scores]
        return flags
    except Exception as e:
        log_error("cli_engine", "Failed to compute outlier flags", e)
        return [False] * len(z_scores)


def process_window_data(
    df: pd.DataFrame,
    cli_column: str = 'cli_value',
    window_size: int = 5,
    high_load_threshold: float = 0.5,
    outlier_threshold: float = 3.0
) -> pd.DataFrame:
    """
    Orchestrate the full CLI processing pipeline for a DataFrame of window data.

    Steps:
    1. Compute moving average z-scores.
    2. Identify high-load windows.
    3. Flag outliers for exclusion.
    4. Append results to the DataFrame.

    Args:
        df: Input DataFrame containing raw CLI values.
        cli_column: Name of the column containing raw CLI values.
        window_size: Rolling window size for z-score calculation.
        high_load_threshold: SD threshold for high-load detection.
        outlier_threshold: SD threshold for outlier detection.

    Returns:
        DataFrame with added columns: 'cli_zscore', 'is_high_load', 'is_outlier'.
    """
    log_step("cli_engine", "Starting window data processing.")

    if cli_column not in df.columns:
        raise ValueError(f"Column '{cli_column}' not found in DataFrame.")

    values = df[cli_column].values.astype(float)

    # Compute z-scores
    z_scores = compute_moving_average_zscore(values, window_size)

    # Identify high load
    is_high_load = identify_high_load_windows(z_scores, high_load_threshold)

    # Flag outliers
    is_outlier = compute_outlier_flags(z_scores, outlier_threshold)

    result = df.copy()
    result['cli_zscore'] = z_scores
    result['is_high_load'] = is_high_load
    result['is_outlier'] = is_outlier

    log_step("cli_engine", "Window data processing complete.")
    return result
