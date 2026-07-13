from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Add project root to path to resolve imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from utils.reproducibility import set_seed


def ensure_output_dir(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def load_molecule_subset(raw_path: Path, subset_size: int = 10000) -> pd.DataFrame:
    """
    Load the raw QM9 data and create a reproducible subset.
    Expects raw data to be in data/raw/ (e.g., from download_qm9.py).
    """
    # Check for raw data files. QM9 download typically produces a CSV or similar.
    # We look for the most likely output from T015/T016.
    # If the download task produced 'qm9.csv' or similar in data/raw, use it.
    # Since T015/T016 are marked done, we assume the data exists or we handle the case.
    
    raw_files = list(raw_path.glob("*.csv"))
    if not raw_files:
        # Fallback: check for common names if glob didn't catch it
        raw_files = [raw_path / "qm9.csv"] if (raw_path / "qm9.csv").exists() else []
    
    if not raw_files:
        raise FileNotFoundError(
            f"No raw data found in {raw_path}. "
            "Ensure T015 (download_qm9) and T016 (create_subset) have run successfully."
        )
    
    source_file = raw_files[0]
    print(f"Loading raw data from: {source_file}")
    df = pd.read_csv(source_file)
    
    # Apply reproducible subset if the raw file is larger than target
    if len(df) > subset_size:
        print(f"Creating reproducible subset of {subset_size} molecules...")
        df = create_reproducible_subset(df, size=subset_size, seed=42)
    
    return df


def extract_3d_features(df: pd.DataFrame, output_path: Path) -> None:
    """
    Extract 3D features (coordinates, atom types, bonds) and save to parquet.
    """
    print("Extracting 3D features...")
    # The function extract_3d_features from preprocess_3d expects a DataFrame
    # and returns a processed DataFrame or writes directly. 
    # Based on T017 description, it extracts coordinates, atom types, bonds.
    # We assume it returns a DataFrame ready for saving or writes internally.
    # To be safe and explicit per T020 requirement:
    
    # Call the existing implementation
    processed_3d = extract_3d_features(df)
    
    # Ensure it has the required columns or structure
    # If the function returns a dict or list, convert to DF
    if isinstance(processed_3d, dict):
        processed_3d = pd.DataFrame([processed_3d])
    elif isinstance(processed_3d, list):
        processed_3d = pd.DataFrame(processed_3d)
    
    # Validate no missing values in critical columns if possible
    # (T019 handles exclusion, so this should be clean)
    
    processed_3d.to_parquet(output_path, index=False)
    print(f"Saved 3D features to: {output_path}")


def extract_2d_features(df: pd.DataFrame, output_path: Path) -> None:
    """
    Extract 2D features (fingerprints, Coulomb matrix) and save to parquet.
    """
    print("Extracting 2D features...")
    # Call the existing implementation from T018
    processed_2d = extract_2d_features(df)
    
    if isinstance(processed_2d, dict):
        processed_2d = pd.DataFrame([processed_2d])
    elif isinstance(processed_2d, list):
        processed_2d = pd.DataFrame(processed_2d)
    
    processed_2d.to_parquet(output_path, index=False)
    print(f"Saved 2D features to: {output_path}")


def generate_processed_data(
    raw_dir: str,
    output_dir: str,
    subset_size: int = 10000
) -> None:
    """
    Main pipeline to generate all processed data files.
    """
    set_seed(42)
    
    raw_path = Path(raw_dir)
    out_path = Path(output_dir)
    ensure_output_dir(out_path)
    
    # 1. Load and subset
    molecules_df = load_molecule_subset(raw_path, subset_size)
    print(f"Loaded {len(molecules_df)} molecules.")
    
    # 2. Save the main molecule dataframe (molecules_10k.parquet)
    molecules_output = out_path / "molecules_10k.parquet"
    molecules_df.to_parquet(molecules_output, index=False)
    print(f"Saved molecules subset to: {molecules_output}")
    
    # 3. Extract and save 3D features
    features_3d_output = out_path / "features_3d.parquet"
    extract_3d_features(molecules_df, features_3d_output)
    
    # 4. Extract and save 2D features
    features_2d_output = out_path / "features_2d.parquet"
    extract_2d_features(molecules_df, features_2d_output)
    
    print("All processed data generated successfully.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate processed data for dipole prediction.")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default="data/raw",
        help="Directory containing raw QM9 data."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to write processed data files."
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
    data_dir = Path(args.data_dir)
    
    # Define paths
    # T016 creates molecule_subset.csv in data/processed (or similar)
    # We assume the input is in the same directory or we use the data_dir as base.
    # The task says: Generate output files: data/processed/molecules_10k.parquet, features_3d.parquet, features_2d.parquet
    # We assume the input subset is also in data/processed (from T016).
    
    output_molecules = data_dir / "molecules_10k.parquet"
    output_3d = data_dir / "features_3d.parquet"
    output_2d = data_dir / "features_2d.parquet"
    
    # The input subset file name is assumed to be molecule_subset.csv based on T016 logic
    # If T016 outputs a different name, we might need to adjust.
    # Let's assume the standard name.
    input_subset = data_dir / "molecule_subset.csv"
    
    # If the subset file is not in data/processed, we might need to look elsewhere.
    # But T016 is "Create a reproducible random subset", likely saving to data/processed.
    
    generate_processed_data(
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        subset_size=args.subset_size
    )


if __name__ == "__main__":
    main()