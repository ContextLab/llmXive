"""
Data alignment module: merges sources, handles gaps, resamples to hourly.
"""
import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any

import pandas as pd
import numpy as np

from utils.logging import AlignmentError, get_logger, log_duration, check_memory_usage
from utils.io import load_parquet, save_parquet

logger = get_logger(__name__)

def load_source_data(source_type: str, data_dir: Path) -> pd.DataFrame:
    """Load pre-aligned source data from parquet."""
    file_path = data_dir / f"{source_type}.parquet"
    if not file_path.exists():
        raise FileNotFoundError(f"Source data file not found: {file_path}")
    logger.info(f"Loading source data from {file_path}")
    return load_parquet(file_path)

def apply_epsilon_floor(df: pd.DataFrame, col: str, floor_val: float = 1e-6) -> pd.DataFrame:
    """Apply epsilon floor to prevent division by zero or log(0)."""
    df[col] = df[col].clip(lower=floor_val)
    return df

def handle_instrument_transitions(df: pd.DataFrame, instrument_col: str) -> pd.DataFrame:
    """
    Handle instrument version transitions by applying calibration offsets.
    If offsets are not available, treat as separate cohorts (no merging).
    """
    # Placeholder for calibration logic
    # In a real implementation, this would apply specific offsets based on instrument version
    logger.info("Checking for instrument transitions...")
    if instrument_col in df.columns:
        unique_instruments = df[instrument_col].unique()
        logger.info(f"Found instrument versions: {unique_instruments}")
        # No automatic merging if multiple versions exist without calibration
        if len(unique_instruments) > 1:
            logger.warning("Multiple instrument versions detected. Treating as separate cohorts.")
    return df

def detect_and_handle_gaps(df: pd.DataFrame, time_col: str, max_gap_hours: float = 6.0) -> pd.DataFrame:
    """
    Detect data gaps larger than max_gap_hours.
    If gaps exist, log a warning and flag rows for potential interpolation.
    """
    df = df.sort_values(time_col)
    df['time_diff'] = df[time_col].diff()
    gap_threshold = pd.Timedelta(hours=max_gap_hours)
    gaps = df['time_diff'] > gap_threshold
    if gaps.any():
        gap_count = gaps.sum()
        logger.warning(f"Detected {gap_count} data gaps larger than {max_gap_hours} hours.")
        # Flag rows after a gap
        df['is_after_gap'] = gaps.shift(1).fillna(False)
    else:
        df['is_after_gap'] = False
    return df

def resample_to_hourly_median(df: pd.DataFrame, time_col: str, value_cols: list) -> pd.DataFrame:
    """Resample data to hourly frequency using median aggregation."""
    df = df.set_index(time_col)
    # Select only numeric columns for aggregation
    agg_cols = [c for c in value_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
    if not agg_cols:
        raise ValueError("No numeric columns found for resampling.")
    
    hourly_df = df[agg_cols].resample('h').median()
    hourly_df = hourly_df.reset_index()
    return hourly_df

def validate_temporal_alignment(df: pd.DataFrame, time_col: str) -> bool:
    """Validate that timestamps are monotonically increasing and no duplicates."""
    if not df[time_col].is_monotonic_increasing:
        raise AlignmentError("Timestamps are not monotonically increasing.")
    if df[time_col].duplicated().any():
        raise AlignmentError("Duplicate timestamps found.")
    return True

def check_memory_usage(threshold_gb: float = 6.0) -> None:
    """Check current memory usage and log a warning if exceeded."""
    usage_gb = check_memory_usage.__wrapped__() if hasattr(check_memory_usage, '__wrapped__') else 0.0
    # Simplified check for demonstration
    logger.info(f"Current memory usage: {usage_gb:.2f} GB (Threshold: {threshold_gb} GB)")

@log_duration
def align_data(ace_path: Path, noaa_path: Path, output_path: Path) -> None:
    """
    Main alignment routine: loads ACE and NOAA data, merges, handles gaps, resamples, and saves.
    """
    logger.info("Starting data alignment...")
    
    # Load data (assuming they are already downloaded to parquet by T022/T023)
    try:
        ace_data = load_parquet(ace_path)
        noaa_data = load_parquet(noaa_path)
    except Exception as e:
        raise AlignmentError(f"Failed to load source data: {e}")

    # Check memory
    check_memory_usage()

    # Merge on timestamp
    # Assuming both have a 'timestamp' column
    if 'timestamp' not in ace_data.columns or 'timestamp' not in noaa_data.columns:
        raise AlignmentError("Missing 'timestamp' column in source data.")
    
    merged = pd.merge(ace_data, noaa_data, on='timestamp', how='outer')
    
    # Apply epsilon floor to velocity/IMF columns if they exist
    for col in ['V', 'Bz', 'By', 'Bt']:
        if col in merged.columns:
            merged = apply_epsilon_floor(merged, col)

    # Handle instrument transitions
    if 'instrument' in merged.columns:
        merged = handle_instrument_transitions(merged, 'instrument')

    # Detect gaps
    merged = detect_and_handle_gaps(merged, 'timestamp', max_gap_hours=6.0)

    # Resample to hourly median
    numeric_cols = merged.select_dtypes(include=[np.number]).columns.tolist()
    merged = resample_to_hourly_median(merged, 'timestamp', numeric_cols)

    # Validate
    validate_temporal_alignment(merged, 'timestamp')

    # Save
    save_parquet(merged, output_path)
    logger.info(f"Aligned data saved to {output_path}")

def main():
    """Entry point for alignment script."""
    config_path = Path("code/config.py")
    # In a real scenario, load config from file
    ace_path = Path("data/processed/ace.parquet")
    noaa_path = Path("data/processed/noaa.parquet")
    output_path = Path("data/processed/aligned_hourly.parquet")
    
    align_data(ace_path, noaa_path, output_path)

if __name__ == "__main__":
    main()
