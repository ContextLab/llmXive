"""
Utility module for spatial block cross-validation generation.

This module provides functions to assign spatial blocks to occurrence data
and generate spatially stratified cross-validation folds to reduce spatial
autocorrelation bias in model evaluation.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from config import DATA_DIR, RND_SEED
import logging

# Import logger from logging_config if available, otherwise use default
try:
    from logging_config import get_logger
    logger = get_logger("spatial_blocks")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def create_spatial_blocks(
    df: pd.DataFrame,
    lon_col: str = "decimalLongitude",
    lat_col: str = "decimalLatitude",
    n_blocks_lon: int = 5,
    n_blocks_lat: int = 5,
    seed: int = RND_SEED
) -> pd.DataFrame:
    """
    Assign spatial blocks to a dataframe based on longitude and latitude.
    
    This function divides the spatial extent of the data into a grid of
    rectangular blocks. Each record is assigned a block ID based on its
    coordinates. This is used for spatial cross-validation to ensure
    training and validation sets are spatially distinct.
    
    Args:
        df: Input dataframe with coordinates.
        lon_col: Column name for longitude.
        lat_col: Column name for latitude.
        n_blocks_lon: Number of blocks along longitude axis.
        n_blocks_lat: Number of blocks along latitude axis.
        seed: Random seed for reproducibility (not used for grid assignment, 
              but for shuffling if needed).
    
    Returns:
        DataFrame with an added 'spatial_block' column containing integer IDs.
        
    Raises:
        ValueError: If coordinate columns are missing or contain invalid values.
    """
    # Validate inputs
    if lon_col not in df.columns:
        raise ValueError(f"Column '{lon_col}' not found in dataframe.")
    if lat_col not in df.columns:
        raise ValueError(f"Column '{lat_col}' not found in dataframe.")
    
    # Check for valid numeric coordinates
    if not np.issubdtype(df[lon_col].dtype, np.number) or not np.issubdtype(df[lat_col].dtype, np.number):
        logger.warning(f"Coordinates may not be numeric. Converting to float.")
        df_copy = df.copy()
        df_copy[lon_col] = pd.to_numeric(df_copy[lon_col], errors='coerce')
        df_copy[lat_col] = pd.to_numeric(df_copy[lat_col], errors='coerce')
    else:
        df_copy = df.copy()
    
    # Remove rows with invalid coordinates
    valid_mask = df_copy[lon_col].notna() & df_copy[lat_col].notna()
    if not valid_mask.all():
        invalid_count = (~valid_mask).sum()
        logger.warning(f"Dropped {invalid_count} rows with invalid coordinates.")
        df_copy = df_copy[valid_mask]
    
    if len(df_copy) == 0:
        raise ValueError("No valid coordinates remaining after cleaning.")
    
    # Determine bounds
    min_lon, max_lon = df_copy[lon_col].min(), df_copy[lon_col].max()
    min_lat, max_lat = df_copy[lat_col].min(), df_copy[lat_col].max()
    
    # Handle edge case where all points are the same
    if min_lon == max_lon:
        logger.warning("All longitudes are identical. Using a single column of blocks.")
        lon_edges = np.array([min_lon - 0.001, max_lon + 0.001])
    else:
        lon_edges = np.linspace(min_lon, max_lon, n_blocks_lon + 1)
        
    if min_lat == max_lat:
        logger.warning("All latitudes are identical. Using a single row of blocks.")
        lat_edges = np.array([min_lat - 0.001, max_lat + 0.001])
    else:
        lat_edges = np.linspace(min_lat, max_lat, n_blocks_lat + 1)
    
    # Assign blocks
    # include_lowest=True ensures the minimum value is included in the first bin
    lon_bins = pd.cut(df_copy[lon_col], bins=lon_edges, labels=False, include_lowest=True)
    lat_bins = pd.cut(df_copy[lat_col], bins=lat_edges, labels=False, include_lowest=True)
    
    # Combine into a single block ID
    # Formula: block_id = lat_index * n_lon_blocks + lon_index
    # This creates a unique ID for each (lat, lon) pair in the grid
    df_copy['spatial_block'] = lat_bins * n_blocks_lon + lon_bins
    
    logger.info(f"Created {len(df_copy['spatial_block'].unique())} spatial blocks "
               f"using grid {n_blocks_lat}x{n_blocks_lon}.")
    
    return df_copy

def generate_spatial_folds(
    df: pd.DataFrame,
    n_folds: int = 5,
    seed: int = RND_SEED
) -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Generate spatial cross-validation folds.
    
    This function creates k-fold cross-validation splits where each fold
    consists of entire spatial blocks rather than individual points.
    This ensures spatial independence between training and validation sets.
    
    Args:
        df: Dataframe with 'spatial_block' column assigned (via create_spatial_blocks).
        n_folds: Number of folds to create.
        seed: Random seed for reproducibility.
    
    Returns:
        List of (train_df, val_df) tuples for each fold.
        
    Raises:
        ValueError: If 'spatial_block' column is missing or if not enough blocks exist.
    """
    if 'spatial_block' not in df.columns:
        raise ValueError("DataFrame must contain 'spatial_block' column. "
                       "Run create_spatial_blocks() first.")
    
    blocks = df['spatial_block'].unique()
    if len(blocks) < n_folds:
        raise ValueError(f"Cannot create {n_folds} folds with only {len(blocks)} blocks. "
                       "Reduce n_folds or increase spatial resolution.")
    
    # Set random seed for reproducibility
    rng = np.random.default_rng(seed)
    shuffled_blocks = rng.permutation(blocks)
    
    # Split blocks into folds
    fold_size = len(shuffled_blocks) // n_folds
    folds = []
    
    for i in range(n_folds):
        # Define validation block indices for this fold
        start_idx = i * fold_size
        end_idx = start_idx + fold_size if i < n_folds - 1 else len(shuffled_blocks)
        
        val_blocks = shuffled_blocks[start_idx:end_idx]
        train_blocks = np.setdiff1d(shuffled_blocks, val_blocks)
        
        val_df = df[df['spatial_block'].isin(val_blocks)].copy()
        train_df = df[df['spatial_block'].isin(train_blocks)].copy()
        
        folds.append((train_df, val_df))
    
    logger.info(f"Generated {n_folds} spatial folds with {len(shuffled_blocks)} total blocks.")
    return folds

def get_spatial_block_summary(df: pd.DataFrame) -> Dict:
    """
    Get a summary of spatial blocks in the dataframe.
    
    Provides statistics about the distribution of records across spatial blocks,
    which can be used to assess data quality and balance for cross-validation.
    
    Args:
        df: Dataframe with 'spatial_block' column.
    
    Returns:
        Dictionary with block statistics:
            - total_blocks: Number of unique blocks
            - records_per_block: Dict mapping block_id to record count
            - min_records: Minimum records in any block
            - max_records: Maximum records in any block
            - mean_records: Mean records per block
            - empty_blocks: Number of blocks with zero records (if applicable)
            
    Raises:
        ValueError: If 'spatial_block' column is missing.
    """
    if 'spatial_block' not in df.columns:
        raise ValueError("DataFrame must contain 'spatial_block' column.")
    
    block_counts = df['spatial_block'].value_counts().to_dict()
    total_blocks = len(block_counts)
    
    if total_blocks == 0:
        return {
            "total_blocks": 0,
            "records_per_block": {},
            "min_records": 0,
            "max_records": 0,
            "mean_records": 0.0
        }
    
    counts = list(block_counts.values())
    return {
        "total_blocks": total_blocks,
        "records_per_block": block_counts,
        "min_records": min(counts),
        "max_records": max(counts),
        "mean_records": sum(counts) / len(counts)
    }