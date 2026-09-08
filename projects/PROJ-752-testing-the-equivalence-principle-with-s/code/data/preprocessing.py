import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from datetime import timedelta
import logging
import sys
import os

# Import from local utils
from utils.logging import get_logger

logger = get_logger(__name__)

# Constants
MIN_POINTS_THRESHOLD = 500

def filter_residuals(df: pd.DataFrame, residual_column: str = 'residual', threshold_m: float = 0.02) -> pd.DataFrame:
    """
    Filter out SLR normal points with residuals greater than the threshold (2cm default).
    
    Args:
        df: DataFrame containing SLR observations.
        residual_column: Name of the column containing residual values (in meters).
        threshold_m: Maximum allowed residual in meters (default 0.02m = 2cm).
        
    Returns:
        Filtered DataFrame.
    """
    if residual_column not in df.columns:
        logger.warning(f"Column '{residual_column}' not found in dataframe. Skipping residual filter.")
        return df
        
    initial_count = len(df)
    filtered_df = df[np.abs(df[residual_column]) <= threshold_m]
    removed_count = initial_count - len(filtered_df)
    
    if removed_count > 0:
        logger.info(f"Filtered {removed_count} points with residuals > {threshold_m*1000:.1f}mm.")
    
    return filtered_df

def handle_sparse_satellites(df: pd.DataFrame, satellite_id_col: str = 'satellite_id', min_points: int = MIN_POINTS_THRESHOLD) -> Tuple[pd.DataFrame, List[str]]:
    """
    Identify and exclude satellites with insufficient data points.
    
    Requirement T018:
    1. Log a specific "Insufficient Data" warning for satellites with < min_points.
    2. Explicitly exclude these satellites from the returned DataFrame.
    3. Return the list of excluded satellite IDs for downstream reporting.
    
    Args:
        df: DataFrame containing SLR observations.
        satellite_id_col: Name of the column containing satellite identifiers.
        min_points: Minimum number of points required (default 500).
        
    Returns:
        Tuple of (Filtered DataFrame with sufficient satellites, List of excluded satellite IDs).
    """
    if satellite_id_col not in df.columns:
        raise ValueError(f"Column '{satellite_id_col}' not found in dataframe.")
        
    satellite_counts = df[satellite_id_col].value_counts()
    excluded_satellites = []
    
    for sat_id, count in satellite_counts.items():
        if count < min_points:
            excluded_satellites.append(sat_id)
            logger.warning(f"Insufficient Data: Satellite '{sat_id}' has {count} points (threshold: {min_points}). Excluding from joint estimation.")
    
    if excluded_satellites:
        # Explicitly exclude
        valid_satellites = [s for s in satellite_counts.index if s not in excluded_satellites]
        filtered_df = df[df[satellite_id_col].isin(valid_satellites)]
        logger.info(f"Excluded {len(excluded_satellites)} satellites due to insufficient data.")
    else:
        filtered_df = df
        
    return filtered_df, excluded_satellites

def align_time_series(df: pd.DataFrame, timestamp_col: str = 'timestamp', freq: str = 'H') -> pd.DataFrame:
    """
    Align time series to a regular frequency (optional resampling).
    
    Args:
        df: DataFrame with time series data.
        timestamp_col: Name of the timestamp column.
        freq: Pandas frequency string for resampling (default 'H' for hourly).
        
    Returns:
        Resampled DataFrame (if applicable).
    """
    # Basic alignment logic placeholder for T017 dependency
    if timestamp_col in df.columns:
        df[timestamp_col] = pd.to_datetime(df[timestamp_col])
        df = df.sort_values(timestamp_col)
    return df

def merge_multi_satellite_datasets(dfs: List[pd.DataFrame], common_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Merge multiple satellite datasets into a single DataFrame.
    
    Args:
        dfs: List of DataFrames.
        common_cols: Columns to use for merging if needed.
        
    Returns:
        Merged DataFrame.
    """
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

def preprocess_slr_data(
    df: pd.DataFrame, 
    residual_col: str = 'residual', 
    sat_id_col: str = 'satellite_id',
    timestamp_col: str = 'timestamp'
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Orchestrate the full preprocessing pipeline including filtering and exclusion logic.
    
    This function implements the core logic for T016 (filtering) and T018 (exclusion).
    
    Args:
        df: Raw SLR data DataFrame.
        residual_col: Column name for residuals.
        sat_id_col: Column name for satellite IDs.
        timestamp_col: Column name for timestamps.
        
    Returns:
        Tuple of (Cleaned DataFrame, List of excluded satellite IDs).
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Filter residuals > 2cm (T016)
    df_filtered = filter_residuals(df, residual_column=residual_col, threshold_m=0.02)
    
    # 2. Handle sparse satellites / Exclusion Logic (T018)
    df_clean, excluded_list = handle_sparse_satellites(
        df_filtered, 
        satellite_id_col=sat_id_col, 
        min_points=MIN_POINTS_THRESHOLD
    )
    
    # 3. Time alignment (T017)
    df_aligned = align_time_series(df_clean, timestamp_col=timestamp_col)
    
    logger.info(f"Preprocessing complete. Final shape: {df_aligned.shape}, Excluded satellites: {excluded_list}")
    return df_aligned, excluded_list

def main():
    """
    CLI entry point for preprocessing (for testing/debugging).
    Expects input CSV and outputs cleaned CSV + excluded list JSON.
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Preprocess SLR data")
    parser.add_argument('--input', type=str, required=True, help='Input CSV path')
    parser.add_argument('--output', type=str, required=True, help='Output CSV path')
    parser.add_argument('--excluded-log', type=str, default='data/processed/excluded_satellites.json', help='JSON log of excluded satellites')
    args = parser.parse_args()
    
    logger.info(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    cleaned_df, excluded = preprocess_slr_data(df)
    
    logger.info(f"Saving cleaned data to {args.output}")
    cleaned_df.to_csv(args.output, index=False)
    
    logger.info(f"Saving excluded satellites list to {args.excluded_log}")
    os.makedirs(os.path.dirname(args.excluded_log), exist_ok=True)
    with open(args.excluded_log, 'w') as f:
        json.dump(excluded, f, indent=2)
        
    logger.info("Done.")

if __name__ == '__main__':
    main()
