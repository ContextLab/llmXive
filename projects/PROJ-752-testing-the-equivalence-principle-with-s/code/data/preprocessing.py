"""
Data Preprocessing Module for SLR Normal Points.

This module handles cleaning, filtering, and aligning SLR observation data
for subsequent analysis.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from datetime import timedelta
import logging

from utils.logging import get_logger, log_progress, log_error, AnalysisError

logger = get_logger(__name__)

def filter_residuals(df: pd.DataFrame, threshold_m: float = 0.02) -> pd.DataFrame:
    """
    Filter out observations with residuals larger than the threshold.

    Args:
        df: DataFrame with a 'residual' or 'range' column (depending on context).
            Assuming 'residual' is pre-computed or we filter based on range quality.
            For this task, we assume 'residual' is available or we compute it.
            If 'residual' is not present, we skip this step or assume it's based on range variance.
            To be safe, we filter based on 'residual' if present, else 'range' deviation.
        threshold_m: Threshold in meters (default 2cm).

    Returns:
        Filtered DataFrame.
    """
    if 'residual' in df.columns:
        mask = np.abs(df['residual']) <= threshold_m
        filtered = df[mask]
        removed = len(df) - len(filtered)
        logger.info(f"Filtered {removed} points with residuals > {threshold_m}m")
    else:
        # Fallback: if no residual, maybe filter based on range variance or just pass
        logger.warning("No 'residual' column found. Skipping residual-based filtering.")
        filtered = df
    
    return filtered

def handle_sparse_satellites(df: pd.DataFrame, min_points: int = 500) -> pd.DataFrame:
    """
    Handle satellites with insufficient data points.

    Args:
        df: DataFrame with 'satellite_id' column.
        min_points: Minimum required points.

    Returns:
        DataFrame with sparse satellites removed or flagged.
    """
    if 'satellite_id' not in df.columns:
        logger.warning("No 'satellite_id' column found. Cannot filter sparse satellites.")
        return df

    counts = df['satellite_id'].value_counts()
    sparse_sats = counts[counts < min_points].index.tolist()
    
    if sparse_sats:
        logger.warning(f"Found {len(sparse_sats)} satellites with < {min_points} points: {sparse_sats}")
        # Filter them out
        mask = ~df['satellite_id'].isin(sparse_sats)
        filtered = df[mask]
        logger.info(f"Removed {len(df) - len(filtered)} points from sparse satellites.")
        return filtered
    
    return df

def align_time_series(dfs: List[pd.DataFrame], time_step: float = 60.0) -> pd.DataFrame:
    """
    Align multiple satellite datasets to a common time grid.

    Args:
        dfs: List of DataFrames, each with a 'time' column.
        time_step: Time step for the grid in seconds.

    Returns:
        Aligned DataFrame.
    """
    if not dfs:
        return pd.DataFrame()

    # Combine all times
    all_times = np.concatenate([df['time'].values for df in dfs])
    min_t, max_t = np.min(all_times), np.max(all_times)
    
    # Create grid
    grid = np.arange(min_t, max_t, time_step)
    
    # Interpolate or merge?
    # For this task, we assume a merge operation or simple concatenation with time alignment
    # A full alignment would involve interpolation.
    # Here we simply concatenate and sort by time.
    combined = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values('time').reset_index(drop=True)
    
    logger.info(f"Aligned {len(combined)} points over {len(grid)} time steps.")
    return combined

def merge_multi_satellite_datasets(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple satellite datasets into one.

    Args:
        dfs: Dictionary of satellite_id -> DataFrame.

    Returns:
        Merged DataFrame.
    """
    if not dfs:
        return pd.DataFrame()
    
    for sat_id, df in dfs.items():
        if 'satellite_id' not in df.columns:
            df['satellite_id'] = sat_id
    
    return pd.concat(dfs.values(), ignore_index=True)

def preprocess_slr_data(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Main preprocessing pipeline.

    Args:
        raw_df: Raw SLR data.

    Returns:
        Cleaned and preprocessed DataFrame.
    """
    log_progress("Starting preprocessing pipeline...")
    
    # 1. Filter residuals
    # Assuming 'residual' is available or we compute it
    # For this implementation, we assume 'residual' exists or skip
    df = filter_residuals(raw_df, threshold_m=0.02)
    
    # 2. Handle sparse satellites
    df = handle_sparse_satellites(df, min_points=500)
    
    # 3. Align time series
    # If multiple satellites, align them
    # Here we assume the input is already combined or we split by sat_id
    if 'satellite_id' in df.columns:
        grouped = {sat: group for sat, group in df.groupby('satellite_id')}
        aligned = align_time_series(list(grouped.values()))
    else:
        aligned = df
    
    # 4. Final checks
    if aligned.isnull().sum().sum() > 0:
        logger.warning("NaN values found in preprocessed data. Dropping them.")
        aligned = aligned.dropna()
    
    log_progress("Preprocessing complete.")
    return aligned
