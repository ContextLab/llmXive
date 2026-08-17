"""
T020: Implement Pearson correlation tests between CLR-transformed relative band powers and median RT.

This script computes Pearson correlation coefficients and p-values between
each EEG band power feature (delta, theta, alpha, low_beta, high_beta, gamma)
and the median reaction time (RT) for each participant.

It also applies Bonferroni correction for multiple comparisons (6 bands).

Input: data/processed/features_clr.csv
Output: data/processed/correlations.csv
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Add parent directory to path for imports if running as script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_path, ensure_dirs, bonferroni_correct


def load_features():
    """Load the CLR-transformed features dataset."""
    features_path = get_path("processed", "features_clr.csv")
    if not os.path.exists(features_path):
        raise FileNotFoundError(
            f"Features file not found: {features_path}. "
            "Run T015 (05_compute_relative_power.py) first."
        )
    
    df = pd.read_csv(features_path)
    
    # Expected columns
    required_cols = ['participant_id', 'median_rt', 'delta', 'theta', 'alpha', 
                    'low_beta', 'high_beta', 'gamma']
    
    missing = set(required_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in features file: {missing}")
    
    return df


def run_correlations(df):
    """
    Compute Pearson correlations between each band power and median RT.
    
    Args:
        df: DataFrame with columns ['participant_id', 'median_rt', 'delta', 
            'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    
    Returns:
        DataFrame with correlation results
    """
    band_cols = ['delta', 'theta', 'alpha', 'low_beta', 'high_beta', 'gamma']
    
    results = []
    
    for band in band_cols:
        # Remove any rows with NaN in the band or RT
        valid_mask = df[[band, 'median_rt']].notna().all(axis=1)
        valid_df = df.loc[valid_mask, [band, 'median_rt']]
        
        if len(valid_df) < 3:
            # Not enough data points for correlation
            results.append({
                'band': band,
                'n': len(valid_df),
                'r': np.nan,
                'p_value': np.nan,
                'ci_low': np.nan,
                'ci_high': np.nan
            })
            continue
        
        # Compute Pearson correlation
        r, p_value = stats.pearsonr(valid_df[band], valid_df['median_rt'])
        
        # Compute 95% confidence interval for r using Fisher's z-transformation
        # z = 0.5 * ln((1+r)/(1-r))
        # SE = 1/sqrt(n-3)
        # CI_z = z +/- 1.96 * SE
        # CI_r = (exp(2*CI_z) - 1) / (exp(2*CI_z) + 1)
        
        if abs(r) < 0.9999:  # Avoid division by zero for perfect correlations
            z = 0.5 * np.log((1 + r) / (1 - r))
            se = 1 / np.sqrt(len(valid_df) - 3)
            z_low = z - 1.96 * se
            z_high = z + 1.96 * se
            ci_low = (np.exp(2 * z_low) - 1) / (np.exp(2 * z_low) + 1)
            ci_high = (np.exp(2 * z_high) - 1) / (np.exp(2 * z_high) + 1)
        else:
            # Perfect correlation - CI is just the value itself
            ci_low = ci_high = r
        
        results.append({
            'band': band,
            'n': len(valid_df),
            'r': r,
            'p_value': p_value,
            'ci_low': ci_low,
            'ci_high': ci_high
        })
    
    return pd.DataFrame(results)


def apply_bonferroni_flag(results_df):
    """
    Apply Bonferroni correction and flag significant results.
    
    Args:
        results_df: DataFrame with correlation results including p_value column
    
    Returns:
        DataFrame with additional 'bonferroni_p' and 'significant' columns
    """
    n_bands = len(results_df)
    alpha = 0.05
    
    # Bonferroni corrected p-value threshold
    corrected_alpha = bonferroni_correct(alpha, n_bands)
    
    # Calculate corrected p-values (multiply by number of tests)
    results_df['bonferroni_p'] = results_df['p_value'] * n_bands
    # Cap at 1.0
    results_df['bonferroni_p'] = results_df['bonferroni_p'].clip(upper=1.0)
    
    # Flag significant results at corrected alpha
    results_df['significant'] = results_df['bonferroni_p'] < corrected_alpha
    
    return results_df, corrected_alpha


def save_results(results_df, corrected_alpha, output_path):
    """Save correlation results to CSV."""
    # Ensure output directory exists
    ensure_dirs(output_path.parent)
    
    # Add metadata to the file
    results_df.to_csv(output_path, index=False)
    
    # Also save a summary JSON with the correction info
    summary = {
        'n_bands': len(results_df),
        'alpha': 0.05,
        'bonferroni_corrected_alpha': corrected_alpha,
        'n_significant': results_df['significant'].sum(),
        'output_file': str(output_path)
    }
    
    summary_path = output_path.with_suffix('.json')
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary


def main():
    """Main entry point for the correlation analysis."""
    parser = argparse.ArgumentParser(
        description='Compute Pearson correlations between EEG band powers and median RT'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output path for correlations CSV (default: data/processed/correlations.csv)'
    )
    
    args = parser.parse_args()
    
    print("Loading CLR-transformed features...")
    df = load_features()
    print(f"Loaded {len(df)} participants")
    
    print("Running Pearson correlations...")
    results_df = run_correlations(df)
    
    print("Applying Bonferroni correction...")
    results_df, corrected_alpha = apply_bonferroni_flag(results_df)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_path("processed", "correlations.csv")
    
    print(f"Saving results to {output_path}...")
    summary = save_results(results_df, corrected_alpha, output_path)
    
    # Print summary
    print("\n" + "="*60)
    print("CORRELATION ANALYSIS RESULTS (T020)")
    print("="*60)
    print(f"Bonferroni corrected alpha: {corrected_alpha:.4f}")
    print(f"Number of significant correlations: {summary['n_significant']}/{summary['n_bands']}")
    print("-"*60)
    print(f"{'Band':<12} {'r':>8} {'p-value':>10} {'Bonf_p':>10} {'Signif?':>8}")
    print("-"*60)
    
    for _, row in results_df.iterrows():
        sig = "Yes" if row['significant'] else "No"
        print(f"{row['band']:<12} {row['r']:>8.4f} {row['p_value']:>10.4f} "
              f"{row['bonferroni_p']:>10.4f} {sig:>8}")
    
    print("="*60)
    print(f"Results saved to: {output_path}")
    print(f"Summary saved to: {output_path.with_suffix('.json')}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())