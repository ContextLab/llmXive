import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def calculate_q_values(p_values: pd.Series) -> pd.Series:
    """
    Implements the Benjamini-Hochberg procedure to calculate q-values.
    
    Args:
        p_values: Series of p-values.
        
    Returns:
        Series of q-values.
    """
    n = len(p_values)
    if n == 0:
        return pd.Series([], dtype=float)
    
    # Sort p-values
    sorted_indices = p_values.argsort()
    sorted_p_values = p_values.iloc[sorted_indices]
    
    # Calculate BH q-values
    q_values = np.zeros(n)
    for i in range(n):
        rank = i + 1
        q_values[i] = sorted_p_values.iloc[i] * n / rank
    
    # Ensure monotonicity (q-values should be non-decreasing when sorted by p-value)
    # We process from largest p-value to smallest
    for i in range(n - 2, -1, -1):
        q_values[i] = min(q_values[i], q_values[i + 1])
    
    # Map back to original order
    result = pd.Series(np.zeros(n), index=p_values.index)
    result.iloc[sorted_indices] = q_values
    
    return result

def apply_fdr_correction(df: pd.DataFrame, p_col: str = 'P', q_col: str = 'Q') -> pd.DataFrame:
    """
    Applies FDR correction to a dataframe containing p-values.
    
    Args:
        df: DataFrame with p-values.
        p_col: Name of the column containing p-values.
        q_col: Name of the column for q-values.
        
    Returns:
        DataFrame with added q-values column.
    """
    if p_col not in df.columns:
        raise ValueError(f"Column '{p_col}' not found in DataFrame. Available columns: {df.columns.tolist()}")
    
    df[q_col] = calculate_q_values(df[p_col])
    return df

def write_output_with_disclaimer(df: pd.DataFrame, output_path: Path, p_col: str = 'P', q_col: str = 'Q'):
    """
    Writes the FDR-corrected results to a file, prepending the mandatory disclaimer.
    
    Args:
        df: DataFrame with results.
        output_path: Path to the output file.
        p_col: Name of the p-value column.
        q_col: Name of the q-value column.
    """
    # Flag significant SNPs
    df['significant'] = df[q_col] < 0.05
    
    # Create the disclaimer text
    disclaimer = (
        "# Findings are associational, not causal. "
        "This report applies the Benjamini-Hochberg (BH) FDR correction method. "
        "SNPs with q < 0.05 are flagged as significant. "
        "The BH method controls the expected proportion of false discoveries among the declared significant findings. "
        "Impact on discovery rate: The BH method is less stringent than Bonferroni, "
        "allowing for more discoveries while controlling the false discovery rate. "
        "However, it assumes independence or positive dependence among tests. "
        "In GWAS, linkage disequilibrium (LD) can violate this assumption, potentially affecting the actual FDR. "
        "Results should be interpreted with caution and validated in independent cohorts."
    )
    
    # Write disclaimer and header
    with open(output_path, 'w') as f:
        f.write(disclaimer + "\n")
        f.write("# " + "\t".join(df.columns) + "\n")
        df.to_csv(f, sep='\t', index=False, header=False)

def main():
    parser = argparse.ArgumentParser(description="Apply Benjamini-Hochberg FDR correction to GWAS results.")
    parser.add_argument("--input", required=True, help="Path to the input GWAS raw TSV file.")
    parser.add_argument("--output", required=True, help="Path to the output FDR-corrected TSV file.")
    parser.add_argument("--p-col", default="P", help="Column name for p-values (default: P).")
    parser.add_argument("--q-col", default="Q", help="Column name for q-values (default: Q).")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)
    
    print(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path, sep='\t')
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    print(f"Applying FDR correction to column '{args.p_col}'...")
    df = apply_fdr_correction(df, p_col=args.p_col, q_col=args.q_col)
    
    print(f"Writing results to {output_path}...")
    write_output_with_disclaimer(df, output_path, p_col=args.p_col, q_col=args.q_col)
    
    significant_count = (df[args.q_col] < 0.05).sum()
    print(f"FDR correction complete. Found {significant_count} significant SNPs (q < 0.05).")

if __name__ == "__main__":
    main()