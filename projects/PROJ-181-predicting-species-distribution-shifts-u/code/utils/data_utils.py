"""
Data Utility Functions.
Coordinate validation, missing value imputation, and error handling.
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Union
from pathlib import Path
import logging
from config import DATA_DIR, RND_SEED
from sklearn.impute import KNNImputer

logger = logging.getLogger(__name__)

def validate_coordinates(df: pd.DataFrame, lat_col: str = 'decimalLatitude', lon_col: str = 'decimalLongitude') -> pd.DataFrame:
    """
    Validates and filters coordinates to be within valid ranges.
    
    Args:
        df: Input DataFrame
        lat_col: Name of latitude column
        lon_col: Name of longitude column
        
    Returns:
        Filtered DataFrame with valid coordinates
    """
    if lat_col not in df.columns or lon_col not in df.columns:
        logger.error(f"Columns {lat_col} or {lon_col} not found in DataFrame.")
        return df.drop(columns=[lat_col, lon_col] if lat_col in df.columns and lon_col in df.columns else [])
    
    valid_mask = (
        (df[lat_col].notna()) & 
        (df[lon_col].notna()) &
        (df[lat_col] >= -90) & (df[lat_col] <= 90) &
        (df[lon_col] >= -180) & (df[lon_col] <= 180)
    )
    invalid_count = len(df) - valid_mask.sum()
    if invalid_count > 0:
        logger.warning(f"Removed {invalid_count} records with invalid coordinates.")
    return df[valid_mask].copy()

def impute_missing_nearest_neighbor(df: pd.DataFrame, target_col: str, cols_to_use: List[str]) -> pd.DataFrame:
    """
    Imputes missing values in target_col using KNN imputation based on cols_to_use.
    
    Args:
        df: Input DataFrame
        target_col: Column to impute
        cols_to_use: List of columns to use for calculating distance/neighbors
        
    Returns:
        DataFrame with imputed values
    """
    if df[target_col].isna().sum() == 0:
        logger.info(f"No missing values in {target_col}. Skipping imputation.")
        return df
    
    if not cols_to_use:
        logger.warning(f"No columns provided for KNN imputation. Falling back to mean imputation for {target_col}.")
        mean_val = df[target_col].mean()
        if pd.isna(mean_val):
            raise ValueError(f"Cannot compute mean for {target_col} (all NaN).")
        df[target_col] = df[target_col].fillna(mean_val)
        return df
    
    # Ensure all cols_to_use exist
    missing_cols = [c for c in cols_to_use if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found in DataFrame for KNN imputation: {missing_cols}")
    
    try:
        imputer = KNNImputer(n_neighbors=5)
        # We need to impute target_col, but use cols_to_use to find neighbors.
        # KNNImputer works on the whole matrix provided.
        # Strategy: Impute the subset [target_col] + cols_to_use, then extract target_col.
        subset_cols = [target_col] + cols_to_use
        data_subset = df[subset_cols].copy()
        
        # Check if data is all NaN (KNNImputer will fail)
        if data_subset.isna().all().all():
            logger.error(f"All values in {subset_cols} are NaN. Cannot perform KNN imputation.")
            raise ValueError("Input data for KNN imputation is entirely NaN.")
        
        imputed_array = imputer.fit_transform(data_subset)
        
        # Update the target column
        df[target_col] = imputed_array[:, 0]
        logger.info(f"Imputed {data_subset[target_col].isna().sum()} missing values in {target_col} using KNN.")
        
    except Exception as e:
        logger.error(f"KNN Imputation failed for {target_col}: {e}")
        # Fallback to mean if KNN fails
        mean_val = df[target_col].mean()
        if pd.isna(mean_val):
            logger.critical(f"Mean imputation fallback also failed (all NaN).")
            raise
        df[target_col] = df[target_col].fillna(mean_val)
        logger.warning(f"Fell back to mean imputation for {target_col}.")
        
    return df

def handle_missing_values(df: pd.DataFrame, method: str = 'drop', target_col: Optional[str] = None, cols_to_use: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Handles missing values based on the specified method.
    
    Args:
        df: Input DataFrame
        method: 'drop', 'mean', or 'impute'
        target_col: Required if method is 'impute'
        cols_to_use: Required if method is 'impute'
        
    Returns:
        Cleaned DataFrame
    """
    if method == 'drop':
        clean_df = df.dropna()
        if len(clean_df) == 0:
            logger.warning("Dropping NaNs resulted in an empty DataFrame.")
        return clean_df
    elif method == 'mean':
        return df.fillna(df.mean(numeric_only=True))
    elif method == 'impute':
        if target_col is None or cols_to_use is None:
            raise ValueError("target_col and cols_to_use must be provided for 'impute' method.")
        return impute_missing_nearest_neighbor(df, target_col, cols_to_use)
    else:
        raise ValueError(f"Unknown method: {method}. Use 'drop', 'mean', or 'impute'.")

def validate_and_clean_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper for coordinate validation.
    """
    return validate_coordinates(df)

def check_data_quality(df: pd.DataFrame) -> dict:
    """
    Performs a basic data quality check and returns a summary.
    
    Returns:
        Dictionary with quality metrics
    """
    return {
        "total_rows": len(df),
        "null_count": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": list(df.columns)
    }