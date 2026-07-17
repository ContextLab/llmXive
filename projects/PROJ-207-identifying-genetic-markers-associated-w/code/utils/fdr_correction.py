"""
T020: Benjamini-Hochberg FDR Correction Utility
Applies FDR correction to GWAS results.
"""
import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def calculate_q_values(p_values):
    """
    Calculate Benjamini-Hochberg q-values.
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return np.array([])
    
    # Sort P-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values (q-values)
    # q_i = min( (n/i) * p_i, 1 )
    # But we need to enforce monotonicity: q_i = min( q_i, q_{i+1} ) from bottom up
    
    rank = np.arange(1, n + 1)
    q_values = (n / rank) * sorted_p
    q_values = np.minimum(q_values, 1.0)
    
    # Enforce monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i+1])
    
    # Restore original order
    q_values_final = np.zeros(n)
    q_values_final[sorted_indices] = q_values
    
    return q_values_final

def apply_fdr_correction(df):
    """
    Apply FDR correction to a DataFrame with a 'P' column.
    Adds a 'q_value' column.
    """
    if 'P' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'P' column.")
    
    df = df.copy()
    df['q_value'] = calculate_q_values(df['P'].values)
    return df

def write_output_with_disclaimer(input_path, output_path):
    """
    Read GWAS raw results, apply FDR, write with disclaimer.
    """
    # Read input
    df = pd.read_csv(input_path, sep='\t')
    
    # Apply correction
    df = apply_fdr_correction(df)
    
    # Significance flag
    df['significant'] = df['q_value'] < 0.05
    
    # Write output
    # The task T022 requires the output to be written to data/processed/gwas_results_fdr.tsv
    # and to include the disclaimer. Since the output is a TSV, we can prepend the disclaimer
    # as a comment line at the top.
    
    with open(output_path, 'w') as f:
        f.write("# Disclaimer: Findings are associational, not causal. Further validation required.\n")
        f.write("# Method: Benjamini-Hochberg FDR correction.\n")
        df.to_csv(f, sep='\t', index=False)
    
    print(f"FDR correction complete. Output written to {output_path}")
    return df

def main():
    parser = argparse.ArgumentParser(description="Apply FDR correction to GWAS results")
    parser.add_argument("--input", required=True, help="Path to raw GWAS TSV (e.g., data/interim/gwas_raw.tsv)")
    parser.add_argument("--output", required=True, help="Path to output FDR-corrected TSV")
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    write_output_with_disclaimer(args.input, args.output)

if __name__ == "__main__":
    main()
