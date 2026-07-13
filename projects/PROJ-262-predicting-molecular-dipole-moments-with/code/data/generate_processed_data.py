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

import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.create_subset import create_reproducible_subset
from data.preprocess_3d import extract_3d_features
from data.extract_2d_descriptors import extract_2d_features
from utils.reproducibility import set_seed

def ensure_output_dir(output_path: Path) -> None:
    """Ensure the output directory exists."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

def load_molecule_subset(raw_data_path: Path) -> pd.DataFrame:
    """
    Load the raw QM9 data and create a reproducible subset.
    
    Args:
        raw_data_path: Path to the raw QM9 dataset file.
        
    Returns:
        DataFrame containing the subset of molecules.
    """
    if not raw_data_path.exists():
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")
        
    # Load raw data
    df = pd.read_parquet(raw_data_path)
    
    # Create reproducible subset
    subset_df = create_reproducible_subset(df, n_samples=10000, seed=42)
    
    return subset_df

def extract_3d_features_internal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 3D features from molecule dataframe.
    
    Args:
        df: DataFrame with molecule data.
        
    Returns:
        DataFrame with 3D features.
    """
    features = []
    for _, row in df.iterrows():
        mol_id = row['molecule_id']
        try:
            feat = extract_3d_features(row)
            if feat is not None:
                features.append({
                    'molecule_id': mol_id,
                    'features_3d': feat
                })
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing {mol_id}: {e}")
            continue
    
    return pd.DataFrame(features)

def extract_2d_features_internal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract 2D features from molecule dataframe.
    
    Args:
        df: DataFrame with molecule data.
        
    Returns:
        DataFrame with 2D features.
    """
    features = []
    for _, row in df.iterrows():
        mol_id = row['molecule_id']
        try:
            feat = extract_2d_features(row)
            if feat is not None:
                features.append({
                    'molecule_id': mol_id,
                    'features_2d': feat
                })
        except Exception as e:
            # Log error but continue processing
            print(f"Error processing {mol_id}: {e}")
            continue
    
    return pd.DataFrame(features)

def generate_processed_data(
    raw_data_path: Path,
    output_dir: Path,
    subset_size: int = 10000,
    seed: int = 42
) -> Dict[str, Path]:
    """
    Generate all processed data files.
    
    Args:
        raw_data_path: Path to raw QM9 data.
        output_dir: Directory to write processed files.
        subset_size: Number of molecules in subset.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary mapping file types to output paths.
    """
    set_seed(seed)
    
    # Ensure output directory exists
    ensure_output_dir(output_dir / "molecules_10k.parquet")
    
    print(f"Loading raw data from {raw_data_path}...")
    molecules_df = load_molecule_subset(raw_data_path)
    
    print(f"Extracting 3D features for {len(molecules_df)} molecules...")
    features_3d_df = extract_3d_features_internal(molecules_df)
    
    print(f"Extracting 2D features for {len(molecules_df)} molecules...")
    features_2d_df = extract_2d_features_internal(molecules_df)
    
    # Define output paths
    molecules_path = output_dir / "molecules_10k.parquet"
    features_3d_path = output_dir / "features_3d.parquet"
    features_2d_path = output_dir / "features_2d.parquet"
    
    # Write output files
    print(f"Writing {molecules_path}...")
    molecules_df.to_parquet(molecules_path, index=False)
    
    print(f"Writing {features_3d_path}...")
    features_3d_df.to_parquet(features_3d_path, index=False)
    
    print(f"Writing {features_2d_path}...")
    features_2d_df.to_parquet(features_2d_path, index=False)
    
    return {
        'molecules': molecules_path,
        'features_3d': features_3d_path,
        'features_2d': features_2d_path
    }

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate processed data files")
    parser.add_argument(
        "--raw-data",
        type=str,
        default="data/raw/qm9.parquet",
        help="Path to raw QM9 data file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for processed files"
    )
    parser.add_argument(
        "--subset-size",
        type=int,
        default=10000,
        help="Number of molecules in subset"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    return parser.parse_args()

def main() -> None:
    """Main entry point."""
    args = parse_args()
    raw_data_path = Path(args.raw_data_path)
    output_dir = Path(args.output_dir)
    
    if not raw_data_path.exists():
        print(f"Error: Raw data file not found at {raw_data_path}")
        print("Please ensure T015 (download_qm9) has been executed successfully.")
        sys.exit(1)
    
    try:
        output_files = generate_processed_data(
            raw_data_path=raw_data_path,
            output_dir=output_dir,
            subset_size=args.subset_size,
            seed=args.seed
        )
        
        print("\nGenerated files:")
        for name, path in output_files.items():
            print(f"  {name}: {path}")
            
    except Exception as e:
        print(f"Error generating processed data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()