from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
import pandas as pd

# Ensure we can import from the project root if running as a script
# This handles cases where the script is run from the code/ directory
# or from the project root.
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from data.handle_missing_coords import handle_missing_coordinates
from utils.reproducibility import set_global_seed

def ensure_output_dir(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def load_molecule_subset(raw_data_path: Path, subset_size: int = 10000) -> pd.DataFrame:
    """
    Load the raw QM9 data and create a reproducible subset.
    If raw data doesn't exist, attempt to download it first (via T015 logic).
    For this task, we assume T015 has run and data/raw/qm9.csv exists.
    """
    if not raw_data_path.exists():
        # Fallback: try to trigger download if possible, but strictly speaking
        # T015 should have done this. We raise a clear error if missing.
        raise FileNotFoundError(
            f"Raw QM9 data not found at {raw_data_path}. "
            "Please ensure T015 (download_qm9.py) has been executed successfully."
        )

    df = pd.read_csv(raw_data_path)
    if len(df) < subset_size:
        subset_size = len(df)
    
    # Use the reproducible subset function from T016
    subset_df = create_reproducible_subset(df, n_samples=subset_size, seed=42)
    return subset_df

def extract_3d_features(molecule_df: pd.DataFrame, output_path: Path) -> None:
    """
    Extract 3D features (coordinates, atom types, bonds) and save to parquet.
    This depends on T017 (preprocess_3d.py).
    """
    print(f"Extracting 3D features for {len(molecule_df)} molecules...")
    features_3d = extract_3d_features(molecule_df)
    ensure_output_dir(output_path.parent)
    features_3d.to_parquet(output_path, index=False)
    print(f"Saved 3D features to {output_path}")

def extract_2d_features(molecule_df: pd.DataFrame, output_path: Path) -> None:
    """
    Extract 2D features (fingerprints, Coulomb matrix) and save to parquet.
    This depends on T018 (extract_2d_descriptors.py).
    """
    print(f"Extracting 2D features for {len(molecule_df)} molecules...")
    features_2d = extract_2d_features(molecule_df)
    ensure_output_dir(output_path.parent)
    features_2d.to_parquet(output_path, index=False)
    print(f"Saved 2D features to {output_path}")

def generate_processed_data(
    raw_data_path: Path,
    output_dir: Path,
    subset_size: int = 10000
) -> None:
    """
    Main pipeline to generate all processed data artifacts for T020.
    
    Artifacts produced:
    - data/processed/molecules_10k.parquet (subset of raw molecules)
    - data/processed/features_3d.parquet
    - data/processed/features_2d.parquet
    """
    set_global_seed(42)
    
    # 1. Load and subset raw data
    print("Loading and subsetting raw data...")
    molecule_df = load_molecule_subset(raw_data_path, subset_size)
    
    # 2. Handle missing coordinates (T019)
    # This function returns a cleaned dataframe and writes an exclusion report
    print("Handling missing coordinates...")
    cleaned_molecule_df = handle_missing_coordinates(molecule_df)
    
    # Save the cleaned molecule subset (T020 requirement: molecules_10k.parquet)
    molecules_output = output_dir / "molecules_10k.parquet"
    ensure_output_dir(molecules_output.parent)
    cleaned_molecule_df.to_parquet(molecules_output, index=False)
    print(f"Saved cleaned molecule subset to {molecules_output}")
    
    # 3. Extract 3D features (T017)
    features_3d_output = output_dir / "features_3d.parquet"
    extract_3d_features(cleaned_molecule_df, features_3d_output)
    
    # 4. Extract 2D features (T018)
    features_2d_output = output_dir / "features_2d.parquet"
    extract_2d_features(cleaned_molecule_df, features_2d_output)
    
    print("All processed data generation complete.")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate processed data for molecular dipole prediction.")
    parser.add_argument(
        "--raw-data",
        type=Path,
        default=Path("data/raw/qm9.csv"),
        help="Path to the raw QM9 CSV file."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory to save processed data artifacts."
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10000,
        help="Number of molecules to include in the subset."
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    generate_processed_data(
        raw_data_path=args.raw_data,
        output_dir=args.output_dir,
        subset_size=args.subset_size
    )

if __name__ == "__main__":
    main()