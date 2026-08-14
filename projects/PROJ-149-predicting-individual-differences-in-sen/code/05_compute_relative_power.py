"""
T015: Calculate relative power (band/total) from raw PSD values.
Input: data/interim/eeg_psd.csv (raw power)
Output: data/processed/features.csv (relative power)

Constraint: NO CLR transformation.
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

from config import get_path, ensure_dirs

def load_raw_features(input_path: str) -> pd.DataFrame:
    """Load the raw PSD features."""
    print(f"Loading raw features from: {input_path}")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def compute_relative_power(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate relative power for each band.
    Relative Power = Band Power / Total Power
    Total Power = Sum of all band powers (delta, theta, alpha, low_beta, high_beta, gamma)
    """
    band_cols = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    
    # Verify columns exist
    missing = set(band_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required band columns: {missing}")
    
    # Calculate total power
    df['total_power'] = df[band_cols].sum(axis=1)
    
    # Avoid division by zero
    df['total_power'] = df['total_power'].replace(0, np.nan)
    
    # Compute relative power
    relative_cols = {}
    for col in band_cols:
        relative_cols[f'relative_{col}'] = df[col] / df['total_power']
    
    relative_df = pd.DataFrame(relative_cols)
    
    # Merge with original ID and RT columns if they exist
    id_cols = [c for c in df.columns if c in ['participant_id', 'median_rt']]
    result = pd.concat([df[id_cols], relative_df], axis=1)
    
    return result

def validate_output(df: pd.DataFrame, output_path: str) -> bool:
    """Basic validation before writing."""
    if df.isnull().any().any():
        print("WARNING: Output contains nulls.")
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Compute relative power from raw PSD")
    parser.add_argument("--input", type=str, default=None, help="Path to eeg_psd.csv")
    parser.add_argument("--output", type=str, default=None, help="Path to output features.csv")
    args = parser.parse_args()
    
    input_path = args.input if args.input else get_path("interim", "eeg_psd.csv")
    output_path = args.output if args.output else get_path("processed", "features.csv")
    
    # Ensure output directory exists
    ensure_dirs(os.path.dirname(output_path))
    
    try:
        df_raw = load_raw_features(input_path)
        df_relative = compute_relative_power(df_raw)
        
        if not validate_output(df_relative, output_path):
            print("Validation failed, but proceeding to write (check logs).")
        
        df_relative.to_csv(output_path, index=False)
        print(f"Saved relative power features to: {output_path}")
        print(f"Shape: {df_relative.shape}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
