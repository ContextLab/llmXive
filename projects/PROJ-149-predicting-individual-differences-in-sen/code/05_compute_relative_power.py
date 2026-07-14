"""
T015: Compute relative power (band/total) to control for total power confound.

Consumes: data/processed/features_raw.csv (merged T012/T013 output)
Produces: data/processed/features.csv (with relative power columns)

Requirement FR-010: Implement relative power calculation (band/total) for all bands.
"""
import os
import sys
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

# Import config for band definitions
sys.path.insert(0, str(Path(__file__).parent))
from config import get_band_freqs, get_all_band_names, ensure_dirs, get_path

def load_raw_features(input_path: str) -> pd.DataFrame:
    """Load the merged raw features dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Validate expected columns exist
    band_cols = get_all_band_names()
    # Check for absolute power columns (expected to be in raw features)
    # The naming convention from T012 is typically 'power_{band}' or just 'delta', 'theta' etc.
    # We assume the input has columns matching the band names or 'power_{band}'
    # Let's check for standard naming: if 'delta' exists, use it. Else 'power_delta'.
    available_cols = set(df.columns)
    power_cols = {}
    
    for band in band_cols:
        # Try direct name first, then 'power_{name}'
        if band in available_cols:
            power_cols[band] = band
        elif f"power_{band}" in available_cols:
            power_cols[band] = f"power_{band}"
        else:
            raise ValueError(f"Could not find absolute power column for band '{band}' in {input_path}. "
                             f"Available columns: {list(available_cols)}")
    
    return df, power_cols

def compute_relative_power(df: pd.DataFrame, power_cols: dict) -> pd.DataFrame:
    """
    Calculate relative power for each band: relative_{band} = power_{band} / total_power.
    Total power is the sum of all band powers.
    """
    df = df.copy()
    
    # Calculate total power (sum of all band powers)
    total_power = sum(df[col] for col in power_cols.values())
    
    # Handle potential division by zero or NaN
    # If total power is 0 or NaN, relative power should be 0 or NaN (handled by pandas)
    # We add a tiny epsilon to avoid division by zero if total is exactly 0, 
    # though in EEG this is rare unless all channels were rejected.
    epsilon = 1e-10
    total_power_safe = total_power.replace(0, np.nan) # Replace 0 with NaN to propagate
    
    band_names = get_all_band_names()
    relative_cols = {}
    
    for band in band_names:
        col_name = power_cols[band]
        rel_col_name = f"rel_{band}"
        
        # Compute relative power
        df[rel_col_name] = df[col_name] / (total_power_safe + epsilon)
        
        # Ensure values are in [0, 1] range (sanity check, though mathematically should be)
        # If total power was 0 (NaN), result is NaN. If total was 0 but we added epsilon, 
        # it might be small. We clamp to [0, 1] just in case of floating point issues.
        df[rel_col_name] = df[rel_col_name].clip(lower=0.0, upper=1.0)
        
        relative_cols[band] = rel_col_name
    
    return df, relative_cols

def validate_output(df: pd.DataFrame) -> None:
    """Validate the output dataframe has no nulls in key columns."""
    band_names = get_all_band_names()
    key_cols = ['participant_id'] + [f"rel_{b}" for b in band_names]
    
    for col in key_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
        
        null_count = df[col].isna().sum()
        if null_count > 0:
            raise ValueError(f"Column '{col}' contains {null_count} null values.")
    
    # Check for infinite values
    for col in key_cols:
        if np.isinf(df[col]).any():
            raise ValueError(f"Column '{col}' contains infinite values.")

def main():
    parser = argparse.ArgumentParser(description="Compute relative band powers from raw features.")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to input features_raw.csv. Defaults to config path.")
    parser.add_argument("--output", type=str, default=None,
                        help="Path to output features.csv. Defaults to config path.")
    args = parser.parse_args()
    
    # Determine paths
    if args.input:
        input_path = args.input
    else:
        input_path = get_path("processed", "features_raw.csv")
    
    if args.output:
        output_path = args.output
    else:
        output_path = get_path("processed", "features.csv")
    
    # Ensure output directory exists
    ensure_dirs()
    
    print(f"Loading raw features from: {input_path}")
    df_raw, power_cols = load_raw_features(input_path)
    print(f"Loaded {len(df_raw)} participants.")
    
    print("Computing relative power...")
    df_rel, rel_cols = compute_relative_power(df_raw, power_cols)
    
    print("Validating output...")
    validate_output(df_rel)
    
    print(f"Saving processed features to: {output_path}")
    df_rel.to_csv(output_path, index=False)
    
    print(f"Successfully generated {output_path} with relative power columns: {list(rel_cols.values())}")

if __name__ == "__main__":
    main()