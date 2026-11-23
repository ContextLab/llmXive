"""
Mathematical utility functions for the llmXive pipeline.

Provides statistical helpers, interpolation, and correlation calculations.
"""
import numpy as np
import pandas as pd
from typing import Optional, Union, Tuple
from scipy import interpolate


def interpolate_missing_timesteps(
    times: np.ndarray,
    values: np.ndarray,
    method: str = 'linear'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Interpolate missing timesteps in a time series using linear interpolation.

    Args:
        times: Array of timesteps (may have gaps).
        values: Array of values corresponding to times.
        method: Interpolation method ('linear', 'nearest', etc.).

    Returns:
        Tuple of (filled_times, filled_values) with no gaps.
    """
    times = np.asarray(times)
    values = np.asarray(values)

    if len(times) != len(values):
        raise ValueError("times and values must have the same length")

    if len(times) < 2:
        return times, values

    # Identify unique existing timesteps to ensure we don't interpolate over duplicates incorrectly
    unique_indices = np.unique(times, return_index=True)[1]
    unique_times = times[unique_indices]
    unique_values = values[unique_indices]

    # Create a continuous range of timesteps from min to max
    full_times = np.arange(int(np.floor(unique_times.min())), int(np.ceil(unique_times.max())) + 1)

    # Perform interpolation
    try:
        f = interpolate.interp1d(
            unique_times,
            unique_values,
            kind=method,
            bounds_error=False,
            fill_value='extrapolate'
        )
        filled_values = f(full_times)
    except ValueError:
        # Fallback if interpolation fails (e.g., constant values causing issues)
        filled_values = np.interp(full_times, unique_times, unique_values)

    return full_times, filled_values


def safe_z_score(
    values: np.ndarray,
    window_size: int = 20,
    min_samples: int = 5,
    epsilon: float = 1e-9
) -> np.ndarray:
    """
    Calculate z-score with safety checks for zero variance.

    Implements a rolling z-score calculation where for each point i,
    we look at the window [max(0, i - window_size + 1), i].

    Args:
        values: Array of values to compute z-scores for.
        window_size: Size of the sliding window.
        min_samples: Minimum number of samples required to compute z-score.
        epsilon: Small positive value to prevent division by zero.

    Returns:
        Array of z-scores with neutral baseline (0) for zero variance cases.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)

    if n < min_samples:
        return np.zeros(n)

    z_scores = np.zeros(n)

    for i in range(n):
        # Define window bounds: look back up to window_size steps
        start_idx = max(0, i - window_size + 1)
        window = values[start_idx : i + 1]

        current_len = len(window)

        if current_len < min_samples:
            z_scores[i] = 0.0
            continue

        mean = np.mean(window)
        std = np.std(window)

        # Prevent division by zero using epsilon floor
        if std < epsilon:
            z_scores[i] = 0.0
        else:
            z_scores[i] = (values[i] - mean) / std

    return z_scores


def handle_nan(
    values: np.ndarray,
    strategy: str = 'forward_fill'
) -> np.ndarray:
    """
    Gracefully handle NaN values in time-series data, specifically for
    sliding window calculations.

    Args:
        values: Array of values that may contain NaNs.
        strategy: Handling strategy ('forward_fill', 'backward_fill', 'mean', 'zero').

    Returns:
        Array with NaNs replaced according to the strategy.
    """
    values = np.asarray(values, dtype=float)
    result = values.copy()

    nan_mask = np.isnan(result)

    if not np.any(nan_mask):
        return result

    if strategy == 'forward_fill':
        # Forward fill: propagate last valid observation
        # Using pandas for robust handling
        series = pd.Series(result)
        result = series.ffill().bfill().values
    elif strategy == 'backward_fill':
        # Backward fill: propagate next valid observation
        series = pd.Series(result)
        result = series.bfill().ffill().values
    elif strategy == 'mean':
        # Replace with mean of non-NaN values
        mean_val = np.nanmean(result)
        if np.isnan(mean_val):
            # All values were NaN
            result = np.zeros_like(result)
        else:
            result[nan_mask] = mean_val
    elif strategy == 'zero':
        # Replace with zero
        result[nan_mask] = 0.0
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Final check: if any NaNs remain (e.g., all values were NaN), set to 0
    result = np.nan_to_num(result, nan=0.0)

    return result


def rolling_std_dev(
    values: np.ndarray,
    window_size: int = 20,
    min_samples: int = 5,
    mask: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Calculate rolling standard deviation with optional masking.

    Args:
        values: Array of values.
        window_size: Size of the sliding window.
        min_samples: Minimum samples required for calculation.
        mask: Boolean array to exclude certain indices from baseline calculation.

    Returns:
        Array of rolling standard deviations.
    """
    values = np.asarray(values, dtype=float)
    n = len(values)

    if mask is None:
        mask = np.zeros(n, dtype=bool)

    std_devs = np.zeros(n)

    for i in range(n):
        start = max(0, i - window_size + 1)
        window_indices = np.arange(start, i + 1)

        # Apply mask to exclude contaminated indices
        valid_indices = window_indices[~mask[window_indices]]

        if len(valid_indices) < min_samples:
            std_devs[i] = 0.0
            continue

        window_values = values[valid_indices]
        std_devs[i] = np.std(window_values)

    return std_devs


def calculate_pearson_correlation(
    x: Union[np.ndarray, list],
    y: Union[np.ndarray, list]
) -> float:
    """
    Calculate Pearson correlation coefficient between two arrays.

    Args:
        x: First array of values.
        y: Second array of values.

    Returns:
        Pearson correlation coefficient (float between -1 and 1).
    """
    x = np.asarray(x)
    y = np.asarray(y)

    if len(x) != len(y):
        raise ValueError("Arrays must have the same length")

    if len(x) < 2:
        return 0.0

    # Remove NaN values
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    x_valid = x[valid_mask]
    y_valid = y[valid_mask]

    if len(x_valid) < 2:
        return 0.0

    # Calculate Pearson correlation
    correlation = np.corrcoef(x_valid, y_valid)[0, 1]

    # Handle potential NaN from constant arrays
    if np.isnan(correlation):
        return 0.0

    return float(correlation)