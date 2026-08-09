"""
Resampling utilities for time series data.

Implements logic to detect native frequency and resample datasets
to a consistent frequency (hourly or daily) before stationarity testing.
"""
import logging
from typing import Tuple, Optional, Literal

import pandas as pd
import numpy as np

from src.data.preprocessing import PreprocessingError
from src.utils.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)


def detect_native_frequency(df: pd.DataFrame, datetime_col: str = 'datetime') -> str:
    """
    Detect the native frequency of a time series based on its datetime index.
    
    Args:
        df: DataFrame with a datetime index or a datetime column.
        datetime_col: Name of the datetime column if not already the index.
    
    Returns:
        A string representing the detected frequency (e.g., 'H', 'D', 'T').
    
    Raises:
        PreprocessingError: If frequency cannot be detected or data is insufficient.
    """
    if datetime_col in df.columns:
        df = df.set_index(datetime_col)
    
    if not isinstance(df.index, pd.DatetimeIndex):
        raise PreprocessingError("DataFrame must have a DatetimeIndex or a datetime column.")
    
    if len(df) < 3:
        raise PreprocessingError("Insufficient data points to detect frequency.")
    
    # Calculate differences between consecutive timestamps
    diffs = df.index.to_series().diff().dropna()
    
    if diffs.empty:
        raise PreprocessingError("Could not compute time differences.")
    
    # Get the median difference to handle occasional missing points
    median_diff = diffs.median()
    median_diff_seconds = median_diff.total_seconds()
    
    # Map seconds to frequency strings
    # T = minute, H = hour, D = day, W = week
    if median_diff_seconds < 60:
        # Sub-minute (e.g., seconds)
        return 'S'
    elif median_diff_seconds < 3600:
        if median_diff_seconds < 300: # 5 minutes
            return '5T'
        elif median_diff_seconds < 600: # 10 minutes
            return '10T'
        elif median_diff_seconds < 900: # 15 minutes
            return '15T'
        elif median_diff_seconds < 1800: # 30 minutes
            return '30T'
        else:
            return 'T' # Minute
    elif median_diff_seconds < 86400:
        if median_diff_seconds < 14400: # 4 hours
            return '4H'
        elif median_diff_seconds < 21600: # 6 hours
            return '6H'
        elif median_diff_seconds < 43200: # 12 hours
            return '12H'
        else:
            return 'H' # Hour
    elif median_diff_seconds < 604800: # 7 days
        return 'D'
    else:
        return 'W'


def determine_target_frequency(native_freq: str) -> Literal['H', 'D']:
    """
    Determine the target frequency based on the native frequency.
    
    Strategy:
    - If native is finer than or equal to daily (e.g., seconds, minutes, hours), target is Daily ('D').
    - If native is coarser than daily (e.g., weekly), target is Weekly (but spec asks for H/D, so we might keep Weekly or downsample to D if possible).
    - For this implementation, we target 'D' for any sub-daily data, and 'H' only if the data is extremely high frequency and we need to reduce it significantly, 
      but the spec says "consistent frequency (e.g., hourly, daily)". 
      Let's standardize: 
      - Native <= 1 hour -> Target Daily ('D')
      - Native > 1 hour but <= 1 day -> Target Daily ('D')
      - Native > 1 day -> Target Weekly ('W') (or keep as is if weekly is the native)
      
      However, the task specifically mentions "hourly, daily". 
      Let's interpret: 
      - If native is sub-hourly (e.g., 15min), resample to Hourly ('H') to preserve detail? Or Daily?
      - Spec: "consistent frequency (e.g., hourly, daily) based on the dataset's native resolution".
      
      Decision:
      - If native_freq is sub-hourly (S, T, 5T, 10T, 15T, 30T), resample to Hourly ('H').
      - If native_freq is Hourly ('H') or sub-daily but hourly-aligned (4H, 6H, 12H), resample to Daily ('D').
      - If native_freq is Daily ('D'), keep as 'D'.
      - If native_freq is coarser (W, M), keep as is (or raise warning).
    """
    if native_freq in ['S', 'T', '5T', '10T', '15T', '30T']:
        return 'H'
    elif native_freq in ['H', '4H', '6H', '12H', 'D']:
        return 'D'
    else:
        # For coarser data (weekly, monthly), we cannot resample to H or D meaningfully.
        # We will return the native frequency to avoid data loss, but log a warning.
        log_warning(f"Native frequency {native_freq} is coarser than daily. Keeping native frequency.")
        return native_freq


def resample_series(
    df: pd.DataFrame,
    target_freq: str,
    value_col: str,
    datetime_col: Optional[str] = None,
    aggregation_method: str = 'mean'
) -> pd.DataFrame:
    """
    Resample a time series to a target frequency.
    
    Args:
        df: Input DataFrame.
        target_freq: Target frequency string (e.g., 'H', 'D').
        value_col: Name of the column containing the time series values.
        datetime_col: Name of the datetime column. If None, uses the index.
        aggregation_method: Method to aggregate values during resampling 
            (e.g., 'mean', 'sum', 'last').
    
    Returns:
        Resampled DataFrame with a DatetimeIndex at the target frequency.
    
    Raises:
        PreprocessingError: If resampling fails.
    """
    if datetime_col and datetime_col in df.columns:
        df = df.set_index(datetime_col)
    
    if not isinstance(df.index, pd.DatetimeIndex):
        raise PreprocessingError("DataFrame must have a DatetimeIndex.")
    
    if value_col not in df.columns:
        raise PreprocessingError(f"Value column '{value_col}' not found in DataFrame.")
    
    try:
        resampled = df[value_col].resample(target_freq).agg(aggregation_method)
        # Drop NaNs that might result from resampling (e.g., periods with no data)
        resampled = resampled.dropna()
        
        if len(resampled) < 2:
            raise PreprocessingError(
                f"Resampled series has insufficient data points ({len(resampled)}) "
                f"after resampling to {target_freq}."
            )
        
        # Re-attach other columns if necessary (usually we just need the value)
        # For simplicity, we return a single-column DataFrame
        result = resampled.to_frame(name=value_col)
        
        return result
    
    except Exception as e:
        log_error(f"Resampling failed: {str(e)}")
        raise PreprocessingError(f"Resampling failed: {str(e)}") from e


def resample_dataset(
    df: pd.DataFrame,
    value_col: str,
    datetime_col: Optional[str] = None,
    aggregation_method: str = 'mean'
) -> Tuple[pd.DataFrame, str, str]:
    """
    Main entry point for resampling a dataset.
    
    Detects native frequency, determines target frequency, and resamples.
    
    Args:
        df: Input DataFrame.
        value_col: Name of the value column.
        datetime_col: Name of the datetime column.
        aggregation_method: Aggregation method for resampling.
    
    Returns:
        Tuple of (resampled_df, native_freq, target_freq).
    """
    log_info(f"Starting resampling for dataset with value column '{value_col}'.")
    
    # Detect native frequency
    native_freq = detect_native_frequency(df, datetime_col)
    log_info(f"Detected native frequency: {native_freq}")
    
    # Determine target frequency
    target_freq = determine_target_frequency(native_freq)
    log_info(f"Target frequency determined: {target_freq}")
    
    # If native is already the target, no resampling needed (unless we want to enforce strict alignment)
    if native_freq == target_freq:
        log_info("Native frequency matches target frequency. Skipping resampling.")
        return df, native_freq, target_freq
    
    # Perform resampling
    resampled_df = resample_series(
        df, 
        target_freq, 
        value_col, 
        datetime_col, 
        aggregation_method
    )
    
    log_info(f"Resampling complete. Original length: {len(df)}, Resampled length: {len(resampled_df)}")
    
    return resampled_df, native_freq, target_freq
