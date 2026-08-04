"""
Task T025c: Apply mask to baseline calculation.

Logic:
1. Ensure the `is_contaminated` column is present and correct in the input data.
2. Prepare the DataFrame for T022 (baseline calculation) by ensuring the mask
   is ready to be used for excluding contaminated windows from the baseline
   noise floor calculation.

This script reads the output of T025b (generate_contaminated_mask.py),
validates the mask, and writes the prepared DataFrame back to disk.
"""
import os
import sys
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

from code.config import get_project_root
from code.utils.io_utils import ensure_dir, read_csv, write_csv
from code.utils.validator import validate_trajectory_data


def load_divergence_data(input_path: Path) -> pd.DataFrame:
    """Load the divergence data from the processed CSV."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = read_csv(input_path)
    
    # Validate basic structure
    required_cols = ['seed_id', 'bias_type', 'timestep', 'G_t', 'dG_t']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    return df


def apply_contaminated_mask(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply the contaminated mask logic for baseline preparation.
    
    This function ensures the 'is_contaminated' column exists and is boolean.
    It prepares the dataframe for T022 by ensuring the mask is correctly
    formatted for baseline calculation logic.
    
    Args:
        df: DataFrame containing trajectory data with 'is_contaminated' column.
        
    Returns:
        DataFrame ready for baseline calculation.
    """
    if 'is_contaminated' not in df.columns:
        raise ValueError("DataFrame missing 'is_contaminated' column. "
                       "Run generate_contaminated_mask.py first.")
    
    # Ensure the column is boolean
    df['is_contaminated'] = df['is_contaminated'].astype(bool)
    
    # Validate that we have a mix of contaminated and non-contaminated
    # (If all are contaminated, the baseline calculation will fail later)
    contaminated_count = df['is_contaminated'].sum()
    total_count = len(df)
    
    if contaminated_count == total_count:
        raise ValueError("All timesteps are marked as contaminated. "
                       "Cannot calculate baseline noise floor.")
    
    if contaminated_count == 0:
        # No contamination detected - this is valid, just means baseline uses all data
        pass
    
    # Sort by seed_id and timestep to ensure proper ordering for downstream
    df = df.sort_values(by=['seed_id', 'timestep']).reset_index(drop=True)
    
    return df


def main():
    """Main entry point for T025c."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence.csv"
    output_path = project_root / "data" / "processed" / "trajectories_divergence_masked.csv"
    
    print(f"Starting T025c: Apply contaminated mask")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    # Load data
    try:
        df = load_divergence_data(input_path)
        print(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        print(f"ERROR: Failed to load input data: {e}")
        sys.exit(1)
    
    # Apply mask logic
    try:
        df_masked = apply_contaminated_mask(df)
        print(f"Applied contaminated mask. "
              f"Total rows: {len(df_masked)}, "
              f"Contaminated: {df_masked['is_contaminated'].sum()}")
    except Exception as e:
        print(f"ERROR: Failed to apply mask: {e}")
        sys.exit(1)
    
    # Ensure output directory exists
    ensure_dir(output_path.parent)
    
    # Write output
    try:
        write_csv(df_masked, output_path)
        print(f"Successfully wrote masked data to {output_path}")
    except Exception as e:
        print(f"ERROR: Failed to write output: {e}")
        sys.exit(1)
    
    print("T025c completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
