import os
import sys
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from utils.logging import AlignmentError, get_logger, check_memory_usage

def load_source_data(file_path: Path) -> pd.DataFrame:
    logger = get_logger()
    if not file_path.exists():
        raise AlignmentError(f"Source file not found: {file_path}")
    logger.info(f"Loading data from {file_path}")
    return pd.read_csv(file_path, parse_dates=["timestamp"])

def apply_epsilon_floor(df: pd.DataFrame, column: str, floor: float = 1e-6) -> pd.DataFrame:
    logger = get_logger()
    if column not in df.columns:
        logger.warning(f"Column {column} not found, skipping epsilon floor.")
        return df
    df[column] = df[column].clip(lower=floor)
    return df

def handle_instrument_transitions(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_logger()
    # Placeholder for instrument transition logic
    logger.info("Handling instrument transitions (no-op for synthetic data).")
    return df

def detect_and_handle_gaps(df: pd.DataFrame, time_col: str = "timestamp", max_gap_hours: int = 6) -> pd.DataFrame:
    logger = get_logger()
    df = df.sort_values(time_col)
    df["time_diff"] = df[time_col].diff()
    gaps = df[df["time_diff"] > pd.Timedelta(hours=max_gap_hours)]
    if not gaps.empty:
        logger.warning(f"Detected {len(gaps)} large gaps (> {max_gap_hours}h).")
        # Interpolation for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].interpolate(method="time")
    return df.drop(columns=["time_diff"], errors="ignore")

def resample_to_hourly_median(df: pd.DataFrame, time_col: str = "timestamp") -> pd.DataFrame:
    logger = get_logger()
    df = df.set_index(time_col)
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df_resampled = df[numeric_cols].resample("H").median()
    df_resampled = df_resampled.dropna(how="all")
    df_resampled = df_resampled.reset_index()
    logger.info(f"Resampled to hourly median. Shape: {df_resampled.shape}")
    return df_resampled

def validate_temporal_alignment(df: pd.DataFrame, time_col: str = "timestamp") -> bool:
    logger = get_logger()
    if not df[time_col].is_monotonic_increasing:
        raise AlignmentError("Timestamps are not monotonically increasing.")
    return True

def align_data(ace_df: pd.DataFrame, noaa_df: pd.DataFrame) -> pd.DataFrame:
    logger = get_logger()
    # Merge on timestamp
    merged = pd.merge(ace_df, noaa_df, on="timestamp", how="outer")
    merged = detect_and_handle_gaps(merged)
    merged = apply_epsilon_floor(merged, "v_bs")
    merged = resample_to_hourly_median(merged)
    validate_temporal_alignment(merged)
    return merged

def main():
    logger = get_logger()
    logger.info("Align module called (no-op in this context, invoked by ingestion scripts).")

def check_memory_usage(threshold_gb: float = 6.0) -> bool:
    return check_memory_usage(threshold_gb)
