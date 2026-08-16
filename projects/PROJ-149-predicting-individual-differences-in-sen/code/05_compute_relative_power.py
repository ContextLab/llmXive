"""
T015: Compute Relative Power Features
======================================
Calculates relative power (band_power / total_power) from raw PSD values.
Input: data/interim/eeg_psd.csv
Output: data/processed/features.csv
"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path to allow config import
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, get_band_freqs, get_all_band_names, bonferroni_correct, get_exclusion_params
from utils.stats_helpers import bonferroni_correct as stats_bonferroni

def load_raw_features(input_path: str) -> pd.DataFrame:
    """Load the raw PSD features computed in T012."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                                "Please ensure T012 (03_extract_features.py) has run successfully.")
    df = pd.read_csv(input_path)
    required_cols = ['participant_id', 'delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
    return df

def load_behavioral_metrics(input_path: str) -> pd.DataFrame:
    """Load behavioral metrics to merge with features."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Behavioral metrics file not found: {input_path}. "
                                "Please ensure T013 (04_extract_behavioral_metrics.py) has run successfully.")
    return pd.read_csv(input_path)

def compute_relative_power(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate relative power for each band: band_power / total_power.
    Total power is the sum of all band powers (delta + theta + alpha + low_beta + high_beta + gamma).
    Handles zero total power by adding a small epsilon to avoid division by zero.
    """
    df = df_raw.copy()
    
    # Define band columns
    band_cols = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    
    # Calculate total power across all bands
    # Use the sum of the specific bands as the proxy for total power in the 1-40Hz range
    # as per FR-010 (band/total)
    total_power = df[band_cols].sum(axis=1)
    
    # Get epsilon from config to handle zero division
    epsilon = get_exclusion_params().get('epsilon', 1e-10)
    
    # Calculate relative power
    for band in band_cols:
        relative_col = f'{band}_rel'
        df[relative_col] = df[band] / (total_power + epsilon)
    
    return df

def validate_output(df: pd.DataFrame) -> bool:
    """Validate that the output file contains no nulls and correct columns."""
    rel_cols = [f'{b}_rel' for b in ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']]
    
    # Check for nulls in relative power columns
    for col in rel_cols:
        if col not in df.columns:
            raise ValueError(f"Output missing relative column: {col}")
        if df[col].isnull().any():
            raise ValueError(f"Output contains nulls in column: {col}")
    
    # Check for valid range (0 to 1)
    for col in rel_cols:
        if (df[col] < 0).any() or (df[col] > 1).any():
            # Allow small floating point errors, but warn if out of range significantly
            if ((df[col] < -0.01) | (df[col] > 1.01)).any():
                raise ValueError(f"Relative power values out of expected range [0, 1] in {col}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Compute relative power features (T015)")
    parser.add_argument('--input-psd', type=str, default=None,
                        help="Path to raw PSD CSV (default: auto-detect)")
    parser.add_argument('--input-behavioral', type=str, default=None,
                        help="Path to behavioral metrics CSV (default: auto-detect)")
    parser.add_argument('--output', type=str, default=None,
                        help="Path to output features CSV (default: auto-detect)")
    args = parser.parse_args()

    # Resolve paths
    if args.input_psd is None:
        input_psd = get_path('interim', 'eeg_psd.csv')
    else:
        input_psd = args.input_psd

    if args.input_behavioral is None:
        input_behavioral = get_path('interim', 'behavioral_metrics.csv')
    else:
        input_behavioral = args.input_behavioral

    if args.output is None:
        output_path = get_path('processed', 'features.csv')
    else:
        output_path = args.output

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading raw PSD features from: {input_psd}")
    df_raw = load_raw_features(input_psd)

    print(f"Loading behavioral metrics from: {input_behavioral}")
    df_behav = load_behavioral_metrics(input_behavioral)

    # Merge on participant_id
    # Inner join to ensure we only have participants with both EEG and Behavioral data
    if 'participant_id' not in df_behav.columns:
        raise ValueError("Behavioral metrics file missing 'participant_id' column")
    
    df_merged = pd.merge(df_raw, df_behav[['participant_id', 'median_rt']], on='participant_id', how='inner')
    
    if df_merged.empty:
        raise RuntimeError("No matching participants found between EEG PSD and Behavioral metrics.")

    print(f"Merged dataset size: {len(df_merged)} participants")

    print("Computing relative power (band / total)...")
    df_features = compute_relative_power(df_merged)

    # Validate output
    print("Validating output...")
    validate_output(df_features)

    # Save to CSV
    print(f"Saving features to: {output_path}")
    df_features.to_csv(output_path, index=False)

    print("T015 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())