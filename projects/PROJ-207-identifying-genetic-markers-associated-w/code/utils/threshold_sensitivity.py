"""
Threshold Sensitivity Analysis for GWAS Results.

This module implements a sensitivity sweep across p-value and q-value thresholds
to determine the robustness of genetic associations found in the GWAS pipeline.
It reads raw GWAS output, applies Benjamini-Hochberg FDR correction (via
utils.fdr_correction), and counts significant SNPs at various orders of magnitude.

Output: data/processed/threshold_sensitivity_report.tsv
"""
import os
import sys
import argparse
from pathlib import Path

import pandas as pd
import numpy as np

# Add project root to path to allow relative imports if run as script
# but rely on the provided API surface for specific functions.
# We assume the script is run from the project root or code/ directory.
# The API surface shows utils.fdr_correction exists.
try:
    from utils.fdr_correction import calculate_q_values
except ImportError:
    # Fallback for direct execution in some environments
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.fdr_correction import calculate_q_values

def generate_thresholds(base_p=1.0, min_order=-10, max_order=0, steps_per_order=5):
    """
    Generate a list of thresholds sweeping orders of magnitude.
    
    Args:
        base_p: Base p-value (usually 1.0 or 0.05 depending on logic, here we sweep 1e-10 to 1.0)
        min_order: Minimum exponent (e.g., -10 for 1e-10)
        max_order: Maximum exponent (e.g., 0 for 1e0 = 1.0)
        steps_per_order: Number of steps between each order of magnitude.
    
    Returns:
        List of float thresholds sorted ascending.
    """
    thresholds = []
    for exp in range(min_order, max_order + 1):
        # Generate steps between 10^exp and 10^(exp+1)
        # Using log-spaced steps for better coverage of orders of magnitude
        if exp == max_order:
            continue
        
        # Linear steps in log space
        for i in range(steps_per_order):
            val = 10 ** (exp + (i + 1) / steps_per_order)
            thresholds.append(val)
    
    # Ensure we cover the upper bound if needed, though 1.0 is usually implicit
    thresholds.append(1.0)
    
    # Sort and remove duplicates
    thresholds = sorted(list(set(thresholds)))
    return thresholds

def run_sensitivity_analysis(input_path, output_path):
    """
    Perform threshold sensitivity sweep and write report.
    
    Args:
        input_path: Path to the raw GWAS TSV (e.g., data/interim/gwas_raw.tsv)
        output_path: Path to write the sensitivity report TSV.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input GWAS file not found: {input_file}")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load GWAS results
    # Expected columns: SNP, P, ... (and potentially others)
    # We need at least the P-value column.
    df = pd.read_csv(input_file, sep='\t')
    
    if 'P' not in df.columns:
        raise ValueError(f"Input file {input_file} must contain a 'P' column.")
    
    # Calculate Q-values using the existing FDR module
    # The fdr_correction module expects a dataframe or series of p-values
    # and returns a dataframe with q-values appended.
    # We pass the P column.
    try:
        df_with_q = calculate_q_values(df)
    except Exception as e:
        raise RuntimeError(f"Failed to calculate q-values: {e}")
    
    if 'Q' not in df_with_q.columns:
        raise ValueError("FDR correction did not produce a 'Q' column.")
    
    # Generate thresholds
    # We sweep P and Q thresholds from 1e-10 to 1.0
    p_thresholds = generate_thresholds(min_order=-10, max_order=0, steps_per_order=10)
    q_thresholds = generate_thresholds(min_order=-10, max_order=0, steps_per_order=10)
    
    # Combine unique thresholds for a comprehensive sweep
    all_thresholds = sorted(list(set(p_thresholds + q_thresholds)))
    
    results = []
    
    for thresh in all_thresholds:
        # Count significant SNPs at this threshold for P
        sig_p = (df_with_q['P'] <= thresh).sum()
        
        # Count significant SNPs at this threshold for Q
        sig_q = (df_with_q['Q'] <= thresh).sum()
        
        results.append({
            'threshold': thresh,
            'significant_snps_p': sig_p,
            'significant_snps_q': sig_q
        })
    
    results_df = pd.DataFrame(results)
    
    # Sort by threshold
    results_df = results_df.sort_values('threshold')
    
    # Write output
    results_df.to_csv(output_file, sep='\t', index=False)
    
    print(f"Sensitivity analysis complete. Report written to: {output_file}")
    print(f"Total thresholds tested: {len(all_thresholds)}")
    print(f"Max significant SNPs (P < 1e-8): {results_df[results_df['threshold'] <= 1e-8]['significant_snps_p'].max()}")

def main():
    parser = argparse.ArgumentParser(
        description="Run threshold sensitivity sweep on GWAS results."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="data/interim/gwas_raw.tsv",
        help="Path to the raw GWAS TSV file (default: data/interim/gwas_raw.tsv)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/processed/threshold_sensitivity_report.tsv",
        help="Path to write the sensitivity report TSV (default: data/processed/threshold_sensitivity_report.tsv)"
    )
    
    args = parser.parse_args()
    
    try:
        run_sensitivity_analysis(args.input, args.output)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Data Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
