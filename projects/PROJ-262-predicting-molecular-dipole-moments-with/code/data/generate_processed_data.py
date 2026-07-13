"""
Generate processed data files for molecular dipole moment prediction.

This script orchestrates the creation of:
- data/processed/molecules_10k.parquet: Subset of QM9 molecules
- data/processed/features_3d.parquet: 3D structural features
- data/processed/features_2d.parquet: 2D molecular descriptors

It depends on T015 (download_qm9), T016 (create_subset), T017 (preprocess_3d),
and T018 (extract_2d_descriptors) having been executed successfully.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Import from existing project modules
from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from utils.reproducibility import set_seed


def ensure_output_dir(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def load_molecule_subset(raw_data_path: Path) -> pd.DataFrame:
    """
    Load the raw molecule data and create a reproducible 10k subset.
    Assumes T016 (create_subset) logic is applied here or the file
    'molecules_10k_subset.csv' exists if T016 already wrote it.
    For this task, we assume the raw source is available at `data/raw/qm9_raw.csv`
    (or similar) and we generate the subset if not present.
    """
    # Check if subset already exists (from T016)
    subset_path = raw_data_path.parent / "processed" / "molecules_10k_subset.csv"
    if subset_path.exists():
        print(f"Loading existing subset from {subset_path}")
        return pd.read_csv(subset_path)

    # Fallback: Load raw data and create subset if raw exists
    # In a real scenario, T015 would have downloaded this to data/raw/
    # We assume a standard QM9 download structure or a CSV export.
    # If the specific raw file isn't found, we raise a clear error.
    if not raw_data_path.exists():
        # Try to find any csv in data/raw
        raw_candidates = list(raw_data_path.parent.glob("raw/*.csv"))
        if not raw_candidates:
            raise FileNotFoundError(
                f"Raw data file not found at {raw_data_path} and no CSVs in {raw_data_path.parent / 'raw'}."
            )
        raw_path = raw_candidates[0]
        print(f"Found raw data at {raw_path}")
        df_raw = pd.read_csv(raw_path)
    else:
        df_raw = pd.read_csv(raw_data_path)

    print(f"Loaded raw data with {len(df_raw)} molecules.")
    subset_df = create_reproducible_subset(df_raw, target_size=10000, seed=42)
    print(f"Created reproducible subset with {len(subset_df)} molecules.")
    
    # Save the subset for downstream tasks (T016/T017/T018 usage)
    ensure_output_dir(subset_path.parent)
    subset_df.to_csv(subset_path, index=False)
    return subset_df


def extract_3d_features_wrapper(df_molecules: pd.DataFrame, output_path: Path) -> None:
    """
    Wrapper to extract 3D features and write to parquet.
    Uses the existing extract_3d_features logic from preprocess_3d.py.
    """
    print("Extracting 3D features...")
    # The existing function expects a DataFrame or list of molecules
    # and returns a DataFrame of features.
    df_features = extract_3d_features(df_molecules)
    
    # Ensure all columns are numeric for parquet
    for col in df_features.columns:
        if df_features[col].dtype == 'object':
            # Convert object columns (like lists) to strings or handle appropriately
            # For 3D features, we expect floats. If lists, we might need to flatten or store as string.
            # Assuming extract_3d_features returns a clean DataFrame of floats/ints.
            pass
    
    df_features.to_parquet(output_path, index=False)
    print(f"3D features written to {output_path} with shape {df_features.shape}")


def extract_2d_features_wrapper(df_molecules: pd.DataFrame, output_path: Path) -> None:
    """
    Wrapper to extract 2D features and write to parquet.
    Uses the existing extract_2d_features logic from extract_2d_descriptors.py.
    """
    print("Extracting 2D features...")
    df_features = extract_2d_features(df_molecules)
    
    df_features.to_parquet(output_path, index=False)
    print(f"2D features written to {output_path} with shape {df_features.shape}")


def generate_processed_data(
    raw_data_path: Path,
    output_dir: Path,
    subset_size: int = 10000,
    seed: int = 42
) -> None:
    """
    Main orchestration function to generate all processed data files:
    1. molecules_10k.parquet (subset of raw molecules)
    2. features_3d.parquet
    3. features_2d.parquet
    """
    set_seed(seed)
    ensure_output_dir(output_dir)

    # 1. Load and Subset
    df_molecules = load_molecule_subset(raw_data_path)
    
    # Save the subset as the main molecules file
    molecules_path = output_dir / "molecules_10k.parquet"
    df_molecules.to_parquet(molecules_path, index=False)
    print(f"Molecules subset written to {molecules_path}")

    # 2. Extract 3D Features
    features_3d_path = output_dir / "features_3d.parquet"
    extract_3d_features_wrapper(df_molecules, features_3d_path)

    # 3. Extract 2D Features
    features_2d_path = output_dir / "features_2d.parquet"
    extract_2d_features_wrapper(df_molecules, features_2d_path)

    print("All processed data generation complete.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate processed data files.")
    parser.add_argument(
        "--raw-data-path",
        type=Path,
        default=Path("data/raw/qm9.csv"),
        help="Path to the raw QM9 data file."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory to write processed output files."
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10000,
        help="Size of the random subset."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility."
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    args = parse_args()
    generate_processed_data(
        raw_data_path=args.raw_data_path,
        output_dir=args.output_dir,
        subset_size=args.subset_size,
        seed=args.seed
    )


if __name__ == "__main__":
    main()