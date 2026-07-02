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
    Imputes missing values in target_col using the mean of the nearest neighbors
    based on cols_to_use (e.g., other climate variables).
    
    Note: For simplicity in this baseline context, we use a simple mean of available 
    values if nearest neighbor is too complex for a single column imputation without 
    a spatial index. A true NN implementation would require a KDTree on coordinates 
    or other features. Here we fallback to global mean if neighbors aren't defined 
    by the caller, or use a simple row-based neighbor if sorted.
    
    For the specific task of "nearest neighbor imputation" on climate variables, 
    usually implies spatial neighbors. Since we don't have the spatial index here,
    we will implement a simple mean imputation as a safe fallback or 
    a KNN imputer if sklearn is available and cols_to_use are features.
    
    Implementation: Using KNNImputer from sklearn if cols_to_use are provided, 
    otherwise mean imputation.
    """
    from sklearn.impute import KNNImputer
    
    if df[target_col].isna().sum() == 0:
        return df
    
    # Prepare data for imputation
    # If cols_to_use are provided, we use them to find neighbors
    if cols_to_use:
        imputer = KNNImputer(n_neighbors=5)
        # We only impute the target column, but need features for distance
        # We construct a matrix of [target, *features]
        data_to_impute = df[[target_col] + cols_to_use].copy()
        imputed = imputer.fit_transform(data_to_impute)
        df[target_col] = imputed[:, 0]
    else:
        # Fallback to mean imputation if no features provided
        df[target_col] = df[target_col].fillna(df[target_col].mean())
        
    return df

def handle_missing_values(df: pd.DataFrame, method: str = 'drop') -> pd.DataFrame:
    """
    Handles missing values based on the specified method.
    
    Args:
        df: Input DataFrame
        method: 'drop', 'mean', or 'impute'
        
    Returns:
        Cleaned DataFrame
    """
    if method == 'drop':
        return df.dropna()
    elif method == 'mean':
        return df.fillna(df.mean(numeric_only=True))
    elif method == 'impute':
        # Placeholder for more complex logic, currently just mean
        return df.fillna(df.mean(numeric_only=True))
    return df

def validate_and_clean_coordinates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper for coordinate validation.
    """
    return validate_coordinates(df)

def check_data_quality(df: pd.DataFrame) -> dict:
    """
    Performs a basic data quality check and returns a summary.
    """
    return {
        "total_rows": len(df),
        "null_count": df.isnull().sum().to_dict(),
        "duplicate_rows": df.duplicated().sum()
    }
