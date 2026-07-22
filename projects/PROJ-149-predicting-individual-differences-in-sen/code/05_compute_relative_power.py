"""
Task T015: Compute relative band power (band / total_power) for all bands.

Consumes: data/processed/features_raw.csv (output of T012/T013 merge)
Produces: data/processed/features.csv

Implements FR-010: Control for total power confound by normalizing band power.
"""
import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, load_config, get_all_band_names

# Define the full set of bands used in the pipeline.
# Note: 'total' is not a band name from config, but a computed aggregate.
BANDS_TO_NORMALIZE = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']

def load_raw_features(input_path: Path) -> pd.DataFrame:
    """
    Load the raw features dataframe produced by T012/T013.
    
    Args:
        input_path: Path to features_raw.csv
        
    Returns:
        DataFrame with columns: participant_id, median_rt, and absolute power bands.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Ensure T012 and T013 have completed successfully.")
    
    df = pd.read_csv(input_path)
    
    # Verify required columns exist
    required_cols = ['participant_id', 'median_rt'] + BANDS_TO_NORMALIZE
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
        
    return df

def compute_relative_power(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute relative power for each band: rel_{band} = abs_{band} / total_power.
    
    Total power is defined as the sum of absolute powers across the defined bands.
    This controls for global amplitude differences between participants.
    
    Args:
        df: DataFrame with absolute band power columns.
        
    Returns:
        DataFrame with new columns: rel_delta, rel_theta, etc.
    """
    df = df.copy()
    
    # Calculate total power as sum of the defined bands
    # This assumes the bands partition the frequency range of interest sufficiently
    # or represent the specific bands of interest for normalization.
    power_cols = [f"{b}" for b in BANDS_TO_NORMALIZE]
    
    # Ensure no negative values (should not happen with PSD, but safety check)
    df[power_cols] = df[power_cols].clip(lower=0)
    
    # Compute total power
    df['total_power'] = df[power_cols].sum(axis=1)
    
    # Handle potential division by zero (if total power is 0)
    # In real EEG data this is extremely unlikely, but we guard against it.
    if (df['total_power'] == 0).any():
        zero_indices = df[df['total_power'] == 0].index
        print(f"Warning: {len(zero_indices)} participants have zero total power. "
              "Setting relative power to NaN for these rows.")
    
    # Compute relative power
    for band in BANDS_TO_NORMALIZE:
        col_name = f"rel_{band}"
        df[col_name] = df[band] / df['total_power']
        
    return df

def validate_output(df: pd.DataFrame) -> None:
    """
    Validate the output dataframe meets FR-010 requirements.
    
    Checks:
    - All relative power columns exist.
    - No nulls in relative power columns.
    - Values are between 0 and 1 (inclusive, allowing small float error).
    """
    rel_cols = [f"rel_{b}" for b in BANDS_TO_NORMALIZE]
    
    # Check existence
    missing_cols = [c for c in rel_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Output validation failed: Missing relative power columns: {missing_cols}")
        
    # Check nulls
    for col in rel_cols:
        if df[col].isnull().any():
            raise ValueError(f"Output validation failed: Null values found in {col}")
            
    # Check range [0, 1]
    for col in rel_cols:
        if (df[col] < -1e-9).any() or (df[col] > 1.0 + 1e-9).any():
            raise ValueError(f"Output validation failed: Values in {col} outside [0, 1] range")
            
    print(f"Validation passed: {len(df)} rows, {len(rel_cols)} relative power columns.")

def main():
    """
    Main entry point for T015.
    """
    parser = argparse.ArgumentParser(description="Compute relative band power features.")
    parser.add_argument("--input", type=str, default=None, help="Path to features_raw.csv")
    parser.add_argument("--output", type=str, default=None, help="Path to features.csv")
    args = parser.parse_args()
    
    # Load config for paths if not provided
    config = load_config()
    input_path = Path(args.input) if args.input else get_path('features_raw')
    output_path = Path(args.output) if args.output else get_path('features')
    
    print(f"Loading raw features from: {input_path}")
    df_raw = load_raw_features(input_path)
    
    print(f"Computing relative power...")
    df_rel = compute_relative_power(df_raw)
    
    print("Validating output...")
    validate_output(df_rel)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save result
    df_rel.to_csv(output_path, index=False)
    print(f"Saved relative power features to: {output_path}")
    
    # Print summary
    print(f"Summary statistics for relative power:")
    print(df_rel[[f"rel_{b}" for b in BANDS_TO_NORMALIZE]].describe())

if __name__ == "__main__":
    main()
