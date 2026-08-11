"""
Data Preprocessing Module for SLR Normal Point Data.

Handles quality filtering, time alignment, and merging.
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from datetime import timedelta
import logging
from utils.logging import get_logger, log_progress, log_error, AnalysisError

logger = get_logger(__name__)

def filter_residuals(df: pd.DataFrame, threshold_cm: float = 2.0) -> pd.DataFrame:
    """
    Filter out observations with residuals greater than the threshold.
    
    Args:
        df: Input DataFrame with 'residual' column (in meters).
        threshold_cm: Threshold in centimeters.
        
    Returns:
        Filtered DataFrame.
    """
    threshold_m = threshold_cm / 100.0
    initial_count = len(df)
    
    # Ensure residual column exists
    if 'residual' not in df.columns:
        log_error(logger, "Input DataFrame missing 'residual' column.")
        raise AnalysisError("Missing 'residual' column in input data.")
        
    # Handle potential NaNs in residuals by dropping them first
    df_clean = df.dropna(subset=['residual'])
    
    filtered_df = df_clean[abs(df_clean['residual']) <= threshold_m].copy()
    
    dropped = initial_count - len(filtered_df)
    log_progress(logger, f"Filtered {dropped} points with residuals > {threshold_cm}cm.")
    
    return filtered_df

def handle_sparse_satellites(df: pd.DataFrame, min_points: int = 500) -> pd.DataFrame:
    """
    Warn about or filter satellites with insufficient data.
    
    Args:
        df: Input DataFrame with 'satellite_id' column.
        min_points: Minimum required points per satellite.
        
    Returns:
        DataFrame (potentially filtered if strict mode is on, but here we just warn).
    """
    if 'satellite_id' not in df.columns:
        log_error(logger, "Input DataFrame missing 'satellite_id' column.")
        raise AnalysisError("Missing 'satellite_id' column.")
        
    counts = df['satellite_id'].value_counts()
    
    for sat_id, count in counts.items():
        if count < min_points:
            log_error(logger, f"Satellite {sat_id} has only {count} points (min: {min_points}). "
                              "This may lead to unreliable estimates.")
            
    return df

def align_time_series(df: pd.DataFrame, time_column: str = 'time') -> pd.DataFrame:
    """
    Ensure time column is in datetime format and sorted.
    
    Args:
        df: Input DataFrame.
        time_column: Name of the time column.
        
    Returns:
        DataFrame with sorted, parsed time.
    """
    if time_column not in df.columns:
        # Try to infer from common names
        if 'datetime' in df.columns:
            time_column = 'datetime'
        else:
            log_error(logger, f"Time column '{time_column}' not found.")
            raise AnalysisError("Time column missing.")
            
    if not pd.api.types.is_datetime64_any_dtype(df[time_column]):
        try:
            df[time_column] = pd.to_datetime(df[time_column], errors='raise')
        except Exception as e:
            log_error(logger, f"Failed to parse time column: {e}")
            raise AnalysisError("Time parsing failed.")
            
    df = df.sort_values(by=time_column).reset_index(drop=True)
    return df

def merge_multi_satellite_datasets(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple satellite DataFrames into one.
    
    Args:
        dfs: List of DataFrames.
        
    Returns:
        Combined DataFrame.
    """
    if not dfs:
        return pd.DataFrame()
        
    return pd.concat(dfs, ignore_index=True)

def preprocess_slr_data(raw_df: pd.DataFrame, config: Any) -> pd.DataFrame:
    """
    Main preprocessing pipeline: filter -> handle sparse -> align.
    
    Args:
        raw_df: Raw ingested DataFrame.
        config: Configuration object containing thresholds.
        
    Returns:
        Cleaned DataFrame ready for output.
    """
    log_progress(logger, "Starting preprocessing pipeline...")
    
    if raw_df is None or raw_df.empty:
        log_error(logger, "Preprocessing received empty DataFrame.")
        raise AnalysisError("Empty input to preprocessing.")
        
    # 1. Filter residuals
    try:
        filtered_df = filter_residuals(raw_df, threshold_cm=config.residual_threshold_cm)
    except AnalysisError:
        # If residual column missing, assume raw data is already clean or log error
        log_error(logger, "Skipping residual filter due to missing column.")
        filtered_df = raw_df
        
    # 2. Handle sparse satellites
    handle_sparse_satellites(filtered_df, min_points=config.min_points_per_satellite)
    
    # 3. Align time
    try:
        cleaned_df = align_time_series(filtered_df)
    except AnalysisError:
        log_error(logger, "Time alignment failed, proceeding with unsorted data.")
        cleaned_df = filtered_df
        
    log_progress(logger, f"Preprocessing complete. Final count: {len(cleaned_df)}")
    
    return cleaned_df
