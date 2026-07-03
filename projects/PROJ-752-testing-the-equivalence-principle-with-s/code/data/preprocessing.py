import numpy as np
import pandas as pd
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field
from data.ingestion import NormalPoint, normal_points_to_dataframe
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class PreprocessingStats:
    """Container for statistics about the preprocessing pipeline."""
    original_points: int = 0
    filtered_out_residuals: int = 0
    filtered_out_sparse: int = 0
    final_points: int = 0
    satellites_processed: List[str] = field(default_factory=list)
    time_range_start: Optional[str] = None
    time_range_end: Optional[str] = None


def filter_residuals(df: pd.DataFrame, threshold_m: float = 0.02) -> Tuple[pd.DataFrame, int]:
    """
    Filter out normal points with residuals larger than the threshold.

    Args:
        df: DataFrame containing SLR data with a 'residual' column (in meters).
        threshold_m: Threshold in meters (default 0.02m = 2cm).

    Returns:
        Tuple of (filtered DataFrame, count of removed points).
    """
    original_count = len(df)
    if 'residual' not in df.columns:
        logger.warning("DataFrame missing 'residual' column; skipping residual filtering.")
        return df, 0

    mask = df['residual'].abs() <= threshold_m
    filtered_df = df[mask].copy()
    removed_count = original_count - len(filtered_df)

    if removed_count > 0:
        logger.info(f"Filtered {removed_count} points with residuals > {threshold_m*1000:.1f}mm")

    return filtered_df, removed_count


def handle_sparse_satellites(df: pd.DataFrame, min_points: int = 500) -> Tuple[pd.DataFrame, int]:
    """
    Remove satellites from the dataset that have fewer than min_points observations.

    Args:
        df: DataFrame containing SLR data with a 'satellite_id' column.
        min_points: Minimum number of points required to keep a satellite.

    Returns:
        Tuple of (filtered DataFrame, count of removed points).
    """
    original_count = len(df)
    if 'satellite_id' not in df.columns:
        logger.warning("DataFrame missing 'satellite_id' column; skipping sparse satellite handling.")
        return df, 0

    counts = df['satellite_id'].value_counts()
    sparse_satellites = counts[counts < min_points].index.tolist()

    if sparse_satellites:
        logger.warning(f"Removing {len(sparse_satellites)} sparse satellites: {sparse_satellites}")
        mask = ~df['satellite_id'].isin(sparse_satellites)
        filtered_df = df[mask].copy()
    else:
        filtered_df = df

    removed_count = original_count - len(filtered_df)
    return filtered_df, removed_count


def align_time_series(
    multi_df: pd.DataFrame,
    time_col: str = 'timestamp',
    freq: str = '1min',
    method: str = 'nearest'
) -> pd.DataFrame:
    """
    Align multi-satellite datasets to a common time grid.

    This function merges data from multiple satellites onto a unified time index,
    handling cases where satellites have different observation schedules.

    Args:
        multi_df: DataFrame containing combined data from multiple satellites.
                  Must have 'timestamp' (or time_col) and 'satellite_id' columns.
        time_col: Name of the timestamp column.
        freq: Resampling frequency (e.g., '1min', '10min', '1h').
        method: Method for filling missing values in the time alignment:
                'nearest', 'pad', 'backfill', or None for no filling.

    Returns:
        DataFrame with observations aligned to the common time grid.
        Includes a 'time_aligned' column with the canonical timestamp.
    """
    if multi_df.empty:
        logger.warning("Empty DataFrame provided to align_time_series.")
        return multi_df

    if time_col not in multi_df.columns:
        raise ValueError(f"DataFrame must contain '{time_col}' column for time alignment.")
    if 'satellite_id' not in multi_df.columns:
        raise ValueError("DataFrame must contain 'satellite_id' column for multi-satellite alignment.")

    # Ensure timestamp is datetime
    df = multi_df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col], utc=True)

    # Create a complete time index covering the range of the data
    start_time = df[time_col].min()
    end_time = df[time_col].max()

    # Generate the common time grid
    time_index = pd.date_range(start=start_time, end=end_time, freq=freq, tz='UTC')
    logger.info(f"Created time grid from {start_time} to {end_time} with freq {freq}")

    # Set timestamp as index for resampling/alignment
    df = df.set_index(time_col)

    # Create a MultiIndex to track satellite_id for each time slot
    # We will reindex per satellite then combine
    result_frames = []

    for sat_id in df['satellite_id'].unique():
        sat_df = df[df['satellite_id'] == sat_id].copy()
        sat_df = sat_df.sort_index()

        # Reindex to the common time grid
        # This creates NaNs for times where this satellite has no observation
        sat_df = sat_df.reindex(time_index)
        sat_df.index.name = 'time_aligned'
        sat_df['satellite_id'] = sat_id  # Ensure ID persists after reindex

        # Handle missing values based on method
        if method == 'nearest':
            # Only fill NaNs in numeric columns
            numeric_cols = sat_df.select_dtypes(include=[np.number]).columns
            sat_df[numeric_cols] = sat_df[numeric_cols].fillna(method='nearest')
        elif method == 'pad':
            sat_df = sat_df.ffill()
        elif method == 'backfill':
            sat_df = sat_df.bfill()
        # else: leave as NaN (no filling)

        result_frames.append(sat_df)

    # Concatenate all aligned satellite dataframes
    if result_frames:
        aligned_df = pd.concat(result_frames, axis=0)
        aligned_df = aligned_df.reset_index()
        aligned_df = aligned_df.rename(columns={'index': time_col})
        # Sort by time and satellite
        aligned_df = aligned_df.sort_values(by=[time_col, 'satellite_id']).reset_index(drop=True)

        logger.info(f"Time alignment complete. Result shape: {aligned_df.shape}")
        return aligned_df
    else:
        logger.warning("No data frames to align.")
        return df.reset_index()


def preprocess_normal_points(
    normal_points: List[NormalPoint],
    residual_threshold_m: float = 0.02,
    min_satellite_points: int = 500
) -> Tuple[pd.DataFrame, PreprocessingStats]:
    """
    Full preprocessing pipeline for a list of NormalPoint objects.

    1. Converts to DataFrame
    2. Filters by residual threshold
    3. Removes sparse satellites

    Args:
        normal_points: List of NormalPoint objects.
        residual_threshold_m: Max allowed residual (meters).
        min_satellite_points: Min points to keep a satellite.

    Returns:
        Tuple of (processed DataFrame, PreprocessingStats).
    """
    stats = PreprocessingStats(original_points=len(normal_points))

    if not normal_points:
        logger.warning("Empty list of NormalPoints provided.")
        return pd.DataFrame(), stats

    # Convert to DataFrame
    df = normal_points_to_dataframe(normal_points)
    stats.satellites_processed = list(df['satellite_id'].unique())

    # Filter residuals
    df, filtered_residuals = filter_residuals(df, residual_threshold_m)
    stats.filtered_out_residuals = filtered_residuals

    # Handle sparse satellites
    df, filtered_sparse = handle_sparse_satellites(df, min_satellite_points)
    stats.filtered_out_sparse = filtered_sparse

    stats.final_points = len(df)

    if not df.empty:
        stats.time_range_start = str(df['timestamp'].min())
        stats.time_range_end = str(df['timestamp'].max())

    logger.info(f"Preprocessing complete. Stats: {stats}")
    return df, stats


def preprocess_slr_data(
    input_df: pd.DataFrame,
    residual_threshold_m: float = 0.02,
    min_satellite_points: int = 500,
    align: bool = False,
    align_freq: str = '1min'
) -> Tuple[pd.DataFrame, PreprocessingStats]:
    """
    Preprocess SLR data from a DataFrame (e.g., output of ingestion).

    This function applies residual filtering, sparse satellite handling,
    and optional time alignment.

    Args:
        input_df: DataFrame from ingestion.
        residual_threshold_m: Max allowed residual (meters).
        min_satellite_points: Min points to keep a satellite.
        align: Whether to perform time alignment.
        align_freq: Frequency for time alignment if align=True.

    Returns:
        Tuple of (processed DataFrame, PreprocessingStats).
    """
    # Convert NormalPoint objects in the dataframe to a list if necessary,
    # or assume the dataframe is already in the format expected by filter_residuals.
    # The ingestion pipeline typically outputs a standard DataFrame.
    
    stats = PreprocessingStats(original_points=len(input_df))

    if input_df.empty:
        logger.warning("Empty DataFrame provided to preprocess_slr_data.")
        return input_df, stats

    df = input_df.copy()
    stats.satellites_processed = list(df['satellite_id'].unique())

    # Filter residuals
    df, filtered_residuals = filter_residuals(df, residual_threshold_m)
    stats.filtered_out_residuals = filtered_residuals

    # Handle sparse satellites
    df, filtered_sparse = handle_sparse_satellites(df, min_satellite_points)
    stats.filtered_out_sparse = filtered_sparse

    # Time alignment if requested
    if align:
        logger.info("Performing time alignment...")
        df = align_time_series(df, freq=align_freq, method='nearest')
        # Update stats after alignment (row count might change if NaNs dropped or filled)
        # Note: align_time_series keeps rows but fills NaNs, so count usually stays same
        # unless we dropna explicitly. We'll keep the count as is for now.
    
    stats.final_points = len(df)

    if not df.empty:
        stats.time_range_start = str(df['timestamp'].min())
        stats.time_range_end = str(df['timestamp'].max())

    logger.info(f"SLR Data preprocessing complete. Final shape: {df.shape}")
    return df, stats
