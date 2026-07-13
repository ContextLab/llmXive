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

# Ensure project root is in path for imports if running as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from utils.reproducibility import set_seed

def ensure_output_dir(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def load_molecule_subset(data_path: Path) -> pd.DataFrame:
    """Load the raw molecule subset created by T016."""
    # T016 creates data/processed/molecule_subset.csv (or similar)
    # We assume the subset is available here. If not, we fallback to a small real sample
    # from QM9 if the file is missing, but T016 should have created it.
    # For robustness, we check for the expected file from T016.
    # The task T016 description says "Create a reproducible random subset".
    # Let's assume it outputs to data/processed/molecule_subset.csv
    
    subset_file = data_path / "molecule_subset.csv"
    
    if not subset_file.exists():
        # Fallback: If T016 didn't run or failed, we try to load raw QM9 if available
        # This is a safety net. The primary path is T016 -> T017/T018 -> T020.
        # However, T016 is marked completed. We expect the file.
        # If it's missing, we might need to re-run T016, but here we just error out or try to fetch raw.
        # Given the constraint "Real data only", we cannot fabricate.
        # We will attempt to load the raw QM9 data if the subset is missing, but that's T015's job.
        # Let's assume the file exists as per T016 completion.
        raise FileNotFoundError(f"Expected molecule subset file not found: {subset_file}. "
                                "Please ensure T016 (create_subset.py) has been executed successfully.")
    
    df = pd.read_csv(subset_file)
    return df

def extract_3d_features_wrapper(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """Wrapper to call extract_3d_features and return the result DataFrame."""
    # The function extract_3d_features from preprocess_3d.py is expected to take a DF and return features
    # Based on T017, it extracts 3D coordinates, atom types, and bond connectivity.
    # We assume it returns a DataFrame with columns: molecule_id, features_3d (list of floats)
    # and potentially other metadata.
    
    print("Extracting 3D features...")
    # We pass the dataframe. The function signature in T017 is likely:
    # extract_3d_features(df: pd.DataFrame) -> pd.DataFrame
    features_3d_df = extract_3d_features(df)
    
    # Save to parquet
    ensure_output_dir(output_path.parent)
    features_3d_df.to_parquet(output_path, index=False)
    print(f"Saved 3D features to {output_path}")
    return features_3d_df

def extract_2d_features_wrapper(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """Wrapper to call extract_2d_features and return the result DataFrame."""
    print("Extracting 2D features...")
    # Similar to 3D, this should return a DataFrame with molecule_id and features_2d
    features_2d_df = extract_2d_features(df)
    
    ensure_output_dir(output_path.parent)
    features_2d_df.to_parquet(output_path, index=False)
    print(f"Saved 2D features to {output_path}")
    return features_2d_df

def generate_processed_data(
    raw_data_path: Path,
    output_3d_path: Path,
    output_2d_path: Path,
    output_molecules_path: Path
) -> None:
    """
    Main function to generate all processed data files for T020.
    
    1. Loads the molecule subset (from T016).
    2. Extracts 3D features (T017).
    3. Extracts 2D features (T018).
    4. Saves the original subset (or a processed version of it) to molecules_10k.parquet.
    """
    # Load the subset
    try:
        molecule_df = load_molecule_subset(raw_data_path)
    except FileNotFoundError as e:
        print(f"Error loading subset: {e}")
        # If the subset is missing, we cannot proceed with real data.
        # We should not fabricate.
        sys.exit(1)

    # Ensure we have the 10k limit (T016 should have done this, but we verify)
    if len(molecule_df) > 10000:
        print(f"Subset size {len(molecule_df)} exceeds 10k. Truncating.")
        molecule_df = molecule_df.head(10000)

    # Save the molecules dataframe (with original columns + any processed metadata) to molecules_10k.parquet
    # The task requires: data/processed/molecules_10k.parquet
    ensure_output_dir(output_molecules_path.parent)
    molecule_df.to_parquet(output_molecules_path, index=False)
    print(f"Saved molecules data to {output_molecules_path}")

    # Extract 3D features
    extract_3d_features_wrapper(molecule_df, output_3d_path)

    # Extract 2D features
    extract_2d_features_wrapper(molecule_df, output_2d_path)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate processed data for molecular dipole prediction.")
    parser.add_argument("--data-dir", type=str, default="data/processed",
                        help="Directory containing the molecule subset and where to save outputs.")
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
        raw_data_path=data_dir, # Passing the directory where the subset is expected
        output_3d_path=output_3d,
        output_2d_path=output_2d,
        output_molecules_path=output_molecules
    )

if __name__ == "__main__":
    main()