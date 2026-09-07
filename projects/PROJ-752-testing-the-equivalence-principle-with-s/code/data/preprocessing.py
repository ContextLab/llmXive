import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from datetime import timedelta
import logging
from utils.logging import get_logger, log_progress, log_error, AnalysisError

logger = get_logger(__name__)

def filter_residuals(df: pd.DataFrame, threshold_cm: float = 2.0) -> pd.DataFrame:
    """
    Filter SLR normal points based on residual magnitude.
    
    Args:
        df: DataFrame with at least 'residual_m' column.
        threshold_cm: Maximum allowed residual in centimeters (default 2.0 cm).
        
    Returns:
        Filtered DataFrame.
        
    Raises:
        AnalysisError: If required columns are missing.
    """
    required_cols = ['residual_m']
    if not all(col in df.columns for col in required_cols):
        raise AnalysisError(f"DataFrame missing required columns: {required_cols}")
        
    threshold_m = threshold_cm / 100.0
    valid_mask = np.abs(df['residual_m']) <= threshold_m
    
    log_progress(logger, f"Filtered {len(df) - valid_mask.sum()} points exceeding {threshold_cm}cm threshold")
    return df[valid_mask].copy()

def handle_sparse_satellites(df: pd.DataFrame, min_points: int = 500) -> pd.DataFrame:
    """
    Handle satellites with insufficient data points.
    
    Args:
        df: DataFrame with 'satellite_id' column.
        min_points: Minimum required points per satellite.
        
    Returns:
        DataFrame with sparse satellites flagged or removed (based on context).
        Currently returns full DF but logs warnings for sparse satellites.
        
    Raises:
        AnalysisError: If 'satellite_id' column is missing.
    """
    if 'satellite_id' not in df.columns:
        raise AnalysisError("DataFrame missing 'satellite_id' column")
        
    counts = df['satellite_id'].value_counts()
    sparse_ids = counts[counts < min_points].index.tolist()
    
    if sparse_ids:
        log_error(logger, f"Found {len(sparse_ids)} satellites with <{min_points} points: {sparse_ids}")
        # Note: We do not drop them here; downstream logic or T018 will handle the warning logic
        # This function ensures the data is available for the warning mechanism.
        
    return df

def align_time_series(df: pd.DataFrame, time_col: str = 'time', tolerance: str = '1s') -> pd.DataFrame:
    """
    Align time series to a regular grid (optional, for interpolation needs).
    Currently returns a sorted copy to ensure time ordering for merging.
    
    Args:
        df: DataFrame with time column.
        time_col: Name of the time column.
        tolerance: Pandas frequency tolerance string (not strictly used for sort, but for future resample).
        
    Returns:
        Sorted DataFrame by time.
    """
    if time_col not in df.columns:
        raise AnalysisError(f"DataFrame missing time column: {time_col}")
        
    df_sorted = df.sort_values(by=time_col).reset_index(drop=True)
    return df_sorted

def merge_multi_satellite_datasets(
    df_list: List[pd.DataFrame], 
    time_col: str = 'time', 
    tolerance: str = '1s'
) -> pd.DataFrame:
    """
    Merge multiple satellite datasets into a single time-aligned DataFrame.
    
    This function performs an outer join on time to allow for non-overlapping
    observation windows, then sorts by time. It assumes each input DataFrame
    has a 'satellite_id' column to distinguish sources.
    
    Args:
        df_list: List of DataFrames, each representing one satellite's data.
        time_col: Name of the time column to align on.
        tolerance: Tolerance for time alignment (passed to pandas merge logic if needed).
        
    Returns:
        Merged DataFrame with all satellites, sorted by time.
        
    Raises:
        AnalysisError: If any input DataFrame is empty or missing required columns.
    """
    if not df_list:
        raise AnalysisError("No DataFrames provided for merging.")
        
    if not all('satellite_id' in df.columns for df in df_list):
        raise AnalysisError("All input DataFrames must contain 'satellite_id' column.")
        
    if not all(time_col in df.columns for df in df_list):
        raise AnalysisError(f"All input DataFrames must contain '{time_col}' column.")
        
    # Filter out empty dataframes
    valid_dfs = [df for df in df_list if not df.empty]
    if not valid_dfs:
        logger.warning("All input DataFrames were empty. Returning empty DataFrame.")
        return pd.DataFrame()
        
    # Concatenate and sort
    # Using concat is more efficient than iterative merging for time alignment
    # when the goal is a single time-ordered stream for joint analysis
    combined = pd.concat(valid_dfs, ignore_index=True)
    combined = combined.sort_values(by=time_col).reset_index(drop=True)
    
    log_progress(logger, f"Merged {len(valid_dfs)} satellite datasets into {len(combined)} total points")
    return combined

def preprocess_slr_data(
    raw_data: pd.DataFrame, 
    threshold_cm: float = 2.0,
    min_points: int = 500
) -> pd.DataFrame:
    """
    End-to-end preprocessing pipeline for SLR data.
    
    1. Filter residuals > threshold_cm
    2. Check for sparse satellites (logs warning if < min_points)
    3. Align time series (sort by time)
    4. Merge multi-satellite data if multiple IDs present
    
    Args:
        raw_data: Raw DataFrame from ingestion.
        threshold_cm: Residual filtering threshold.
        min_points: Minimum points per satellite warning threshold.
        
    Returns:
        Cleaned, time-aligned DataFrame ready for estimation.
    """
    if raw_data.empty:
        raise AnalysisError("Input raw_data is empty.")
        
    # 1. Filter
    filtered = filter_residuals(raw_data, threshold_cm)
    
    # 2. Handle sparse (logging side-effect)
    handle_sparse_satellites(filtered, min_points)
    
    # 3 & 4. Align and Merge
    # If multiple satellites, merge_multi_satellite_datasets ensures a single coherent stream
    # If single satellite, it just sorts.
    result = merge_multi_satellite_datasets([filtered], time_col='time')
    
    # Ensure no NaN values in critical columns
    critical_cols = ['time', 'residual_m', 'satellite_id']
    existing_cols = [c for c in critical_cols if c in result.columns]
    if existing_cols:
        nan_counts = result[existing_cols].isna().sum()
        if nan_counts.any():
            log_error(logger, f"Found NaN values in critical columns: {nan_counts[nan_counts > 0].to_dict()}")
            # Drop rows with NaN in critical columns
            result = result.dropna(subset=existing_cols)
            
    return result
