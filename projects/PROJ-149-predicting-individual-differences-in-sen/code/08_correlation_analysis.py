"""
T020: Implement Pearson correlation tests between relative band powers and median RT.

This script reads data/processed/features.csv (produced by T015),
computes Pearson correlations for each relative band power against median RT,
applies Bonferroni correction (alpha = 0.05 / 6 bands),
and writes the results to data/processed/correlations.csv.

Dependencies:
- data/processed/features.csv (from T015)
- code/config.py (for paths and seed)
- code/utils/stats_helpers.py (for bonferroni_correct)
"""
import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, get_seed, load_config
from utils.stats_helpers import bonferroni_correct

def load_features(filepath: str) -> pd.DataFrame:
    """Load the features CSV and validate basic structure."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Features file not found: {filepath}")
    
    df = pd.read_csv(filepath)
    
    required_cols = ['participant_id', 'median_rt']
    band_cols = ['delta_rel', 'theta_rel', 'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    
    missing = [c for c in required_cols + band_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in features file: {missing}")
    
    # Drop rows with NaN in relevant columns
    df = df.dropna(subset=required_cols + band_cols)
    
    if df.empty:
        raise ValueError("No valid data rows remaining after dropping NaNs.")
        
    return df

def run_correlations(df: pd.DataFrame, bands: list) -> pd.DataFrame:
    """
    Compute Pearson correlation between each band power and median RT.
    
    Returns a DataFrame with columns:
    - band: band name
    - r: correlation coefficient
    - p_raw: raw p-value
    - p_corrected: Bonferroni-corrected p-value
    - significant: boolean (corrected p < 0.05)
    """
    y = df['median_rt'].values
    results = []
    
    for band in bands:
        x = df[band].values
        
        # Compute Pearson correlation
        r, p_raw = stats.pearsonr(x, y)
        
        results.append({
            'band': band,
            'r': r,
            'p_raw': p_raw,
            'n': len(x)
        })
    
    res_df = pd.DataFrame(results)
    
    # Apply Bonferroni correction
    # We correct for the number of bands tested
    p_corrected = bonferroni_correct(res_df['p_raw'].tolist(), len(bands))
    res_df['p_corrected'] = p_corrected
    res_df['significant'] = res_df['p_corrected'] < 0.05
    
    return res_df

def main():
    parser = argparse.ArgumentParser(description="Run Pearson correlations between band powers and RT.")
    parser.add_argument('--input', type=str, default=None, help='Path to features CSV (default: from config)')
    parser.add_argument('--output', type=str, default=None, help='Path to output CSV (default: from config)')
    args = parser.parse_args()

    # Set random seed for reproducibility (though Pearson is deterministic)
    cfg = load_config()
    seed = get_seed()
    
    # Determine paths
    input_path = args.input or get_path('features_processed')
    output_path = args.output or get_path('correlations')
    
    print(f"Loading features from: {input_path}")
    df = load_features(input_path)
    print(f"Loaded {len(df)} participants.")

    # Define bands to test (relative power)
    bands = ['delta_rel', 'theta_rel', 'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    
    print(f"Running Pearson correlations for {len(bands)} bands against median RT...")
    results_df = run_correlations(df, bands)
    
    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_df.to_csv(output_path, index=False)
    print(f"Correlation results saved to: {output_path}")
    
    # Print summary
    print("\n--- Correlation Summary ---")
    print(results_df.to_string(index=False))
    
    sig_count = results_df['significant'].sum()
    print(f"\nSignificant correlations (Bonferroni-corrected p < 0.05): {sig_count}/{len(bands)}")

if __name__ == '__main__':
    main()