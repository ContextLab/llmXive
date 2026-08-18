import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from utils.logging import get_logger, AlignmentError, ValidationError, check_memory_usage
from utils.io import load_parquet, save_parquet
from config import get_config

logger = get_logger(__name__)

# Constants for validation
MAX_TEMPORAL_OFFSET_MINUTES = 30
MEMORY_WARNING_THRESHOLD_GB = 6.0

def load_source_data(sources: dict) -> pd.DataFrame:
    """
    Load source data from provided paths or synthetic generators.
    Merges ACE and NOAA data into a single DataFrame.
    """
    config = get_config()
    dfs = []

    # Load ACE data (Solar Wind Composition)
    if 'ace' in sources:
        ace_path = sources['ace']
        if os.path.exists(ace_path):
            logger.info(f"Loading ACE data from {ace_path}")
            df_ace = load_parquet(ace_path)
            if 'timestamp' in df_ace.columns:
                df_ace['timestamp'] = pd.to_datetime(df_ace['timestamp'])
                dfs.append(df_ace)
            else:
                raise AlignmentError(f"ACE data missing 'timestamp' column: {ace_path}")
        else:
            logger.warning(f"ACE data file not found: {ace_path}. Skipping.")

    # Load NOAA data (Geomagnetic Indices)
    if 'noaa' in sources:
        noaa_path = sources['noaa']
        if os.path.exists(noaa_path):
            logger.info(f"Loading NOAA data from {noaa_path}")
            df_noaa = load_parquet(noaa_path)
            if 'timestamp' in df_noaa.columns:
                df_noaa['timestamp'] = pd.to_datetime(df_noaa['timestamp'])
                dfs.append(df_noaa)
            else:
                raise AlignmentError(f"NOAA data missing 'timestamp' column: {noaa_path}")
        else:
            logger.warning(f"NOAA data file not found: {noaa_path}. Skipping.")

    if not dfs:
        raise AlignmentError("No valid source data found to merge.")

    # Merge on timestamp
    merged_df = dfs[0]
    for df in dfs[1:]:
        merged_df = pd.merge(merged_df, df, on='timestamp', how='outer')

    return merged_df

def apply_epsilon_floor(df: pd.DataFrame, column: str, floor: float = 1e-6) -> pd.DataFrame:
    """
    Apply epsilon floor to prevent log(0) or division by zero in coupling functions.
    """
    if column in df.columns:
        df[column] = df[column].clip(lower=floor)
    return df

def handle_instrument_transitions(df: pd.DataFrame, instrument_col: str = 'instrument_version'):
    """
    Handle instrument version transitions by applying calibration offsets if available.
    For now, logs warnings if multiple versions exist without offsets.
    """
    if instrument_col in df.columns:
        versions = df[instrument_col].unique()
        if len(versions) > 1:
            logger.warning(f"Multiple instrument versions detected: {versions}. "
                           "No calibration offsets applied in this phase. Treating as separate cohorts.")
    return df

def detect_and_handle_gaps(df: pd.DataFrame, time_col: str = 'timestamp', max_gap_hours: int = 6) -> pd.DataFrame:
    """
    Detect gaps in time series. If gaps > max_gap_hours, interpolate or flag.
    Returns a dataframe with a 'gap_flag' column (1 if interpolated/missing, 0 if valid).
    """
    df = df.sort_values(time_col).reset_index(drop=True)
    df['time_diff'] = df[time_col].diff()
    
    # Identify gaps larger than max_gap_hours
    gap_threshold = pd.Timedelta(hours=max_gap_hours)
    df['is_large_gap'] = df['time_diff'] > gap_threshold
    
    # Flag rows that are part of a gap (the row after a large gap)
    df['gap_flag'] = df['is_large_gap'].astype(int)
    
    # Interpolate numeric columns for small gaps if needed, but for large gaps we flag
    # Here we simply mark the rows. Actual interpolation logic might depend on specific needs.
    # For this task, we ensure the flag is present.
    df = df.drop(columns=['time_diff', 'is_large_gap'])
    return df

def resample_to_hourly_median(df: pd.DataFrame, time_col: str = 'timestamp'):
    """
    Resample the data to hourly frequency using median aggregation.
    """
    df = df.set_index(time_col)
    # Select only numeric columns for aggregation
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) == 0:
        raise AlignmentError("No numeric columns found for resampling.")
    
    resampled = df[numeric_cols].resample('H').median()
    return resampled.reset_index()

def check_memory_usage(df: pd.DataFrame):
    """
    Check memory usage of the dataframe.
    """
    mem_usage = df.memory_usage(deep=True).sum() / (1024 ** 3)  # GB
    if mem_usage > MEMORY_WARNING_THRESHOLD_GB:
        logger.warning(f"Memory usage exceeds {MEMORY_WARNING_THRESHOLD_GB}GB: {mem_usage:.2f}GB. "
                       "Consider chunked processing in future phases.")
    return mem_usage

def validate_temporal_alignment(df: pd.DataFrame, time_col: str = 'timestamp', max_offset_minutes: int = MAX_TEMPORAL_OFFSET_MINUTES):
    """
    Validate that the temporal offset between any two consecutive rows is <= max_offset_minutes.
    Also checks for monotonic increase.
    
    Raises ValidationError if the check fails.
    """
    if time_col not in df.columns:
        raise ValidationError(f"Timestamp column '{time_col}' not found in dataframe.")

    # Check monotonicity
    if not df[time_col].is_monotonic_increasing:
        raise ValidationError("Timestamps are not monotonically increasing.")

    # Check offsets
    time_diffs = df[time_col].diff().dropna()
    max_offset = pd.Timedelta(minutes=max_offset_minutes)
    
    if (time_diffs > max_offset).any():
        # Find the specific gaps
        bad_gaps = time_diffs[time_diffs > max_offset]
        logger.error(f"Temporal offset exceeds {max_offset_minutes} minutes at {len(bad_gaps)} locations.")
        logger.error(f"Max offset found: {bad_gaps.max()}")
        raise ValidationError(f"Temporal offset exceeds {max_offset_minutes} minutes. "
                              f"Max offset: {bad_gaps.max()}. Data alignment failed.")
    
    logger.info(f"Temporal alignment validation passed. Max offset: {time_diffs.max()}")
    return True

def align_data(ace_path: str, noaa_path: str, output_path: str):
    """
    Main alignment pipeline:
    1. Load sources
    2. Merge
    3. Handle instrument transitions
    4. Detect gaps
    5. Resample to hourly median
    6. Validate temporal alignment
    7. Save output
    """
    logger.info("Starting data alignment pipeline.")
    
    # 1. Load
    sources = {'ace': ace_path, 'noaa': noaa_path}
    df = load_source_data(sources)
    
    # 2. Memory check
    check_memory_usage(df)
    
    # 3. Handle instrument transitions
    df = handle_instrument_transitions(df)
    
    # 4. Detect gaps
    df = detect_and_handle_gaps(df)
    
    # 5. Resample
    df_hourly = resample_to_hourly_median(df)
    
    # 6. Validate
    validate_temporal_alignment(df_hourly)
    
    # 7. Save
    logger.info(f"Saving aligned data to {output_path}")
    save_parquet(df_hourly, output_path)
    logger.info("Alignment pipeline completed successfully.")

def main():
    config = get_config()
    ace_path = config.get('paths', {}).get('ace_data', 'data/raw/ace_data.parquet')
    noaa_path = config.get('paths', {}).get('noaa_data', 'data/raw/noaa_data.parquet')
    output_path = config.get('paths', {}).get('aligned_data', 'data/processed/aligned_hourly.parquet')
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        align_data(ace_path, noaa_path, output_path)
    except Exception as e:
        logger.error(f"Alignment failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()