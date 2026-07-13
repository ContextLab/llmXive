"""
Process raw synthetic data: split into train/test based on geometry IDs.
This ensures the test set contains only novel geometries.
"""
import os
import sys
import json
import math
import random
from pathlib import Path
from typing import List, Dict, Set, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

# Import project modules
sys.path.insert(0, str(Path(__file__).parent))
from utils.data_utils import update_checksums

# Configuration
RAW_DATA_PATH = Path(__file__).parent.parent / "data" / "raw" / "synthetic_episodes.parquet"
TRAIN_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "train.parquet"
TEST_OUTPUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "test.parquet"
CHECKSUMS_PATH = Path(__file__).parent.parent / "data" / "checksums.json"

def load_raw_data(raw_path: Path) -> pd.DataFrame:
    """Load raw synthetic episodes from parquet file."""
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data not found at {raw_path}")
    
    df = pd.read_parquet(raw_path)
    
    # Validate required columns
    required_cols = ["geometry_id", "translation_trajectory", "stability_label"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return df

def get_unique_geometries(df: pd.DataFrame) -> Set[int]:
    """Extract unique geometry IDs from the dataset."""
    return set(df["geometry_id"].unique())

def split_geometry_disjoint(df: pd.DataFrame, test_ratio: float = 0.2, 
                            seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into train/test sets such that test set contains
    ONLY geometries not present in the training set.
    """
    random.seed(seed)
    
    # Get unique geometry IDs
    unique_geoms = df["geometry_id"].unique()
    
    # Shuffle and split geometry IDs
    shuffled_geoms = list(unique_geoms)
    random.shuffle(shuffled_geoms)
    
    # Calculate split point
    n_test_geoms = max(1, int(len(shuffled_geoms) * test_ratio))
    test_geoms = set(shuffled_geoms[:n_test_geoms])
    train_geoms = set(shuffled_geoms[n_test_geoms:])
    
    # Split data based on geometry IDs
    train_df = df[df["geometry_id"].isin(train_geoms)].reset_index(drop=True)
    test_df = df[df["geometry_id"].isin(test_geoms)].reset_index(drop=True)
    
    return train_df, test_df

def validate_splits(train_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """Validate that train and test sets are geometry-disjoint and meet size requirements."""
    train_geoms = set(train_df["geometry_id"].unique())
    test_geoms = set(test_df["geometry_id"].unique())
    
    # Check disjointness
    overlap = train_geoms.intersection(test_geoms)
    if overlap:
        raise ValueError(f"Geometry overlap detected: {overlap}")
    
    # Check minimum sizes (T016d requirement)
    total_rows = len(train_df) + len(test_df)
    if total_rows < 5000:
        raise ValueError(f"Total rows ({total_rows}) is less than required 5000")
    
    if len(test_df) < 1000:
        raise ValueError(f"Test set rows ({len(test_df)}) is less than required 1000")
    
    print(f"Validation passed: Train={len(train_df)}, Test={len(test_df)}, Total={total_rows}")
    return True

def save_parquet(df: pd.DataFrame, output_path: Path):
    """Save dataframe to parquet file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Saved {len(df)} rows to {output_path}")

def update_checksums_registry(checksums_path: Path, new_files: List[Path]):
    """Update the checksums.json registry with new file hashes."""
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
    else:
        checksums = {}
    
    from utils.data_utils import compute_checksum
    
    for file_path in new_files:
        if file_path.exists():
            checksums[file_path.name] = compute_checksum(file_path)
    
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)

def main():
    print("Starting data processing (T016c)...")
    
    # Load raw data
    df = load_raw_data(RAW_DATA_PATH)
    print(f"Loaded {len(df)} rows from raw data")
    
    # Split geometry-disjoint
    train_df, test_df = split_geometry_disjoint(df, test_ratio=0.2)
    
    # Validate splits
    validate_splits(train_df, test_df)
    
    # Save processed files
    save_parquet(train_df, TRAIN_OUTPUT_PATH)
    save_parquet(test_df, TEST_OUTPUT_PATH)
    
    # Update checksums
    update_checksums_registry(CHECKSUMS_PATH, [TRAIN_OUTPUT_PATH, TEST_OUTPUT_PATH])
    
    print("Data processing completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
