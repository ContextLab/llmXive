from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Project-relative imports based on provided API surface
from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from utils.reproducibility import set_seed

def ensure_output_dir(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def load_molecule_subset(raw_data_path: Path, subset_size: int = 10000) -> pd.DataFrame:
    """
    Load the raw QM9 data (or the pre-downloaded subset if available)
    and create a reproducible 10k subset.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {raw_data_path}. "
                                "Please run download_qm9.py first.")
    
    # Load raw data
    df = pd.read_parquet(raw_data_path)
    
    # Create reproducible subset
    subset_df = create_reproducible_subset(df, n_samples=subset_size, seed=42)
    
    return subset_df

def extract_3d_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 3D features (coordinates, atom types, bonds) from the molecule subset.
    Uses the existing extract_3d_features logic from preprocess_3d.
    """
    # Call the existing function from preprocess_3d module
    return extract_3d_features(df)

def extract_2d_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 2D features (fingerprints, Coulomb matrix) from the molecule subset.
    Uses the existing extract_2d_features logic from extract_2d_descriptors.
    """
    # Call the existing function from extract_2d_descriptors module
    return extract_2d_features(df)

def generate_processed_data(
    raw_data_path: Path,
    output_dir: Path,
    subset_size: int = 10000
) -> Dict[str, Path]:
    """
    Main pipeline to generate processed data files:
    1. Load and subset raw data
    2. Extract 3D features
    3. Extract 2D features
    4. Save all outputs to parquet files
    
    Returns:
        Dict mapping output file names to their paths
    """
    set_seed(42)
    
    print(f"Loading raw data from {raw_data_path}...")
    molecules_df = load_molecule_subset(raw_data_path, subset_size)
    print(f"Created subset with {len(molecules_df)} molecules.")
    
    print("Extracting 3D features...")
    features_3d_df = extract_3d_features(molecules_df)
    print(f"Extracted 3D features for {len(features_3d_df)} molecules.")
    
    print("Extracting 2D features...")
    features_2d_df = extract_2d_features(molecules_df)
    print(f"Extracted 2D features for {len(features_2d_df)} molecules.")
    
    # Ensure output directory exists
    ensure_output_dir(output_dir)
    
    # Define output paths
    molecules_path = output_dir / "molecules_10k.parquet"
    features_3d_path = output_dir / "features_3d.parquet"
    features_2d_path = output_dir / "features_2d.parquet"
    
    # Save to parquet
    print(f"Saving molecules subset to {molecules_path}...")
    molecules_df.to_parquet(molecules_path, index=False)
    
    print(f"Saving 3D features to {features_3d_path}...")
    features_3d_df.to_parquet(features_3d_path, index=False)
    
    print(f"Saving 2D features to {features_2d_path}...")
    features_2d_df.to_parquet(features_2d_path, index=False)
    
    return {
        "molecules_10k.parquet": molecules_path,
        "features_3d.parquet": features_3d_path,
        "features_2d.parquet": features_2d_path
    }

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate processed data files from QM9 subset.")
    parser.add_argument(
        "--raw-data",
        type=str,
        default="data/raw/qm9.parquet",
        help="Path to the raw QM9 data file."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save processed data files."
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10000,
        help="Size of the reproducible subset to create."
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    raw_data_path = Path(args.raw_data)
    output_dir = Path(args.output_dir)
    
    try:
        output_files = generate_processed_data(raw_data_path, output_dir, args.subset_size)
        print("\nSuccessfully generated processed data files:")
        for name, path in output_files.items():
            print(f"  - {name}: {path}")
    except Exception as e:
        print(f"Error generating processed data: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()