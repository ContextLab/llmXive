import os
import sys
import json
import math
import random
import gc
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple

try:
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError as e:
    print(f"CRITICAL: Missing dependencies for data processing. Run: pip install pandas pyarrow")
    sys.exit(1)

from utils.data_utils import compute_checksum, update_checksums

# Configuration paths
CONFIG_PATH = "code/config.yaml"
RAW_DATA_PATH = "data/raw/synthetic_episodes.parquet"
PROCESSED_DIR = "data/processed"
TRAIN_PATH = os.path.join(PROCESSED_DIR, "train.parquet")
TEST_PATH = os.path.join(PROCESSED_DIR, "test.parquet")
CHECKSUMS_PATH = "data/checksums.json"

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_raw_data() -> pd.DataFrame:
    """Load the raw synthetic episodes dataset."""
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Raw data file not found at {RAW_DATA_PATH}. Run generate_data.py first.")
    
    print(f"Loading raw data from {RAW_DATA_PATH}...")
    df = pq.read_table(RAW_DATA_PATH).to_pandas()
    print(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def get_unique_geometries(df: pd.DataFrame) -> Set[str]:
    """Extract unique geometry IDs from the dataset."""
    if 'geometry_id' not in df.columns:
        raise ValueError("Dataset must contain 'geometry_id' column for geometry-disjoint split.")
    
    unique_ids = set(df['geometry_id'].unique())
    print(f"Found {len(unique_ids)} unique geometry IDs")
    return unique_ids

def split_geometry_disjoint(
    df: pd.DataFrame, 
    train_ratio: float = 0.8, 
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into train/test sets based on unique geometry IDs.
    Ensures that no geometry ID appears in both train and test sets.
    
    Args:
        df: The input dataframe with 'geometry_id' column
        train_ratio: Proportion of unique geometries to use for training
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (train_df, test_df)
    """
    unique_ids = get_unique_geometries(df)
    
    # Shuffle and split the unique IDs
    random.seed(seed)
    id_list = list(unique_ids)
    random.shuffle(id_list)
    
    split_idx = int(len(id_list) * train_ratio)
    train_ids = set(id_list[:split_idx])
    test_ids = set(id_list[split_idx:])
    
    print(f"Train geometries: {len(train_ids)}, Test geometries: {len(test_ids)}")
    
    # Filter dataframe based on geometry IDs
    train_df = df[df['geometry_id'].isin(train_ids)].reset_index(drop=True)
    test_df = df[df['geometry_id'].isin(test_ids)].reset_index(drop=True)
    
    print(f"Train rows: {len(train_df)}, Test rows: {len(test_df)}")
    
    # Validate disjointness
    train_geom_set = set(train_df['geometry_id'].unique())
    test_geom_set = set(test_df['geometry_id'].unique())
    intersection = train_geom_set & test_geom_set
    
    if intersection:
        raise ValueError(f"Geometry-disjoint split failed! Shared geometries: {intersection}")
    
    return train_df, test_df

def validate_splits(train_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """
    Validate the splits meet requirements:
    1. No shared geometry IDs
    2. Total rows >= 5000
    3. Test rows >= 1000
    """
    train_geoms = set(train_df['geometry_id'].unique())
    test_geoms = set(test_df['geometry_id'].unique())
    
    # Check disjointness
    if train_geoms & test_geoms:
        print("FAIL: Train and test sets share geometry IDs!")
        return False
    
    total_rows = len(train_df) + len(test_df)
    test_rows = len(test_df)
    
    print(f"Validation: Total rows={total_rows}, Test rows={test_rows}")
    
    if total_rows < 5000:
        print(f"FAIL: Total rows ({total_rows}) < 5000")
        return False
    
    if test_rows < 1000:
        print(f"FAIL: Test rows ({test_rows}) < 1000")
        return False
    
    print("Validation PASSED")
    return True

def save_parquet(df: pd.DataFrame, path: str) -> None:
    """Save dataframe to parquet file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    table = pa.Table.from_pandas(df)
    pq.write_table(table, path)
    print(f"Saved {len(df)} rows to {path}")

def update_checksums_registry(file_path: str) -> None:
    """Update the checksums.json registry with the new file's checksum."""
    checksum = compute_checksum(file_path)
    update_checksums(file_path, checksum, CHECKSUMS_PATH)
    print(f"Updated checksum for {file_path}")

def main():
    """Main entry point for geometry-disjoint split."""
    print("=== Starting Geometry-Disjoint Split (T016c) ===")
    
    # Load raw data
    df = load_raw_data()
    
    # Load config for split ratio if available
    try:
        config = load_config()
        train_ratio = config.get('split', {}).get('train_ratio', 0.8)
        seed = config.get('split', {}).get('seed', 42)
    except Exception as e:
        print(f"Warning: Could not load config, using defaults: train_ratio=0.8, seed=42")
        train_ratio = 0.8
        seed = 42
    
    # Perform split
    train_df, test_df = split_geometry_disjoint(df, train_ratio=train_ratio, seed=seed)
    
    # Validate splits
    if not validate_splits(train_df, test_df):
        print("ERROR: Split validation failed. Aborting.")
        sys.exit(1)
    
    # Save processed data
    save_parquet(train_df, TRAIN_PATH)
    save_parquet(test_df, TEST_PATH)
    
    # Update checksums
    update_checksums_registry(TRAIN_PATH)
    update_checksums_registry(TEST_PATH)
    
    print("=== Geometry-Disjoint Split Complete ===")
    print(f"Train: {TRAIN_PATH} ({len(train_df)} rows)")
    print(f"Test: {TEST_PATH} ({len(test_df)} rows)")

if __name__ == "__main__":
    main()
