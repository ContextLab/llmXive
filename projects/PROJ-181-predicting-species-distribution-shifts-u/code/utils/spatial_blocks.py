"""
Spatial Block Cross-Validation Utilities.
Generates spatial blocks for training/testing splits to reduce spatial autocorrelation.
"""
import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from config import DATA_DIR, RND_SEED

def create_spatial_blocks(df: pd.DataFrame, n_blocks: int = 5, lat_col: str = 'decimalLatitude', lon_col: str = 'decimalLongitude') -> pd.DataFrame:
    """
    Assigns spatial block IDs to the dataframe based on latitude and longitude.
    Uses a simple grid-based approach.
    
    Args:
        df: Input DataFrame
        n_blocks: Number of blocks to create (k for k-fold)
        lat_col: Latitude column name
        lon_col: Longitude column name
        
    Returns:
        DataFrame with a new 'spatial_block' column
    """
    df = df.copy()
    
    # Ensure coordinates are valid
    if lat_col not in df.columns or lon_col not in df.columns:
        raise ValueError(f"Columns {lat_col} or {lon_col} not found.")
    
    # Determine grid dimensions
    # We want roughly n_blocks blocks. We can split lat and lon.
    # A simple heuristic: sqrt(n_blocks) x sqrt(n_blocks) grid
    n_lat = int(np.ceil(np.sqrt(n_blocks)))
    n_lon = int(np.ceil(n_blocks / n_lat))
    
    lat_min, lat_max = df[lat_col].min(), df[lat_col].max()
    lon_min, lon_max = df[lon_col].min(), df[lon_col].max()
    
    lat_bins = np.linspace(lat_min, lat_max, n_lat + 1)
    lon_bins = np.linspace(lon_min, lon_max, n_lon + 1)
    
    # Assign block IDs
    # Using pd.cut to bin and then mapping to a unique ID
    lat_codes = pd.cut(df[lat_col], bins=lat_bins, labels=False, include_lowest=True)
    lon_codes = pd.cut(df[lon_col], bins=lon_bins, labels=False, include_lowest=True)
    
    # Combine to get unique block ID (0 to n_blocks-1)
    # Flatten the 2D grid indices
    df['spatial_block'] = lat_codes * n_lon + lon_codes
    
    # Re-index blocks to ensure they are 0..k-1 if some are empty
    unique_blocks = df['spatial_block'].dropna().unique()
    mapping = {old: new for new, old in enumerate(sorted(unique_blocks))}
    df['spatial_block'] = df['spatial_block'].map(mapping)
    
    return df

def generate_spatial_folds(df: pd.DataFrame, n_splits: int = 5, lat_col: str = 'decimalLatitude', lon_col: str = 'decimalLongitude') -> List[Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Generates spatial block cross-validation folds.
    
    Args:
        df: Input DataFrame
        n_splits: Number of folds
        lat_col: Latitude column
        lon_col: Longitude column
        
    Returns:
        List of (train_df, test_df) tuples
    """
    df_with_blocks = create_spatial_blocks(df, n_blocks=n_splits, lat_col=lat_col, lon_col=lon_col)
    
    folds = []
    unique_blocks = df_with_blocks['spatial_block'].unique()
    
    for i in range(n_splits):
        # Test set is one block
        test_mask = df_with_blocks['spatial_block'] == i
        train_mask = ~test_mask
        
        test_df = df_with_blocks[train_mask].drop(columns=['spatial_block'])
        train_df = df_with_blocks[train_mask].drop(columns=['spatial_block'])
        
        folds.append((train_df, test_df))
        
    return folds

def get_spatial_block_summary(df: pd.DataFrame, block_col: str = 'spatial_block') -> Dict:
    """
    Returns a summary of records per spatial block.
    """
    if block_col not in df.columns:
        return {}
    return df[block_col].value_counts().to_dict()
