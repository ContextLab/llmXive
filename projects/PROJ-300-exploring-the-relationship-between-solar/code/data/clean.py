"""
Data cleaning and resampling module.
Handles NaN removal, resampling to a common cadence, and gap handling.
"""
import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta
import logging
import json

logger = logging.getLogger(__name__)

def clean_and_resample(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Remove NaN values and resample both DataFrames to a common regular cadence.
    
    Args:
        df_sw: Solar wind DataFrame with columns [timestamp, Vsw, Bz].
        df_ey: THEMIS DataFrame with columns [timestamp, Ey].
        
    Returns:
        Tuple of (df_sw_clean, df_ey_clean) resampled to 5-minute cadence.
    """
    # Ensure timestamp is datetime and set as index
    df_sw = df_sw.copy()
    df_ey = df_ey.copy()
    
    df_sw['timestamp'] = pd.to_datetime(df_sw['timestamp'])
    df_ey['timestamp'] = pd.to_datetime(df_ey['timestamp'])
    
    df_sw.set_index('timestamp', inplace=True)
    df_ey.set_index('timestamp', inplace=True)
    
    # Drop rows with NaN in the value columns
    df_sw = df_sw.dropna(subset=['Vsw', 'Bz'])
    df_ey = df_ey.dropna(subset=['Ey'])
    
    # Resample to 5-minute intervals using mean
    df_sw_resampled = df_sw.resample('5min').mean()
    df_ey_resampled = df_ey.resample('5min').mean()
    
    # Re-align indices (inner join to keep only common timestamps)
    common_index = df_sw_resampled.index.intersection(df_ey_resampled.index)
    df_sw_clean = df_sw_resampled.loc[common_index]
    df_ey_clean = df_ey_resampled.loc[common_index]
    
    # Drop any remaining NaNs resulting from resampling
    df_sw_clean = df_sw_clean.dropna(subset=['Vsw', 'Bz'])
    df_ey_clean = df_ey_clean.dropna(subset=['Ey'])
    
    logger.info(f"Cleaned data: {len(df_sw_clean)} points after resampling.")
    
    return df_sw_clean, df_ey_clean

def handle_gaps(df: pd.DataFrame, max_gap_minutes: int = 30) -> pd.DataFrame:
    """
    Identify gaps > max_gap_minutes and truncate or flag the series.
    
    Args:
        df: DataFrame with a DatetimeIndex.
        max_gap_minutes: Maximum allowed gap in minutes.
        
    Returns:
        DataFrame truncated at the first large gap, or the original if no gaps.
    """
    if df.empty:
        return df
    
    # Calculate time differences
    time_diffs = df.index.to_series().diff()
    
    # Identify gaps
    gap_mask = time_diffs > timedelta(minutes=max_gap_minutes)
    
    if gap_mask.any():
        # Find the first large gap
        first_gap_idx = gap_mask[gap_mask].index[0]
        # Truncate the dataframe before the gap
        # We keep data up to the point before the gap
        # The gap is at first_gap_idx, so we keep up to the previous index
        prev_idx = df.index.get_loc(first_gap_idx) - 1
        if prev_idx >= 0:
            truncated_df = df.iloc[:prev_idx+1]
            logger.warning(f"Truncated data at gap starting at {first_gap_idx}.")
            return truncated_df
        else:
            # Gap is at the very beginning, return empty or original?
            # Return original but log warning
            logger.warning(f"Gap at the beginning of the series. No data kept.")
            return df.iloc[:0]
    
    return df
