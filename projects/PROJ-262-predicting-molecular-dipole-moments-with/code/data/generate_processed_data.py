from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Import existing functions from the API surface
from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from data.handle_missing_coords import handle_missing_coordinates
from utils.reproducibility import set_seed


def ensure_output_dir(output_dir: Path) -> None:
    """Create output directory if it does not exist."""
    output_dir.mkdir(parents=True, exist_ok=True)


def load_molecule_subset(raw_data_path: Path) -> pd.DataFrame:
    """
    Load the raw molecule data and create a reproducible subset.
    Expects raw data to be in 'data/raw/qm9_processed.csv' (or similar).
    """
    if not raw_data_path.exists():
        # Fallback: try to find the file in the raw directory if the specific path isn't exact
        raw_dir = raw_data_path.parent
        files = list(raw_dir.glob("*.csv"))
        if not files:
            raise FileNotFoundError(f"No CSV files found in {raw_dir} to load molecule subset.")
        # Assuming the first found CSV is the processed raw data
        raw_data_path = files[0]
        
    df = pd.read_csv(raw_data_path)
    # Ensure we have a 10k subset as per T016
    subset_df = create_reproducible_subset(df, subset_size=10000, seed=42)
    return subset_df


def extract_3d_features(df: pd.DataFrame, output_path: Path) -> None:
    """
    Extract 3D features and save to parquet.
    Uses the existing extract_3d_features function from preprocess_3d.
    """
    print(f"Extracting 3D features for {len(df)} molecules...")
    # The existing function returns a DataFrame
    features_3d_df = extract_3d_features(df)
    features_3d_df.to_parquet(output_path, index=False)
    print(f"Saved 3D features to {output_path}")


def extract_2d_features(df: pd.DataFrame, output_path: Path) -> None:
    """
    Extract 2D features and save to parquet.
    Uses the existing extract_2d_features function from extract_2d_descriptors.
    """
    print(f"Extracting 2D features for {len(df)} molecules...")
    # The existing function returns a DataFrame
    features_2d_df = extract_2d_features(df)
    features_2d_df.to_parquet(output_path, index=False)
    print(f"Saved 2D features to {output_path}")


def generate_processed_data(
    raw_data_path: Path,
    output_dir: Path,
    molecules_file: str = "molecules_10k.parquet",
    features_3d_file: str = "features_3d.parquet",
    features_2d_file: str = "features_2d.parquet"
) -> None:
    """
    Main pipeline to generate processed data files.
    1. Load raw data and create 10k subset.
    2. Handle missing coordinates (generates exclusion report).
    3. Extract 3D features.
    4. Extract 2D features.
    5. Save the cleaned subset and feature files.
    """
    set_seed(42)
    
    # 1. Load and subset
    print(f"Loading raw data from {raw_data_path}...")
    df = load_molecule_subset(raw_data_path)
    print(f"Created subset with {len(df)} molecules.")

    # 2. Handle missing coordinates
    # This updates df in place (removes excluded) and writes the report
    print("Checking for missing coordinates...")
    df = handle_missing_coordinates(df)
    print(f"Remaining molecules after filtering: {len(df)}")

    # Ensure output directory exists
    ensure_output_dir(output_dir)

    # 3. Save the cleaned molecule subset
    molecules_path = output_dir / molecules_file
    df.to_parquet(molecules_path, index=False)
    print(f"Saved molecules subset to {molecules_path}")

    # 4. Extract and save 3D features
    features_3d_path = output_dir / features_3d_file
    extract_3d_features(df, features_3d_path)

    # 5. Extract and save 2D features
    features_2d_path = output_dir / features_2d_file
    extract_2d_features(df, features_2d_path)

    print("Processed data generation complete.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate processed data files from raw QM9 data.")
    parser.add_argument(
        "--raw-data",
        type=Path,
        default=Path("data/raw/qm9_processed.csv"),
        help="Path to the raw processed QM9 CSV file."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory to save processed parquet files."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generate_processed_data(
        raw_data_path=args.raw_data,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()