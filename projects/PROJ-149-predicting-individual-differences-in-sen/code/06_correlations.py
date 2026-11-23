"""
T020: Implement Pearson correlation script (FR-006).

Reads features_clr.csv and computes Pearson correlation between each band's
relative power (CLR-transformed) and median reaction time.

Outputs: data/interim/correlations_raw.csv
"""
import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Add project root to path for config import
sys.path.insert(0, str(Path(__file__).parent))

from config import get_path, get_epsilon, get_all_band_names


def load_features_clr(input_path: str) -> pd.DataFrame:
    """Load CLR-transformed features dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    required_cols = ['participant_id', 'median_rt']
    band_cols = get_all_band_names()
    clr_band_cols = [f"{band}_clr" for band in band_cols]
    
    missing = [c for c in required_cols + clr_band_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    return df


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute Pearson correlation between each CLR-transformed band power
    and median reaction time.
    
    Returns DataFrame with columns: band, r_value, p_value, n
    """
    results = []
    band_cols = get_all_band_names()
    clr_band_cols = [f"{band}_clr" for band in band_cols]
    
    for band, clr_col in zip(band_cols, clr_band_cols):
        x = df[clr_col].values
        y = df['median_rt'].values
        
        # Filter out any NaN values
        valid_mask = ~(np.isnan(x) | np.isnan(y))
        x_valid = x[valid_mask]
        y_valid = y[valid_mask]
        n = len(x_valid)
        
        if n < 2:
            r_val = np.nan
            p_val = np.nan
        else:
            r_val, p_val = stats.pearsonr(x_valid, y_valid)
        
        results.append({
            'band': band,
            'r_value': r_val,
            'p_value': p_val,
            'n': n
        })
    
    return pd.DataFrame(results)


def save_results(df: pd.DataFrame, output_path: str) -> None:
    """Save correlation results to CSV."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"Saved correlation results to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Compute Pearson correlations between band power and RT')
    parser.add_argument('--input', type=str, default=None,
                      help='Path to features_clr.csv (default: from config)')
    parser.add_argument('--output', type=str, default=None,
                      help='Path to output CSV (default: from config)')
    args = parser.parse_args()
    
    # Determine input path
    if args.input:
        input_path = args.input
    else:
        input_path = get_path('data/processed/features_clr.csv')
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = get_path('data/interim/correlations_raw.csv')
    
    print(f"Loading features from {input_path}...")
    df = load_features_clr(input_path)
    print(f"Loaded {len(df)} participants")
    
    print("Computing Pearson correlations...")
    correlations_df = compute_correlations(df)
    
    print("Saving results...")
    save_results(correlations_df, output_path)
    
    # Print summary
    print("\nCorrelation Summary:")
    print(correlations_df.to_string(index=False))
    
    # Check for any significant correlations (raw p < 0.05)
    significant = correlations_df[correlations_df['p_value'] < 0.05]
    if len(significant) > 0:
        print(f"\nFound {len(significant)} raw significant correlations (p < 0.05):")
        print(significant.to_string(index=False))
    else:
        print("\nNo raw significant correlations found (p < 0.05).")


if __name__ == '__main__':
    main()