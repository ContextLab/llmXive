"""
Preprocessing module for Satellite Laser Ranging (SLR) data.

This module handles quality filtering, sparse satellite handling,
and time-alignment logic for multi-satellite datasets.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from datetime import timedelta
import logging

from utils.logging import get_logger, AnalysisError

logger = get_logger(__name__)


def filter_residuals(df: pd.DataFrame, threshold_cm: float = 2.0) -> pd.DataFrame:
    """
    Filter out SLR observations with residuals exceeding a threshold.

    Args:
        df: DataFrame containing SLR observations with a 'residual' column (in meters).
        threshold_cm: Threshold in centimeters (default 2.0 cm).

    Returns:
        Filtered DataFrame with residuals <= threshold_cm.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    threshold_m = threshold_cm / 100.0
    mask = np.abs(df['residual']) <= threshold_m
    filtered_df = df[mask].copy()
    removed_count = len(df) - len(filtered_df)
    if removed_count > 0:
        logger.info(f"Removed {removed_count} points with residuals > {threshold_cm}cm.")
    return filtered_df


def handle_sparse_satellites(df: pd.DataFrame, min_points: int = 500) -> Tuple[pd.DataFrame, List[str]]:
    """
    Identify and flag satellites with insufficient data points.

    Args:
        df: DataFrame with a 'satellite_id' column.
        min_points: Minimum required points per satellite.

    Returns:
        Tuple of (filtered DataFrame with sparse satellites removed, list of removed IDs).
    """
    if df.empty:
        return df, []

    counts = df['satellite_id'].value_counts()
    sparse_ids = counts[counts < min_points].index.tolist()

    if sparse_ids:
        logger.warning(f"Found {len(sparse_ids)} satellites with < {min_points} points: {sparse_ids}")
        filtered_df = df[~df['satellite_id'].isin(sparse_ids)].copy()
    else:
        filtered_df = df.copy()

    return filtered_df, sparse_ids


def align_time_series(
    df: pd.DataFrame,
    time_col: str = 'time',
    tolerance_seconds: float = 60.0
) -> pd.DataFrame:
    """
    Align time series data to a common grid or ensure consistent time indexing.

    This function sorts the data by time and ensures the time column is a datetime64 type.
    It does not resample but prepares the data for merging by ensuring sorted order.

    Args:
        df: Input DataFrame.
        time_col: Name of the time column.
        tolerance_seconds: Logging threshold for large time gaps (not used for filtering here).

    Returns:
        DataFrame sorted by time with proper datetime type.
    """
    if df.empty:
        return df

    if time_col not in df.columns:
        raise AnalysisError(f"Time column '{time_col}' not found in DataFrame.")

    # Ensure datetime type
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        logger.info(f"Converting '{time_col}' to datetime.")
        df[time_col] = pd.to_datetime(df[time_col])

    # Sort by time
    df_sorted = df.sort_values(by=time_col).reset_index(drop=True)

    # Log large gaps if they exist (optional diagnostic)
    if len(df_sorted) > 1:
        time_diffs = df_sorted[time_col].diff().dt.total_seconds()
        max_gap = time_diffs.max()
        if max_gap > tolerance_seconds:
            logger.warning(f"Large time gap detected: {max_gap:.1f}s (tolerance: {tolerance_seconds}s)")

    return df_sorted


def merge_multi_satellite_datasets(
    dataframes: Dict[str, pd.DataFrame],
    time_col: str = 'time',
    tolerance_seconds: float = 60.0
) -> pd.DataFrame:
    """
    Merge multiple satellite datasets into a single aligned DataFrame.

    This function takes a dictionary of DataFrames (keyed by satellite_id),
    aligns their time series, and concatenates them into one master dataset.

    Args:
        dataframes: Dict mapping satellite_id -> DataFrame.
        time_col: Name of the time column.
        tolerance_seconds: Tolerance for time alignment warnings.

    Returns:
        Merged DataFrame with all satellites, sorted by time.
    """
    if not dataframes:
        logger.warning("No dataframes provided for merging.")
        return pd.DataFrame()

    processed_dfs = []
    for sat_id, df in dataframes.items():
        if df is None or df.empty:
            logger.warning(f"Skipping empty or None DataFrame for satellite {sat_id}")
            continue

        # Ensure satellite_id column exists
        if 'satellite_id' not in df.columns:
            df = df.copy()
            df['satellite_id'] = sat_id

        # Align time series for this satellite
        aligned_df = align_time_series(df, time_col=time_col, tolerance_seconds=tolerance_seconds)
        processed_dfs.append(aligned_df)

    if not processed_dfs:
        logger.warning("No valid dataframes after processing.")
        return pd.DataFrame()

    # Concatenate all
    merged_df = pd.concat(processed_dfs, ignore_index=True)
    logger.info(f"Merged {len(processed_dfs)} satellite datasets into {len(merged_df)} total rows.")

    return merged_df


def preprocess_slr_data(
    raw_data_path: str,
    output_path: str,
    residual_threshold_cm: float = 2.0,
    min_points_per_sat: int = 500
) -> pd.DataFrame:
    """
    Full preprocessing pipeline: load, filter, handle sparse, and align.

    Args:
        raw_data_path: Path to the raw CSV containing merged satellite data.
        output_path: Path to save the cleaned CSV.
        residual_threshold_cm: Threshold for residual filtering.
        min_points_per_sat: Minimum points required per satellite.

    Returns:
        The cleaned DataFrame.
    """
    logger.info(f"Loading raw data from {raw_data_path}")
    try:
        df = pd.read_csv(raw_data_path)
    except FileNotFoundError:
        raise AnalysisError(f"Raw data file not found: {raw_data_path}")

    # 1. Filter residuals
    df = filter_residuals(df, threshold_cm=residual_threshold_cm)

    # 2. Handle sparse satellites
    df, removed_sats = handle_sparse_satellites(df, min_points=min_points_per_sat)

    # 3. Align time series (sort and ensure types)
    df = align_time_series(df)

    # 4. Save output
    logger.info(f"Saving cleaned data to {output_path}")
    df.to_csv(output_path, index=False)

    logger.info(f"Preprocessing complete. Rows: {len(df)}, Removed Satellites: {removed_sats}")
    return df