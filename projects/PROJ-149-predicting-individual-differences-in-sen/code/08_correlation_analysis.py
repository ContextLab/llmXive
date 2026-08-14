"""
T020: Calculate Pearson correlations between band powers and RT.

This script computes Pearson correlations between each band power feature
and median RT, then saves the results.

Output: data/processed/correlations.csv (intermediate)
"""

import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from scipy import stats

from config import get_path, ensure_dirs

def load_features():
    """Load features dataset."""
    path = get_path("data/processed", "features.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found at {path}")
    return pd.read_csv(path)

def run_correlations(df):
    """Run Pearson correlations for each band."""
    # Identify band columns
    band_cols = []
    for col in df.columns:
        if col.endswith('_clr') or col.endswith('_relative') or col in ['delta', 'theta', 'alpha', 'beta', 'gamma']:
            if col != 'median_rt' and col != 'participant_id':
                band_cols.append(col)
    
    if not band_cols:
        raise ValueError("No band power columns found in features")
    
    results = []
    for band in band_cols:
        x = df[band].values
        y = df['median_rt'].values
        
        # Remove NaNs
        mask = ~(np.isnan(x) | np.isnan(y))
        x_clean = x[mask]
        y_clean = y[mask]
        
        if len(x_clean) < 3:
            continue
        
        # Pearson correlation
        r, p = stats.pearsonr(x_clean, y_clean)
        
        results.append({
            'band': band,
            'r': r,
            'p_value': p,
            'n': len(x_clean)
        })
    
    return pd.DataFrame(results)

def apply_bonferroni_flag(df, alpha=0.05, n_tests=6):
    """Apply Bonferroni flag to results."""
    corrected_alpha = alpha / n_tests
    df['significant_bonferroni'] = df['p_value'] < corrected_alpha
    return df

def save_results(df, output_path):
    """Save correlation results."""
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    print(f"Saved correlations to {output_path}")

def main():
    """Main function for correlation analysis."""
    parser = argparse.ArgumentParser(description="Run correlation analysis")
    parser.add_argument("--output", type=str, default=None,
                      help="Output path for correlations CSV (default: data/processed/correlations.csv)")
    args = parser.parse_args()
    
    print("Loading features...")
    df = load_features()
    
    print("Running Pearson correlations...")
    correlations = run_correlations(df)
    
    print("Applying Bonferroni flag...")
    correlations = apply_bonferroni_flag(correlations)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = get_path("data/processed", "correlations.csv")
    
    save_results(correlations, output_path)
    
    # Also save interim version for Bonferroni script
    interim_output = get_path("data/processed", "raw_correlations.csv")
    ensure_dirs(interim_output)
    correlations.to_csv(interim_output, index=False)
    print(f"Also saved raw correlations to {interim_output}")
    
    print(f"Correlation analysis completed. Found {len(correlations)} correlations.")

if __name__ == "__main__":
    main()