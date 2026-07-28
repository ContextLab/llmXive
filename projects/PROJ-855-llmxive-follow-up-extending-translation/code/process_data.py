"""
Data processing module for splitting and validating datasets.
Implements geometry-disjoint train/test splits.
"""
import os
import sys
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import pandas as pd
import pyarrow.parquet as pq
import hashlib

# Import shared utilities from the project structure
# Note: The prompt indicates 'utils' is in code/, so we adjust import path
sys.path.insert(0, str(Path(__file__).parent))
from utils.data_utils import compute_checksum, update_checksums

def load_raw_data(raw_path: str) -> pd.DataFrame:
    """
    Load the raw synthetic episodes dataset.
    
    Args:
        raw_path: Path to the raw parquet file.
        
    Returns:
        DataFrame containing the raw episodes.
        
    Raises:
        FileNotFoundError: If the raw file does not exist.
        ValueError: If the file is not a valid parquet.
    """
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw data file not found: {raw_path}")
    
    try:
        df = pd.read_parquet(raw_path)
        # Ensure required columns exist
        required_cols = ['geometry_id', 'stability_label']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Raw data missing required columns: {missing}")
        return df
    except Exception as e:
        raise ValueError(f"Failed to load parquet file {raw_path}: {e}")

def get_unique_geometries(df: pd.DataFrame) -> Set[str]:
    """
    Extract unique geometry IDs from the dataset.
    
    Args:
        df: DataFrame with 'geometry_id' column.
        
    Returns:
        Set of unique geometry ID strings.
    """
    return set(df['geometry_id'].unique())

def split_geometry_disjoint(
    df: pd.DataFrame, 
    train_ratio: float = 0.8, 
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the dataset into train and test sets such that no geometry ID
    appears in both sets.
    
    This ensures the model is tested on entirely novel object geometries.
    
    Args:
        df: The full dataset DataFrame.
        train_ratio: Fraction of geometries to include in training (default 0.8).
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, test_df).
        
    Raises:
        ValueError: If there are not enough unique geometries to split.
    """
    if train_ratio <= 0 or train_ratio >= 1:
        raise ValueError("train_ratio must be between 0 and 1 (exclusive)")
    
    unique_geoms = get_unique_geometries(df)
    if len(unique_geoms) < 2:
        raise ValueError(f"Need at least 2 unique geometries to split, found {len(unique_geoms)}")
    
    random.seed(seed)
    geoms_list = list(unique_geoms)
    random.shuffle(geoms_list)
    
    split_idx = int(len(geoms_list) * train_ratio)
    train_geoms = set(geoms_list[:split_idx])
    test_geoms = set(geoms_list[split_idx:])
    
    # Filter DataFrame
    train_df = df[df['geometry_id'].isin(train_geoms)].copy()
    test_df = df[df['geometry_id'].isin(test_geoms)].copy()
    
    # Verify disjointness
    train_set = set(train_df['geometry_id'].unique())
    test_set = set(test_df['geometry_id'].unique())
    intersection = train_set.intersection(test_set)
    if intersection:
        raise RuntimeError(f"Geometry split failed: shared geometries {intersection}")
    
    return train_df, test_df

def validate_splits(train_df: pd.DataFrame, test_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the resulting splits for statistical power and disjointness.
    
    Args:
        train_df: Training DataFrame.
        test_df: Test DataFrame.
        
    Returns:
        Dictionary with validation stats.
        
    Raises:
        AssertionError: If validation constraints (e.g., min rows) are violated.
    """
    total_rows = len(train_df) + len(test_df)
    test_rows = len(test_df)
    
    # Assert total rows >= 5000 (from T016d requirement)
    assert total_rows >= 5000, f"Total rows {total_rows} < 5000"
    
    # Assert test rows >= 1000 (from T016d requirement)
    assert test_rows >= 1000, f"Test rows {test_rows} < 1000"
    
    # Assert disjointness
    train_geoms = set(train_df['geometry_id'].unique())
    test_geoms = set(test_df['geometry_id'].unique())
    assert len(train_geoms.intersection(test_geoms)) == 0, "Splits are not disjoint"
    
    return {
        "total_rows": total_rows,
        "train_rows": len(train_df),
        "test_rows": test_rows,
        "train_unique_geoms": len(train_geoms),
        "test_unique_geoms": len(test_geoms),
        "valid": True
    }

def save_parquet(df: pd.DataFrame, path: str) -> None:
    """
    Save DataFrame to a parquet file.
    
    Args:
        df: DataFrame to save.
        path: Output file path.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_parquet(path, index=False)

def update_checksums_registry(file_path: str, registry_path: str) -> None:
    """
    Update the project's checksum registry with the new file.
    
    Args:
        file_path: Path to the file to checksum.
        registry_path: Path to the checksums.json file.
    """
    checksum = compute_checksum(file_path)
    update_checksums(registry_path, file_path, checksum)

def main():
    """
    Main entry point for the data processing script.
    Loads raw data, performs geometry-disjoint split, validates, and saves.
    """
    # Paths
    project_root = Path(__file__).parent.parent
    raw_path = project_root / "data" / "raw" / "synthetic_episodes.parquet"
    processed_dir = project_root / "data" / "processed"
    train_path = processed_dir / "train.parquet"
    test_path = processed_dir / "test.parquet"
    checksums_path = project_root / "data" / "checksums.json"
    
    print(f"Loading raw data from: {raw_path}")
    df = load_raw_data(str(raw_path))
    print(f"Loaded {len(df)} rows.")
    
    print("Performing geometry-disjoint split (80/20)...")
    train_df, test_df = split_geometry_disjoint(df, train_ratio=0.8, seed=42)
    
    print("Validating splits...")
    stats = validate_splits(train_df, test_df)
    print(f"Validation passed: {stats}")
    
    print(f"Saving train set to: {train_path} ({len(train_df)} rows)")
    save_parquet(train_df, str(train_path))
    
    print(f"Saving test set to: {test_path} ({len(test_df)} rows)")
    save_parquet(test_df, str(test_path))
    
    # Update checksums
    print("Updating checksums...")
    update_checksums_registry(str(train_path), str(checksums_path))
    update_checksums_registry(str(test_path), str(checksums_path))
    
    print("Processing complete.")

if __name__ == "__main__":
    main()