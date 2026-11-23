"""
T020: Benjamini-Hochberg FDR Correction Utility
Applies FDR correction to GWAS results.

This module implements the Benjamini-Hochberg procedure for controlling the False
Discovery Rate in multiple hypothesis testing, specifically for GWAS p-values.
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
    
    Implements the BH procedure:
    1. Sort p-values: p(1) <= p(2) <= ... <= p(m)
    2. Calculate q(i) = (m/i) * p(i)
    3. Enforce monotonicity: q(i) = min(q(i), q(i+1), ..., q(m))
    
    Args:
        p_values: Array-like of p-values.
        
    Returns:
        numpy array of q-values in the original order.
    """
    p_values = np.array(p_values, dtype=float)
    n = len(p_values)
    if n == 0:
        return np.array([])
    
    # Handle NaN values by replacing them with 1.0 (non-significant)
    # This ensures the sorting and calculation proceed without errors
    has_nan = np.isnan(p_values)
    if np.any(has_nan):
        p_values_clean = p_values.copy()
        p_values_clean[has_nan] = 1.0
    else:
        p_values_clean = p_values
    
    # Sort P-values
    sorted_indices = np.argsort(p_values_clean)
    sorted_p = p_values_clean[sorted_indices]
    
    # Calculate BH adjusted p-values (q-values)
    # q_i = (n / rank) * p_i
    # Rank starts at 1 for the smallest p-value
    rank = np.arange(1, n + 1)
    q_values = (n / rank) * sorted_p
    
    # Cap at 1.0
    q_values = np.minimum(q_values, 1.0)
    
    # Enforce monotonicity (cumulative min from the end)
    # q(i) = min(q(i), q(i+1), ..., q(m))
    for i in range(n - 2, -1, -1):
        if q_values[i] > q_values[i+1]:
            q_values[i] = q_values[i+1]
    
    # Restore original order
    q_values_final = np.zeros(n)
    q_values_final[sorted_indices] = q_values
    
    # Restore NaN positions if any existed
    if np.any(has_nan):
        q_values_final[has_nan] = np.nan
    
    return q_values_final

def apply_fdr_correction(df):
    """
    Apply FDR correction to a DataFrame with a 'P' column.
    Adds a 'q_value' column.
    
    Args:
        df: pandas DataFrame containing GWAS results with a 'P' column.
        
    Returns:
        DataFrame with an added 'q_value' column.
        
    Raises:
        ValueError: If 'P' column is missing.
    """
    if 'P' not in df.columns:
        raise ValueError("Input DataFrame must contain a 'P' column.")
    
    df = df.copy()
    df['q_value'] = calculate_q_values(df['P'].values)
    return df

def write_output_with_disclaimer(input_path, output_path):
    """
    Read GWAS raw results, apply FDR, write with disclaimer.
    
    Reads the input TSV, applies Benjamini-Hochberg correction,
    flags significant SNPs (q < 0.05), and writes the output.
    
    Args:
        input_path: Path to raw GWAS TSV (e.g., data/interim/gwas_raw.tsv).
        output_path: Path to write FDR-corrected TSV.
        
    Returns:
        The processed DataFrame.
    """
    # Read input
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    df = pd.read_csv(input_path, sep='\t')
    
    # Validate required columns
    required_cols = ['SNP', 'P']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input file missing required columns: {missing}")
    
    # Apply correction
    df = apply_fdr_correction(df)
    
    # Significance flag
    df['significant'] = df['q_value'] < 0.05
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write output
    # Note: T023 requires a separate metadata file for disclaimers.
    # This file contains only clean data.
    df.to_csv(output_path, sep='\t', index=False)
    
    print(f"FDR correction complete. Output written to {output_path}")
    print(f"Total SNPs: {len(df)}")
    print(f"Significant (q < 0.05): {df['significant'].sum()}")
    return df

def main():
    """
    CLI entry point for FDR correction.
    """
    parser = argparse.ArgumentParser(
        description="Apply Benjamini-Hochberg FDR correction to GWAS results"
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="Path to raw GWAS TSV (e.g., data/interim/gwas_raw.tsv)"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Path to output FDR-corrected TSV"
    )
    args = parser.parse_args()
    
    try:
        write_output_with_disclaimer(args.input, args.output)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during FDR correction: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()