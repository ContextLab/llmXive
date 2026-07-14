"""
Task T020: Generate output files for User Story 1.

Produces:
  - data/processed/molecules_10k.parquet
  - data/processed/features_3d.parquet
  - data/processed/features_2d.parquet

This script orchestrates the loading of the QM9 subset, extraction of 3D
features (coords, atoms, bonds), and extraction of 2D descriptors (fingerprints,
coulomb matrix), then saves them as parquet files.

Dependencies:
  - code/data/preprocess_3d.py (extract_3d_features)
  - code/data/extract_2d_descriptors.py (extract_2d_features)
  - code/data/create_subset.py (create_reproducible_subset)
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Ensure we can import from the project root
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

def load_molecule_subset(raw_data_path: Path, subset_size: int = 10000) -> pd.DataFrame:
    """
    Load the raw QM9 data and create a reproducible subset.
    
    Args:
        raw_data_path: Path to the raw QM9 data file (e.g., data/raw/qm9.csv).
        subset_size: Number of molecules to include in the subset.
        
    Returns:
        DataFrame containing the subset of molecules.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
    
    # Load raw data
    df = pd.read_csv(raw_data_path)
    
    # Create reproducible subset
    subset_df = create_reproducible_subset(df, size=subset_size, seed=42)
    
    return subset_df

def extract_3d_features_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper to extract 3D features from the molecule DataFrame.
    
    Args:
        df: DataFrame with molecule data.
        
    Returns:
        DataFrame with 3D features.
    """
    # Use the existing extract_3d_features function
    # It expects a DataFrame with 'molecule_id', 'atoms', 'coordinates', etc.
    features_3d = extract_3d_features(df)
    return features_3d

def extract_2d_features_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper to extract 2D features from the molecule DataFrame.
    
    Args:
        df: DataFrame with molecule data.
        
    Returns:
        DataFrame with 2D features.
    """
    # Use the existing extract_2d_features function
    # It expects a DataFrame with 'molecule_id', 'atoms', 'coordinates', etc.
    features_2d = extract_2d_features(df)
    return features_2d

def generate_processed_data(
    raw_data_path: Path,
    output_dir: Path,
    subset_size: int = 10000,
    seed: int = 42
) -> Dict[str, Path]:
    """
    Main function to generate all processed data files.
    
    Args:
        raw_data_path: Path to the raw QM9 data file.
        output_dir: Directory to save processed data files.
        subset_size: Number of molecules in the subset.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary mapping output file names to their paths.
    """
    set_seed(seed)
    
    # Ensure output directory exists
    ensure_output_dir(output_dir)
    
    print(f"Loading raw data from: {raw_data_path}")
    molecule_df = load_molecule_subset(raw_data_path, subset_size)
    print(f"Created subset with {len(molecule_df)} molecules")
    
    # Save molecules_10k.parquet
    molecules_path = output_dir / "molecules_10k.parquet"
    molecule_df.to_parquet(molecules_path, index=False)
    print(f"Saved molecules to: {molecules_path}")
    
    # Extract and save 3D features
    print("Extracting 3D features...")
    features_3d_df = extract_3d_features_wrapper(molecule_df)
    features_3d_path = output_dir / "features_3d.parquet"
    features_3d_df.to_parquet(features_3d_path, index=False)
    print(f"Saved 3D features to: {features_3d_path}")
    
    # Extract and save 2D features
    print("Extracting 2D features...")
    features_2d_df = extract_2d_features_wrapper(molecule_df)
    features_2d_path = output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(features_2d_path, index=False)
    print(f"Saved 2D features to: {features_2d_path}")
    
    return {
        "molecules_10k.parquet": molecules_path,
        "features_3d.parquet": features_3d_path,
        "features_2d.parquet": features_2d_path
    }

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate processed data files for molecular dipole prediction.")
    parser.add_argument(
        "--raw-data",
        type=str,
        default="data/raw/qm9.csv",
        help="Path to the raw QM9 data file (default: data/raw/qm9.csv)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save processed data files (default: data/processed)"
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10000,
        help="Number of molecules in the subset (default: 10000)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)"
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    raw_data_path = Path(args.raw_data)
    output_dir = Path(args.output_dir)
    
    if not raw_data_path.exists():
        print(f"Error: Raw data file not found at {raw_data_path}")
        print("Please run 'python code/data/download_qm9.py' first to download the dataset.")
        sys.exit(1)
    
    try:
        output_files = generate_processed_data(
            raw_data_path=raw_data_path,
            output_dir=output_dir,
            subset_size=args.subset_size,
            seed=args.seed
        )
        print("\nSuccessfully generated the following files:")
        for name, path in output_files.items():
            print(f"  - {path}")
    except Exception as e:
        print(f"Error generating processed data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()