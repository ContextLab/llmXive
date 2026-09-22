"""
Utility module for coordinate validation, missing value imputation, and error handling.

This module provides functions to:
- Validate geographic coordinates within standard bounds.
- Impute missing climate/environmental values using nearest neighbor spatial interpolation.
- Handle missing data via configurable strategies.
- Perform basic data quality checks.
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Union, Dict
from pathlib import Path
import logging
from config import DATA_DIR, RND_SEED

logger = logging.getLogger(__name__)

def validate_coordinates(
    df: pd.DataFrame,
    lon_col: str = "decimalLongitude",
    lat_col: str = "decimalLatitude",
    lon_min: float = -180.0,
    lon_max: float = 180.0,
    lat_min: float = -90.0,
    lat_max: float = 90.0
) -> pd.DataFrame:
    """
    Validate and filter coordinates to ensure they are within valid ranges.

    This function filters out records where longitude or latitude fall outside
    the specified bounds. It logs the number of valid vs total records.

    Args:
        df: Input dataframe containing coordinate columns.
        lon_col: Column name for longitude.
        lat_col: Column name for latitude.
        lon_min, lon_max: Valid longitude range (default: -180 to 180).
        lat_min, lat_max: Valid latitude range (default: -90 to 90).

    Returns:
        Filtered dataframe with only valid coordinates.
    """
    # Ensure columns exist
    if lon_col not in df.columns or lat_col not in df.columns:
        raise ValueError(f"Columns '{lon_col}' or '{lat_col}' not found in dataframe.")

    valid_mask = (
        (df[lon_col].notna()) & (df[lat_col].notna()) &
        (df[lon_col] >= lon_min) & (df[lon_col] <= lon_max) &
        (df[lat_col] >= lat_min) & (df[lat_col] <= lat_max)
    )
    
    valid_count = valid_mask.sum()
    total_count = len(df)
    invalid_count = total_count - valid_count

    logger.info(f"Coordinate validation: {valid_count}/{total_count} records valid. ({invalid_count} invalid)")

    if invalid_count > 0:
        # Log details of first few invalid records for debugging
        invalid_sample = df[~valid_mask].head()
        logger.debug(f"Sample invalid records:\n{invalid_sample[[lon_col, lat_col]]}")

    return df[valid_mask].copy()

def impute_missing_nearest_neighbor(
    df: pd.DataFrame,
    value_cols: List[str],
    lon_col: str = "decimalLongitude",
    lat_col: str = "decimalLatitude",
    max_distance: float = 2.0  # degrees (approx 220km at equator)
) -> pd.DataFrame:
    """
    Impute missing values in specified columns using nearest neighbor interpolation
    based on spatial proximity.

    This function identifies rows with missing values in `value_cols` and attempts
    to fill them using the value from the nearest non-missing neighbor within `max_distance`.
    Distance is calculated as Euclidean distance in degrees.

    Args:
        df: Input dataframe.
        value_cols: List of column names to impute (e.g., climate variables).
        lon_col: Column name for longitude.
        lat_col: Column name for latitude.
        max_distance: Maximum distance in degrees to consider a neighbor.

    Returns:
        Dataframe with imputed values. Missing values that cannot be imputed remain NaN.
    """
    df_copy = df.copy()
    
    # Check for required columns
    for col in [lon_col, lat_col] + value_cols:
        if col not in df_copy.columns:
            raise ValueError(f"Required column '{col}' not found in dataframe.")

    # Identify rows with missing values in any of the target columns
    missing_mask = df_copy[value_cols].isna().any(axis=1)
    
    if not missing_mask.any():
        logger.info("No missing values found in specified columns to impute.")
        return df_copy

    logger.info(f"Attempting to impute {missing_mask.sum()} records using nearest neighbor.")

    # Separate missing and non-missing rows
    missing_indices = df_copy[missing_mask].index
    non_missing_mask = ~df_copy[value_cols].isna().any(axis=1)
    non_missing_df = df_copy[non_missing_mask]

    if len(non_missing_df) == 0:
        logger.warning("No non-missing records found to use as neighbors. Imputation skipped.")
        return df_copy

    # Pre-calculate coordinates for non-missing rows for efficiency
    non_missing_coords = non_missing_df[[lon_col, lat_col]].values
    non_missing_indices = non_missing_df.index

    imputed_count = 0
    failed_count = 0

    for idx in missing_indices:
        # Get coordinates of the missing point
        point_lon = df_copy.loc[idx, lon_col]
        point_lat = df_copy.loc[idx, lat_col]
        
        if pd.isna(point_lon) or pd.isna(point_lat):
            logger.warning(f"Skipping imputation for index {idx}: missing coordinates.")
            continue

        # Calculate distances to all non-missing points
        # Euclidean distance in degrees
        diffs = non_missing_coords - np.array([point_lon, point_lat])
        distances = np.sqrt(np.sum(diffs**2, axis=1))

        # Find the nearest neighbor
        min_dist_idx = np.argmin(distances)
        min_dist = distances[min_dist_idx]

        if min_dist <= max_distance:
            # Found a valid neighbor
            neighbor_idx = non_missing_indices[min_dist_idx]
            
            # Impute each missing column in this row
            for col in value_cols:
                if pd.isna(df_copy.loc[idx, col]):
                    df_copy.loc[idx, col] = df_copy.loc[neighbor_idx, col]
                    imputed_count += 1
        else:
            failed_count += 1
            logger.debug(f"Could not find neighbor for index {idx} within {max_distance} degrees (min dist: {min_dist:.4f}).")

    logger.info(f"Imputation complete: {imputed_count} values imputed, {failed_count} failed.")
    return df_copy

def handle_missing_values(
    df: pd.DataFrame,
    strategy: str = "nearest_neighbor",
    value_cols: Optional[List[str]] = None,
    **kwargs
) -> pd.DataFrame:
    """
    Handle missing values in the dataframe based on the specified strategy.

    Args:
        df: Input dataframe.
        strategy: Strategy to handle missing values. Supported:
            - 'nearest_neighbor': Spatial nearest neighbor imputation (requires lon/lat).
            - 'drop': Drop rows with any missing values in specified columns.
            - 'mean': Fill with column mean.
        value_cols: List of columns to apply the strategy to. If None, applies to all numeric columns.
        **kwargs: Additional arguments passed to the specific strategy function.

    Returns:
        Processed dataframe.

    Raises:
        ValueError: If an unknown strategy is provided.
    """
    if value_cols is None:
        # Default to all numeric columns that have missing values
        value_cols = df.select_dtypes(include=[np.number]).columns[df.select_dtypes(include=[np.number]).isna().any()].tolist()
    
    if not value_cols:
        logger.info("No numeric columns with missing values to process.")
        return df

    if strategy == "nearest_neighbor":
        # Ensure we have coordinate columns for spatial imputation
        lon_col = kwargs.pop('lon_col', "decimalLongitude")
        lat_col = kwargs.pop('lat_col', "decimalLatitude")
        max_dist = kwargs.pop('max_distance', 2.0)
        
        if lon_col not in df.columns or lat_col not in df.columns:
            raise ValueError(f"Spatial imputation requires '{lon_col}' and '{lat_col}' columns.")
        
        return impute_missing_nearest_neighbor(
            df, 
            value_cols, 
            lon_col=lon_col, 
            lat_col=lat_col, 
            max_distance=max_dist
        )
    
    elif strategy == "drop":
        count_before = len(df)
        df_result = df.dropna(subset=value_cols)
        count_after = len(df_result)
        logger.info(f"Dropped {count_before - count_after} rows due to missing values in {value_cols}.")
        return df_result

    elif strategy == "mean":
        df_result = df.copy()
        for col in value_cols:
            if col in df_result.columns:
                mean_val = df_result[col].mean()
                if pd.isna(mean_val):
                    logger.warning(f"Cannot compute mean for column '{col}' (all NaN or non-numeric).")
                else:
                    df_result[col] = df_result[col].fillna(mean_val)
        return df_result

    else:
        raise ValueError(f"Unknown strategy: {strategy}. Supported: 'nearest_neighbor', 'drop', 'mean'")

def validate_and_clean_coordinates(
    df: pd.DataFrame,
    lon_col: str = "decimalLongitude",
    lat_col: str = "decimalLatitude"
) -> pd.DataFrame:
    """
    Validate coordinates and clean them (e.g., remove 0,0 points which are often errors).

    Args:
        df: Input dataframe.
        lon_col: Column name for longitude.
        lat_col: Column name for latitude.

    Returns:
        Cleaned dataframe with valid coordinates and (0,0) points removed.
    """
    # First validate ranges
    df_valid = validate_coordinates(df, lon_col, lat_col)
    
    # Remove points at (0,0) which are common GBIF errors
    mask_zero = (df_valid[lon_col] == 0) & (df_valid[lat_col] == 0)
    if mask_zero.any():
        logger.warning(f"Removing {mask_zero.sum()} records with coordinates (0, 0).")
        df_clean = df_valid[~mask_zero]
    else:
        df_clean = df_valid

    return df_clean

def check_data_quality(
    df: pd.DataFrame,
    required_cols: List[str]
) -> Dict:
    """
    Perform a basic data quality check on the dataframe.

    Args:
        df: Input dataframe.
        required_cols: List of required column names to check for missing values.

    Returns:
        Dictionary with quality metrics including missing counts, duplicate coordinates, and total records.
    """
    # Check for missing values in required columns
    missing_counts = {}
    for col in required_cols:
        if col in df.columns:
            missing_counts[col] = int(df[col].isna().sum())
        else:
            missing_counts[col] = -1  # Indicate column missing

    # Check for duplicate coordinate pairs
    if 'decimalLongitude' in df.columns and 'decimalLatitude' in df.columns:
        duplicate_coords = int(df.duplicated(subset=['decimalLongitude', 'decimalLatitude']).sum())
    else:
        duplicate_coords = -1

    quality_report = {
        "missing_counts": missing_counts,
        "duplicate_coordinate_pairs": duplicate_coords,
        "total_records": len(df),
        "complete_records": int(df.dropna(subset=required_cols).shape[0])
    }

    logger.info(f"Data quality check: {quality_report['total_records']} records, {duplicate_coords} duplicate coords.")
    
    return quality_report