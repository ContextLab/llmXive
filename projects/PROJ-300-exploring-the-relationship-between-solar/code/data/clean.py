"""
Data cleaning and resampling module.
Handles NaN removal, resampling to regular cadence, and gap detection.

File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/data/clean.py
"""

import pandas as pd
import numpy as np
from typing import Tuple
from datetime import timedelta
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Project root for logging
project_root = Path(__file__).resolve().parent.parent
QUALITY_LOG_PATH = project_root / "data" / "processed" / "quality_log.json"

def clean_and_resample(df_sw: pd.DataFrame, df_ey: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Remove NaN values and resample both DataFrames to a common regular cadence.

    Args:
        df_sw: Solar wind data with columns [timestamp, Vsw, Bz] (or index as timestamp)
        df_ey: THEMIS data with columns [timestamp, Ey] (or index as timestamp)

    Returns:
        Tuple of (cleaned_df_sw, cleaned_df_ey) resampled to 5-minute intervals.
    """
    # Ensure timestamp is index
    if 'timestamp' in df_sw.columns:
        df_sw = df_sw.set_index('timestamp')
    if 'timestamp' in df_ey.columns:
        df_ey = df_ey.set_index('timestamp')

    # Ensure index is datetime
    if not isinstance(df_sw.index, pd.DatetimeIndex):
        df_sw.index = pd.to_datetime(df_sw.index)
    if not isinstance(df_ey.index, pd.DatetimeIndex):
        df_ey.index = pd.to_datetime(df_ey.index)

    # Drop rows with NaN in value columns
    # Assuming value columns are 'Vsw' for sw and 'Ey' for ey
    df_sw_clean = df_sw.dropna(subset=['Vsw'])
    df_ey_clean = df_ey.dropna(subset=['Ey'])

    # Resample to 5-minute mean
    # Use '5T' or '5min' for 5 minutes
    df_sw_resampled = df_sw_clean.resample('5min').mean()
    df_ey_resampled = df_ey_clean.resample('5min').mean()

    # Align indices to the intersection of both
    common_index = df_sw_resampled.index.intersection(df_ey_resampled.index)
    
    df_sw_final = df_sw_resampled.loc[common_index]
    df_ey_final = df_ey_resampled.loc[common_index]

    # Drop any remaining NaNs that might have occurred during resampling
    df_sw_final = df_sw_final.dropna(subset=['Vsw'])
    df_ey_final = df_ey_final.dropna(subset=['Ey'])

    logger.info(f"Resampled data: {len(df_sw_final)} points (5-min cadence)")

    return df_sw_final, df_ey_final

def handle_gaps(df: pd.DataFrame, max_gap_minutes: int = 30) -> pd.DataFrame:
    """
    Identify gaps > max_gap_minutes and truncate or flag the series.
    Logs warnings to quality_log.json.

    Args:
        df: DataFrame with DatetimeIndex
        max_gap_minutes: Maximum allowed gap in minutes

    Returns:
        DataFrame, potentially truncated at the first large gap.
    """
    if df.empty:
        return df

    # Calculate time differences
    time_diffs = df.index.to_series().diff()
    
    # Identify gaps larger than threshold
    gap_threshold = timedelta(minutes=max_gap_minutes)
    large_gaps = time_diffs > gap_threshold

    if large_gaps.any():
        # Find the index of the first large gap
        first_gap_idx = large_gaps[large_gaps].index[0]
        # The row *after* the gap is the start of the new segment
        # We want to keep data up to the row *before* the gap
        cut_point_idx = first_gap_idx - 1 # This logic might be off for DatetimeIndex, let's use position

        # Get position of the first gap
        gap_positions = large_gaps[large_gaps].index
        if len(gap_positions) > 0:
            first_gap_time = gap_positions[0]
            # Find the index in the dataframe corresponding to the row before the gap
            # The gap is between first_gap_time - time_diff and first_gap_time
            # We keep up to first_gap_time - time_diff
            
            # Simpler approach: split by gap and keep the first segment
            mask = time_diffs <= gap_threshold
            # The first row has NaT, treat as False (or True? First row is start)
            # Actually, diff()[0] is NaT. We want to keep rows where the gap from previous is small.
            # So we keep row 0, and any row where diff <= threshold.
            # But if row i has a large gap from i-1, we should stop at i-1.
            
            # Let's find the index where the gap starts
            gap_start_indices = large_gaps[large_gaps].index
            if len(gap_start_indices) > 0:
                cut_time = gap_start_indices[0]
                # Keep everything up to the row before the gap
                # Since index is time, we can slice
                df_truncated = df.loc[:cut_time - pd.Timedelta(seconds=1)]
                
                warning_msg = f"Data truncated at {cut_time} due to gap > {max_gap_minutes} minutes."
                logger.warning(warning_msg)
                
                # Log to quality log
                try:
                    log_entry = {
                        "timestamp": pd.Timestamp.now().isoformat(),
                        "type": "gap_handling",
                        "message": warning_msg,
                        "gap_size_minutes": float(time_diffs.loc[cut_time].total_seconds() / 60)
                    }
                    if QUALITY_LOG_PATH.exists():
                        with open(QUALITY_LOG_PATH, 'r') as f:
                            try:
                                existing = json.load(f)
                                if isinstance(existing, list):
                                    existing.append(log_entry)
                                else:
                                    existing = [existing, log_entry]
                            except json.JSONDecodeError:
                                existing = [log_entry]
                        with open(QUALITY_LOG_PATH, 'w') as f:
                            json.dump(existing, f, indent=2)
                    else:
                        with open(QUALITY_LOG_PATH, 'w') as f:
                            json.dump([log_entry], f, indent=2)
                except Exception as e:
                    logger.error(f"Failed to write gap warning to log: {e}")
                
                return df_truncated

    return df
