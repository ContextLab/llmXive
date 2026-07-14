from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
import numpy as np

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from data.download_qm9 import download_qm9
from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from data.handle_missing_coords import handle_missing_coordinates
from utils.reproducibility import set_seed


def ensure_output_dir() -> Path:
    """Ensure the processed data directory exists."""
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_PROCESSED_DIR


def load_molecule_subset(raw_data_path: Path, subset_size: int = 10000) -> pd.DataFrame:
    """
    Load the raw QM9 data and create a reproducible subset.
    This function assumes download_qm9 has been run and the raw file exists.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found at {raw_data_path}. "
                                "Please run download_qm9.py first.")

    # Load raw data (assuming CSV format from download_qm9)
    df = pd.read_csv(raw_data_path)

    # Create reproducible subset
    subset_df = create_reproducible_subset(df, size=subset_size, seed=42)
    return subset_df


def extract_3d_features_wrapper(subset_df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Extract 3D features and return the processed dataframe.
    """
    print(f"Extracting 3D features for {len(subset_df)} molecules...")
    features_3d = extract_3d_features(subset_df)
    features_3d.to_parquet(output_path, index=False)
    print(f"3D features saved to {output_path}")
    return features_3d


def extract_2d_features_wrapper(subset_df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Extract 2D features and return the processed dataframe.
    """
    print(f"Extracting 2D features for {len(subset_df)} molecules...")
    features_2d = extract_2d_features(subset_df)
    features_2d.to_parquet(output_path, index=False)
    print(f"2D features saved to {output_path}")
    return features_2d


def generate_processed_data(
    raw_data_path: Path,
    subset_output_path: Path,
    features_3d_path: Path,
    features_2d_path: Path,
    seed: int = 42
) -> Dict[str, Path]:
    """
    Main orchestration function to generate all processed data files.
    """
    set_seed(seed)

    # Ensure output directories exist
    ensure_output_dir(output_dir)

    # Load and subset data
    print(f"Loading raw data from {raw_data_path}...")
    subset_df = load_molecule_subset(raw_data_path, subset_size)
    print(f"Created subset with {len(subset_df)} molecules.")

    # Define output paths
    molecules_path = output_dir / "molecules_10k.parquet"
    features_3d_path = output_dir / "features_3d.parquet"
    features_2d_path = output_dir / "features_2d.parquet"

    # Save the subset molecules dataframe (includes coordinates and dipole)
    print("Saving molecules subset...")
    subset_df.to_parquet(molecules_path, index=False)
    print(f"Molecules subset saved to {molecules_path}")

    # Extract and save 3D features
    extract_3d_features_wrapper(subset_df, features_3d_path)

    # Extract and save 2D features
    extract_2d_features_wrapper(subset_df, features_2d_path)

    return {
        "molecules": molecules_path,
        "features_3d": features_3d_path,
        "features_2d": features_2d_path
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate processed data files for dipole moment prediction.")
    parser.add_argument(
        "--raw-data",
        type=str,
        default="data/raw/qm9.csv",
        help="Path to the raw QM9 dataset CSV file."
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
        help="Size of the random subset to create."
    )
    parser.add_argument(
        "--features-2d", 
        type=Path, 
        default=Path("data/processed/features_2d.parquet"),
        help="Path for 2D features parquet file."
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_data_path = Path(args.raw_data)
    output_dir = Path(args.output_dir)

    if not raw_data_path.exists():
        print(f"Error: Raw data file not found at {raw_data_path}")
        print("Please ensure you have run code/data/download_qm9.py first.")
        sys.exit(1)

    try:
        results = generate_processed_data(
            raw_data_path=raw_data_path,
            output_dir=output_dir,
            subset_size=args.subset_size,
            seed=args.seed
        )
        print("\nProcessed data generation completed successfully:")
        for name, path in results.items():
            print(f"  - {name}: {path}")
    except Exception as e:
        print(f"Error generating processed data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()