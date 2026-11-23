"""
Utility functions for data validation and imputation.
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Union, Dict
from pathlib import Path
import logging
from config import DATA_DIR, RND_SEED

logger = logging.getLogger("data_utils")

def validate_coordinates(df: pd.DataFrame) -> pd.Series:
    """
    Validate that latitude is between -90 and 90, and longitude between -180 and 180.
    Returns a boolean Series where True indicates valid coordinates.
    """
    lat = df['decimalLatitude']
    lon = df['decimalLongitude']
    
    valid_lat = (lat >= -90) & (lat <= 90)
    valid_lon = (lon >= -180) & (lon <= 180)
    
    return valid_lat & valid_lon

def impute_missing_nearest_neighbor(df: pd.DataFrame, target_cols: List[str]) -> pd.DataFrame:
    """
    Impute missing values in target_cols using nearest neighbor based on coordinates.
    This is a simplified implementation assuming spatial proximity.
    """
    if df.empty:
        return df

    df_copy = df.copy()
    
    # Identify rows with missing values
    mask_missing = df_copy[target_cols].isnull().any(axis=1)
    if not mask_missing.any():
        return df_copy

    # Identify rows with complete data
    mask_complete = ~df_copy[target_cols].isnull().any(axis=1)
    complete_data = df_copy[mask_complete]
    
    if complete_data.empty:
        logger.warning("No complete data available for nearest neighbor imputation.")
        return df_copy

    # For each missing row, find the nearest complete row based on coordinates
    # This is O(N*M) which might be slow for large datasets, but acceptable for validation
    lat_col = 'decimalLatitude'
    lon_col = 'decimalLongitude'
    
    missing_indices = df_copy[mask_missing].index
    
    for idx in missing_indices:
        # Get coordinates of the missing point
        missing_lat = df_copy.loc[idx, lat_col]
        missing_lon = df_copy.loc[idx, lon_col]
        
        # Calculate distances to all complete points
        # Using simple Euclidean distance on lat/lon as an approximation
        distances = np.sqrt(
            (complete_data[lat_col] - missing_lat)**2 + 
            (complete_data[lon_col] - missing_lon)**2
        )
        
        # Find the nearest complete point
        nearest_idx = distances.idxmin()
        
        # Impute values
        for col in target_cols:
            if pd.isnull(df_copy.loc[idx, col]):
                df_copy.loc[idx, col] = complete_data.loc[nearest_idx, col]
    
    return df_copy

def handle_missing_values(df: pd.DataFrame, target_cols: List[str]) -> pd.DataFrame:
    """
    Handle missing values in the dataframe using nearest neighbor imputation.
    """
    return impute_missing_nearest_neighbor(df, target_cols)

def validate_and_clean_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate coordinates and drop rows with invalid coordinates.
    """
    valid_mask = validate_coordinates(df)
    return df[valid_mask].copy()

def check_data_quality(df: pd.DataFrame) -> Dict:
    """
    Perform basic data quality checks and return a summary.
    """
    quality_report = {
        "total_records": len(df),
        "invalid_coordinates": (~validate_coordinates(df)).sum(),
        "missing_climate_values": df.isnull().sum().sum(),
        "duplicate_coordinates": df.duplicated(subset=['decimalLatitude', 'decimalLongitude']).sum()
    }
    return quality_report
