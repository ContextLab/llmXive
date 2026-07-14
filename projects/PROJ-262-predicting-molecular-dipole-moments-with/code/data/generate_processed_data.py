from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Import from existing API surface
from data.download_qm9 import download_qm9
from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from data.handle_missing_coords import handle_missing_coordinates
from utils.reproducibility import set_seed


def ensure_output_dir(path: Path) -> None:
    """Ensure the output directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def load_molecule_subset(raw_data_path: Path, subset_size: int = 10000) -> pd.DataFrame:
    """Load QM9, create reproducible subset, and return dataframe."""
    set_seed(42)
    
    # Download if not exists (handles integrity verification internally)
    if not raw_data_path.exists():
        download_qm9(str(raw_data_path.parent))
    
    # Load raw data
    df = pd.read_parquet(raw_data_path)
    
    # Create reproducible subset
    subset_df = create_reproducible_subset(df, size=subset_size, seed=42)
    
    return subset_df


def extract_3d_features_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    """Wrapper to extract 3D features from molecule dataframe."""
    # This calls the existing extraction logic
    features_3d = extract_3d_features(df)
    return features_3d


def extract_2d_features_wrapper(df: pd.DataFrame) -> pd.DataFrame:
    """Wrapper to extract 2D features from molecule dataframe."""
    # This calls the existing extraction logic
    features_2d = extract_2d_features(df)
    return features_2d


def generate_processed_data(
    raw_data_path: Path,
    output_dir: Path,
    subset_size: int = 10000
) -> Dict[str, Path]:
    """
    Main pipeline to generate all processed data files.
    
    Returns:
        Dictionary mapping output file names to their paths.
    """
    print(f"Starting processed data generation...")
    print(f"  Raw data: {raw_data_path}")
    print(f"  Output dir: {output_dir}")
    print(f"  Subset size: {subset_size}")
    
    # Ensure output directory exists
    ensure_output_dir(output_dir)
    
    # Step 1: Load and subset data
    print("Step 1: Loading and subsetting QM9 data...")
    molecules_df = load_molecule_subset(raw_data_path, subset_size)
    molecules_path = output_dir / "molecules_10k.parquet"
    molecules_df.to_parquet(molecules_path, index=False)
    print(f"  Saved molecules to: {molecules_path}")
    
    # Step 2: Handle missing coordinates (generates exclusion report)
    print("Step 2: Handling missing coordinates...")
    exclusion_report_path = output_dir.parent / "reports" / "excluded_molecules.csv"
    handle_missing_coordinates(molecules_df, str(exclusion_report_path))
    print(f"  Exclusion report saved to: {exclusion_report_path}")
    
    # Step 3: Extract 3D features
    print("Step 3: Extracting 3D features...")
    features_3d_df = extract_3d_features_wrapper(molecules_df)
    features_3d_path = output_dir / "features_3d.parquet"
    features_3d_df.to_parquet(features_3d_path, index=False)
    print(f"  Saved 3D features to: {features_3d_path}")
    
    # Step 4: Extract 2D features
    print("Step 4: Extracting 2D features...")
    features_2d_df = extract_2d_features_wrapper(molecules_df)
    features_2d_path = output_dir / "features_2d.parquet"
    features_2d_df.to_parquet(features_2d_path, index=False)
    print(f"  Saved 2D features to: {features_2d_path}")
    
    print("Processed data generation complete!")
    
    return {
        "molecules": molecules_path,
        "features_3d": features_3d_path,
        "features_2d": features_2d_path
    }


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate processed data files for molecular dipole prediction."
    )
    parser.add_argument(
        "--raw-data",
        type=str,
        default="data/raw/qm9.parquet",
        help="Path to raw QM9 dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory for processed output files"
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10000,
        help="Size of the reproducible subset"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    
    raw_data_path = Path(args.raw_data)
    output_dir = Path(args.output_dir)
    
    generate_processed_data(
        raw_data_path=raw_data_path,
        output_dir=output_dir,
        subset_size=args.subset_size
    )


if __name__ == "__main__":
    main()