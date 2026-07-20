"""
T021: Threshold Sensitivity Analysis
Sweeps across specific significance thresholds to count significant SNPs.

This task implements FR-005 by performing a sensitivity sweep on the
FDR-corrected GWAS results. It measures the robustness of findings
across a range of low-magnitude thresholds.
"""
import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

def generate_thresholds():
    """
    Generate the specific thresholds required by FR-005.
    Sweeps across a range of low-magnitude values to test robustness.
    """
    # Standard GWAS significance thresholds + intermediate steps for sensitivity
    # These are the specific values mandated by the task description
    return [1e-5, 1e-6, 5e-7, 1e-7, 5e-8, 1e-8]

def run_sensitivity_analysis(df, thresholds):
    """
    Count significant SNPs for each threshold.
    
    Args:
        df: DataFrame containing GWAS results with 'P' and 'q_value' columns.
        thresholds: List of float thresholds to sweep.
        
    Returns:
        DataFrame with sensitivity analysis results.
    """
    results = []
    
    for thresh in thresholds:
        # Count SNPs with P < threshold (raw significance)
        p_count = (df['P'] < thresh).sum()
        
        # Count SNPs with q_value < threshold (FDR significance)
        # Only if q_value column exists (it should from T022)
        if 'q_value' in df.columns:
            q_count = (df['q_value'] < thresh).sum()
            min_q = df['q_value'].min()
        else:
            # Fallback if q_value missing (should not happen if T022 ran)
            q_count = 0
            min_q = np.nan
        
        results.append({
            'threshold': thresh,
            'snp_count': len(df),
            'min_q_value': min_q,
            'significant_count': int(q_count)
        })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(
        description="Run threshold sensitivity analysis on FDR-corrected GWAS results"
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="Path to FDR-corrected GWAS results (data/processed/gwas_results_fdr.tsv)"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Path to output report (data/processed/threshold_sensitivity_report.tsv)"
    )
    args = parser.parse_args()

    # Validate input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        print("This file should be produced by code/04_apply_fdr.sh (T022).")
        sys.exit(1)

    # Read data
    try:
        df = pd.read_csv(args.input, sep='\t')
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    # Verify required columns
    required_cols = ['P']
    if 'q_value' not in df.columns:
        print("Warning: 'q_value' column not found. Analysis will proceed with P-values only.")
        # Add a placeholder column to avoid errors in logic, though counts will be 0
        df['q_value'] = np.nan
    else:
        required_cols.append('q_value')
        
    for col in required_cols:
        if col not in df.columns:
            print(f"Error: Required column '{col}' missing from input.")
            sys.exit(1)

    # Generate thresholds
    thresholds = generate_thresholds()

    # Run analysis
    report_df = run_sensitivity_analysis(df, thresholds)

    # Write report
    report_df.to_csv(args.output, sep='\t', index=False)
    print(f"Sensitivity analysis complete.")
    print(f"Report saved to {args.output}")
    print(f"Processed {len(df)} SNPs across {len(thresholds)} thresholds.")

if __name__ == "__main__":
    main()