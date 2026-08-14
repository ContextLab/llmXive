"""
T021: Apply Bonferroni correction to correlation results.

This script takes the correlation results from T020 and applies Bonferroni
correction for 6 bands (0.05/6 = 0.0083) as per Spec FR-006.

Output: data/processed/bonferroni_results.csv
"""

import os
import sys
import argparse
import pandas as pd
from pathlib import Path

from config import get_path, ensure_dirs

def load_correlations():
    """Load raw correlation results."""
    # Try to find the correlations file
    processed_dir = get_path("data/processed")
    if os.path.exists(processed_dir):
        for f in os.listdir(processed_dir):
            if f.startswith("correlations") and f.endswith(".csv"):
                return pd.read_csv(os.path.join(processed_dir, f))
    
    # Try interim directory
    interim_dir = get_path("data/interim")
    if os.path.exists(interim_dir):
        for f in os.listdir(interim_dir):
            if f.startswith("correlations") and f.endswith(".csv"):
                return pd.read_csv(os.path.join(interim_dir, f))
    
    raise FileNotFoundError("Could not find correlation results file")

def apply_bonferroni_correction(df, alpha=0.05, n_tests=6):
    """Apply Bonferroni correction to p-values."""
    corrected_alpha = alpha / n_tests
    df['bonferroni_corrected'] = df['p_value'] < corrected_alpha
    df['corrected_alpha'] = corrected_alpha
    return df

def save_corrected_results(df, output_path):
    """Save Bonferroni corrected results."""
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    print(f"Saved Bonferroni corrected results to {output_path}")

def main():
    """Main function to apply Bonferroni correction."""
    parser = argparse.ArgumentParser(description="Apply Bonferroni correction to correlation results")
    parser.add_argument("--input", type=str, default=None,
                      help="Input path for correlations CSV")
    parser.add_argument("--output", type=str, default=None,
                      help="Output path for Bonferroni results CSV (default: data/processed/bonferroni_results.csv)")
    parser.add_argument("--alpha", type=float, default=0.05,
                      help="Significance level (default: 0.05)")
    parser.add_argument("--n-tests", type=int, default=6,
                      help="Number of tests for Bonferroni correction (default: 6)")
    args = parser.parse_args()
    
    # Determine input path
    if args.input:
        input_path = args.input
    else:
        # Try to find the file
        processed_dir = get_path("data/processed")
        if os.path.exists(processed_dir):
            for f in os.listdir(processed_dir):
                if f.startswith("correlations") and f.endswith(".csv"):
                    input_path = os.path.join(processed_dir, f)
                    break
        else:
            input_path = None
    
    if not input_path or not os.path.exists(input_path):
        print("Error: Could not find input correlations file")
        sys.exit(1)
    
    print(f"Loading correlations from {input_path}...")
    correlations_df = pd.read_csv(input_path)
    
    print(f"Applying Bonferroni correction (alpha={args.alpha}, n_tests={args.n_tests})...")
    corrected_df = apply_bonferroni_correction(correlations_df, args.alpha, args.n_tests)
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = get_path("data/processed", "bonferroni_results.csv")
    
    save_corrected_results(corrected_df, output_path)
    
    # Also save to the expected location for T025
    expected_output = get_path("data/processed", "correlations.csv")
    if output_path != expected_output:
        ensure_dirs(expected_output)
        corrected_df.to_csv(expected_output, index=False)
        print(f"Also saved to {expected_output}")
    
    print("Bonferroni correction completed.")

if __name__ == "__main__":
    main()
