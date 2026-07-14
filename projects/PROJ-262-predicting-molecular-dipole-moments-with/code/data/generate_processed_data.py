from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

# Project root relative to script location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Import project modules
from data.download_qm9 import download_qm9
from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features


def ensure_output_dir() -> Path:
    """Ensure the processed data directory exists."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_PROCESSED_DIR


def load_molecule_subset() -> pd.DataFrame:
    """
    Load the molecule subset.
    This function orchestrates the download and subset creation if the file doesn't exist.
    It expects the raw data to be in data/raw/ or downloads it if missing.
    """
    subset_path = DATA_RAW_DIR / "qm9_subset_10k.csv"

    if not subset_path.exists():
        print(f"Subset file {subset_path} not found. Downloading and creating subset...")
        # Download QM9
        raw_path = download_qm9()
        
        if not raw_path.exists():
            raise FileNotFoundError(f"QM9 download failed. Expected file at {raw_path}")
        
        # Create subset
        subset_df = create_reproducible_subset(raw_path, n_samples=10000, seed=42)
        subset_df.to_csv(subset_path, index=False)
        print(f"Created subset at {subset_path}")
    else:
        print(f"Loading existing subset from {subset_path}")
        subset_df = pd.read_csv(subset_path)

    return subset_df


def extract_3d_features_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper to extract 3D features from the molecule subset.
    """
    print("Extracting 3D features...")
    features_3d = extract_3d_features(df)
    return features_3d


def extract_2d_features_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper to extract 2D features from the molecule subset.
    """
    print("Extracting 2D features...")
    features_2d = extract_2d_features(df)
    return features_2d


def generate_processed_data():
    """
    Main pipeline to generate all processed data files:
    - data/processed/molecules_10k.parquet
    - data/processed/features_3d.parquet
    - data/processed/features_2d.parquet
    """
    output_dir = ensure_output_dir()

    # 1. Load the molecule subset (handles download/subset creation if needed)
    molecules_df = load_molecule_subset()

    # 2. Extract 3D features
    features_3d_df = extract_3d_features_wrapper(molecules_df)
    path_3d = output_dir / "features_3d.parquet"
    features_3d_df.to_parquet(path_3d, index=False)
    print(f"Saved 3D features to {path_3d}")

    # 3. Extract 2D features
    features_2d_df = extract_2d_features_wrapper(molecules_df)
    path_2d = output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(path_2d, index=False)
    print(f"Saved 2D features to {path_2d}")

    # 4. Save the processed molecule data (cleaned subset)
    path_molecules = output_dir / "molecules_10k.parquet"
    molecules_df.to_parquet(path_molecules, index=False)
    print(f"Saved molecule subset to {path_molecules}")

    return {
        "molecules": path_molecules,
        "features_3d": path_3d,
        "features_2d": path_2d
    }


def parse_args():
    parser = argparse.ArgumentParser(description="Generate processed data files.")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        results = generate_processed_data()
        print("Data generation completed successfully.")
        for key, path in results.items():
            print(f"  {key}: {path}")
    except Exception as e:
        print(f"Error during data generation: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    main()