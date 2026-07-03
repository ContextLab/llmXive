"""
Preprocessing module for Satellite Laser Ranging (SLR) data.

This module handles:
- Quality filtering (residual exclusion)
- Time-alignment of multi-satellite datasets
- Merging datasets into a unified time series
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
from datetime import timedelta

# Constants
RESIDUAL_THRESHOLD_CM = 2.0  # cm
RESIDUAL_THRESHOLD_M = RESIDUAL_THRESHOLD_CM / 100.0  # meters


def filter_residuals(df: pd.DataFrame, threshold_m: float = RESIDUAL_THRESHOLD_M) -> pd.DataFrame:
    """
    Filter out SLR normal points with residuals exceeding the threshold.

    Args:
        df: DataFrame containing SLR normal points with a 'residual' column (in meters).
        threshold_m: Maximum allowed residual in meters (default: 2cm).

    Returns:
        Filtered DataFrame with rows where abs(residual) <= threshold_m.
    """
    if 'residual' not in df.columns:
        raise ValueError("DataFrame must contain a 'residual' column for filtering.")

    # Filter based on absolute residual value
    filtered_df = df[np.abs(df['residual']) <= threshold_m].copy()

    return filtered_df


def handle_sparse_satellites(
    df: pd.DataFrame,
    min_points: int = 500,
    satellite_col: str = 'satellite_id'
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Identify and optionally remove satellites with insufficient data points.

    Args:
        df: DataFrame containing SLR data with a 'satellite_id' column.
        min_points: Minimum number of points required for a satellite to be kept.
        satellite_col: Name of the column containing satellite identifiers.

    Returns:
        Tuple of (filtered_df, list_of_excluded_satellite_ids).
        If a satellite has fewer than min_points, it is removed from the DataFrame
        and its ID is added to the exclusion list.
    """
    if satellite_col not in df.columns:
        raise ValueError(f"DataFrame must contain a '{satellite_col}' column.")

    excluded_ids = []
    counts = df[satellite_col].value_counts()

    # Identify satellites below threshold
    sparse_satellites = counts[counts < min_points].index.tolist()
    excluded_ids.extend(sparse_satellites)

    if sparse_satellites:
        filtered_df = df[~df[satellite_col].isin(sparse_satellites)].copy()
    else:
        filtered_df = df.copy()

    return filtered_df, excluded_ids


def align_time_series(
    df_list: List[pd.DataFrame],
    time_col: str = 'time',
    freq: str = '1H',
    satellite_col: str = 'satellite_id'
) -> pd.DataFrame:
    """
    Align multiple satellite datasets to a common time grid by resampling.

    This function:
    1. Sets the time column as the index for each DataFrame.
    2. Determines the global time range (min to max) across all datasets.
    3. Resamples each dataset to the specified frequency (default: 1 hour).
    4. Merges the resampled datasets, filling missing values with NaN.

    Args:
        df_list: List of DataFrames, each representing a satellite's time series.
                 Each must have a 'time' column (datetime-like) and a 'satellite_id' column.
        time_col: Name of the time column (default: 'time').
        freq: Resampling frequency string for pandas (default: '1H').
        satellite_col: Name of the column containing satellite identifiers.

    Returns:
        A single DataFrame with:
        - A DatetimeIndex aligned to the specified frequency.
        - Columns for each satellite's measurements (e.g., 'range_LAGEOS-1', 'range_LAGEOS-2').
        - NaN for missing data points at specific times.
    """
    if not df_list:
        raise ValueError("At least one DataFrame must be provided in df_list.")

    # Validate inputs
    for i, df in enumerate(df_list):
        if time_col not in df.columns:
            raise ValueError(f"DataFrame {i} is missing the '{time_col}' column.")
        if satellite_col not in df.columns:
            raise ValueError(f"DataFrame {i} is missing the '{satellite_col}' column.")

    # Convert time columns to datetime if not already
    processed_dfs = []
    global_min_time = None
    global_max_time = None

    for df in df_list:
        df_temp = df.copy()
        df_temp[time_col] = pd.to_datetime(df_temp[time_col])
        processed_dfs.append(df_temp)

        current_min = df_temp[time_col].min()
        current_max = df_temp[time_col].max()

        if global_min_time is None or current_min < global_min_time:
            global_min_time = current_min
        if global_max_time is None or current_max > global_max_time:
            global_max_time = current_max

    # Create a common time index
    # Add a small buffer to ensure we capture the full range if needed, though range() is exclusive at end
    common_time_index = pd.date_range(start=global_min_time, end=global_max_time, freq=freq)

    aligned_dfs = []

    for df in processed_dfs:
        sat_id = df[satellite_col].iloc[0]  # Assume all rows in a DF have the same satellite ID
        df_indexed = df.set_index(time_col)

        # Resample to the common frequency
        # We use 'mean' for numeric columns. If there are non-numeric columns, we might need to handle them differently.
        # For SLR normal points, the key columns are usually numeric (range, residual, etc.)
        resampled = df_indexed.resample(freq).mean()

        # Reindex to the common time index to ensure alignment
        resampled = resampled.reindex(common_time_index)

        # Rename columns to include satellite ID to avoid conflicts
        # e.g., 'range' -> 'range_LAGEOS-1'
        resampled.columns = [f"{col}_{sat_id}" for col in resampled.columns]

        # Ensure the satellite_id column is preserved if needed, or we rely on the column suffix
        # Here we drop the satellite_id column from the data since the suffix identifies it
        if satellite_col in resampled.columns:
            resampled = resampled.drop(columns=[satellite_col])

        aligned_dfs.append(resampled)

    # Concatenate all aligned DataFrames horizontally
    final_df = pd.concat(aligned_dfs, axis=1)

    # Reset index to make time a column again if desired, or keep as index
    # The task implies merging into a dataset, often useful to have time as a column for CSV export
    final_df = final_df.reset_index().rename(columns={'index': time_col})

    return final_df


def merge_multi_satellite_datasets(
    dfs: List[pd.DataFrame],
    time_col: str = 'time',
    freq: str = '1H',
    threshold_m: float = RESIDUAL_THRESHOLD_M,
    min_points: int = 500
) -> pd.DataFrame:
    """
    End-to-end pipeline to filter, clean, and time-align multiple satellite datasets.

    Steps:
    1. Filter residuals for each satellite.
    2. Remove sparse satellites (optional, based on min_points).
    3. Align all remaining datasets to a common time grid.

    Args:
        dfs: List of DataFrames, each containing data for one satellite.
        time_col: Name of the time column.
        freq: Resampling frequency for time alignment.
        threshold_m: Residual threshold for quality filtering.
        min_points: Minimum points required per satellite to be included.

    Returns:
        A single merged DataFrame with time-aligned data from all valid satellites.
    """
    cleaned_dfs = []
    for df in dfs:
        # Step 1: Filter residuals
        filtered = filter_residuals(df, threshold_m)

        # Step 2: Handle sparse satellites (check count before or after? Usually after filtering)
        # We check if the filtered DF has enough points
        sat_id_col = 'satellite_id' if 'satellite_id' in df.columns else None
        if sat_id_col:
            if len(filtered) < min_points:
                # Log warning or skip
                continue
            cleaned_dfs.append(filtered)
        else:
            # If no satellite_id column, assume the whole DF is one satellite
            cleaned_dfs.append(filtered)

    if not cleaned_dfs:
        raise ValueError("No valid satellite data remaining after filtering.")

    # Step 3: Time alignment
    aligned_df = align_time_series(cleaned_dfs, time_col=time_col, freq=freq)

    return aligned_df
