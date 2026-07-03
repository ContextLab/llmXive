"""
code/utils/fdr_correction.py
Implements Benjamini-Hochberg FDR correction for GWAS results.

Features:
- Calculates q-values from raw p-values.
- Flags SNPs with q-value < threshold as significant.
- Prepend mandatory disclaimer text to the output file header.
- Documents the correction method used.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def calculate_q_values(p_values: pd.Series) -> pd.Series:
    """
    Calculate q-values using the Benjamini-Hochberg procedure.
    
    Args:
        p_values: Series of raw p-values (must be sorted by p-value ascending).
    
    Returns:
        Series of q-values aligned with the input index.
    """
    # Ensure we are working with a copy to avoid modifying original
    p = p_values.sort_values()
    n = len(p)
    if n == 0:
        return pd.Series([], dtype=float)
    
    # BH procedure: q_i = p_i * n / i
    # where i is the rank (1-indexed)
    ranks = np.arange(1, n + 1)
    q_values = (p.values * n) / ranks
    
    # Ensure monotonicity: q_i <= q_{i+1}
    # We iterate backwards to enforce this
    for i in range(n - 2, -1, -1):
        if q_values[i] > q_values[i + 1]:
            q_values[i] = q_values[i + 1]
    
    # Cap values at 1.0
    q_values = np.minimum(q_values, 1.0)
    
    # Re-index to match original input order
    result = pd.Series(q_values, index=p.index)
    return result.sort_index() # Return in original order of input series

def apply_fdr_correction(
    df: pd.DataFrame, 
    p_col: str = "P", 
    q_col: str = "Q", 
    sig_col: str = "significant",
    threshold: float = 0.05
) -> pd.DataFrame:
    """
    Apply FDR correction to a DataFrame containing GWAS results.
    
    Args:
        df: DataFrame with GWAS results.
        p_col: Name of the column containing raw p-values.
        q_col: Name of the column for the calculated q-values.
        sig_col: Name of the column for the significance flag.
        threshold: The q-value threshold for significance.
    
    Returns:
        DataFrame with added q-value and significance columns.
    """
    if p_col not in df.columns:
        raise ValueError(f"P-value column '{p_col}' not found in dataframe. Columns: {df.columns.tolist()}")
    
    # Calculate q-values
    df[q_col] = calculate_q_values(df[p_col])
    
    # Flag significance
    df[sig_col] = df[q_col] < threshold
    
    return df

def write_output_with_disclaimer(
    df: pd.DataFrame, 
    output_path: Path, 
    disclaimer: str, 
    method: str
) -> None:
    """
    Write the DataFrame to a TSV file, prepending the mandatory disclaimer
    and method documentation as comment lines.
    
    Args:
        df: The processed DataFrame.
        output_path: Path to the output file.
        disclaimer: The mandatory disclaimer text.
        method: Description of the correction method used.
    """
    # Prepare header comments
    header_lines = [
        f"# WARNING: {disclaimer}",
        f"# Correction Method: {method}",
        f"# Significance Threshold: q < 0.05",
        f"# This file contains SNPs flagged as significant based on the Benjamini-Hochberg procedure."
    ]
    
    # Write comments first
    with open(output_path, 'w') as f:
        for line in header_lines:
            f.write(line + '\n')
    
    # Append the TSV data
    df.to_csv(output_path, sep='\t', index=False, mode='a')

def main():
    parser = argparse.ArgumentParser(description="Apply FDR correction to GWAS results")
    parser.add_argument("--input", type=str, required=True, help="Input TSV file (raw GWAS results)")
    parser.add_argument("--output", type=str, required=True, help="Output TSV file (FDR corrected)")
    parser.add_argument("--disclaimer", type=str, required=True, help="Mandatory disclaimer text")
    parser.add_argument("--threshold", type=float, default=0.05, help="Q-value threshold for significance")
    parser.add_argument("--method", type=str, default="Benjamini-Hochberg (BH)", help="Description of correction method")
    parser.add_argument("--p-col", type=str, default="P", help="Column name for p-values")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)
    
    # Read data
    try:
        df = pd.read_csv(input_path, sep='\t')
    except Exception as e:
        print(f"ERROR: Failed to read input file: {e}")
        sys.exit(1)
    
    # Apply correction
    df = apply_fdr_correction(
        df, 
        p_col=args.p_col, 
        q_col="Q", 
        sig_col="significant", 
        threshold=args.threshold
    )
    
    # Write output with disclaimer
    write_output_with_disclaimer(df, output_path, args.disclaimer, args.method)
    
    # Print summary
    total_snps = len(df)
    significant_snps = df["significant"].sum()
    print(f"Processed {total_snps} SNPs.")
    print(f"Significant SNPs (q < {args.threshold}): {significant_snps}")

if __name__ == "__main__":
    main()