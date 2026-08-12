"""
Correlation Analysis (Task T020)

Implements Pearson correlation tests between relative band powers (CLR-transformed)
and median reaction times (RT) as per FR-006.

Input: data/processed/features.csv (output of T015)
Output: data/processed/correlations.csv (contains r, p-value, and Bonferroni flag)

Dependencies: T016 (features.csv validation)
"""
import os
import sys
import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from config import get_path, get_all_band_names, get_seed
from utils.stats_helpers import bonferroni_correct

def load_features():
    """
    Load the processed features CSV.
    Expects columns: participant_id, median_rt, delta, theta, alpha, low_beta, high_beta, gamma
    (or similar band names as defined in config).
    """
    path = get_path("processed", "features.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Input file not found: {path}. "
            "Ensure T015 (05_compute_relative_power.py) has completed successfully."
        )
    
    df = pd.read_csv(path)
    
    # Validate required columns
    required_cols = ["participant_id", "median_rt"]
    band_names = get_all_band_names()
    required_cols.extend(band_names)
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in features.csv: {missing}")
    
    # Drop rows with any NaN in relevant columns to ensure valid correlation
    cols_to_check = ["median_rt"] + band_names
    df_clean = df.dropna(subset=cols_to_check)
    
    if len(df_clean) == 0:
        raise ValueError("No valid data rows remaining after dropping NaNs.")
    
    return df_clean, band_names

def run_correlations(df, band_names):
    """
    Compute Pearson correlation between each band power and median RT.
    
    Returns a DataFrame with:
    - band: band name
    - r: Pearson correlation coefficient
    - p_value: raw p-value
    - significant: boolean (raw p < 0.05)
    """
    results = []
    
    rt = df["median_rt"].values
    
    for band in band_names:
        x = df[band].values
        
        # Compute Pearson correlation
        r, p_val = stats.pearsonr(x, rt)
        
        results.append({
            "band": band,
            "r": r,
            "p_value": p_val,
            "n": len(rt),
            "significant_raw": p_val < 0.05
        })
    
    return pd.DataFrame(results)

def apply_bonferroni_flag(df_results):
    """
    Apply Bonferroni correction for 6 bands (0.05 / 6 = 0.00833).
    Adds 'significant_bonferroni' column.
    """
    n_bands = len(df_results)
    alpha = 0.05
    threshold = alpha / n_bands
    
    df_results["bonferroni_threshold"] = threshold
    df_results["significant_bonferroni"] = df_results["p_value"] < threshold
    
    return df_results

def save_results(df_results, output_path):
    """
    Save the correlation results to CSV.
    """
    df_results.to_csv(output_path, index=False)
    print(f"Correlation results saved to: {output_path}")
    
    # Print summary to stdout
    print("\n--- Correlation Summary ---")
    print(f"Total bands tested: {len(df_results)}")
    print(f"Bonferroni threshold: {df_results['bonferroni_threshold'].iloc[0]:.4f}")
    significant_count = df_results["significant_bonferroni"].sum()
    print(f"Significant correlations (Bonferroni corrected): {significant_count}")
    
    if significant_count > 0:
        print("\nSignificant bands:")
        sig_bands = df_results[df_results["significant_bonferroni"]]
        print(sig_bands[["band", "r", "p_value", "significant_bonferroni"]].to_string(index=False))
    else:
        print("\nNo bands passed Bonferroni correction.")

def main():
    parser = argparse.ArgumentParser(
        description="Compute Pearson correlations between EEG band powers and median RT."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to features.csv (overrides config if provided)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output correlations.csv (overrides config if provided)"
    )
    args = parser.parse_args()

    # Load data
    print("Loading features...")
    df_features, band_names = load_features()
    print(f"Loaded {len(df_features)} participants.")

    # Run correlations
    print("Computing Pearson correlations...")
    corr_df = run_correlations(df_features, band_names)

    # Apply Bonferroni
    corr_df = apply_bonferroni_flag(corr_df)

    # Determine output path
    output_path = args.output or get_path("processed", "correlations.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save results
    save_results(corr_df, output_path)

    return 0

if __name__ == "__main__":
    from scipy import stats
    sys.exit(main())