"""
T021: Threshold Sensitivity Analysis
Sweeps across specific significance thresholds to count significant SNPs.

This task implements FR-005 by performing a sensitivity sweep on the
FDR-corrected GWAS results. It measures the robustness of findings
across a range of low-magnitude thresholds.

MANDATORY: Uses Benjamini-Hochberg (BH) corrected q-values as per Spec FR-004.
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
    Sweeps across the mandated set: {1e-7, 5e-8, 1e-8} plus intermediate steps.
    """
    # Explicitly mandated thresholds from the task description: {×10⁻⁷, 5×10⁻⁸, 1×10⁻⁸}
    # Ordered from least to most stringent for the sweep report
    return [1e-7, 5e-8, 1e-8]

def run_sensitivity_analysis(df, thresholds):
    """
    Count significant SNPs for each threshold using FDR-corrected q-values.
    
    Args:
        df: DataFrame containing GWAS results with 'P' and 'q_value' columns.
        thresholds: List of float thresholds to sweep.
        
    Returns:
        DataFrame with sensitivity analysis results.
    """
    results = []
    
    # Ensure q_value column exists and is numeric
    if 'q_value' not in df.columns:
        raise ValueError("Input data must contain 'q_value' column (FDR corrected). "
                         "Ensure T022 (04_apply_fdr.sh) has run successfully.")
    
    # Convert to numeric, coercing errors to NaN, then drop NaNs for calculation
    df['q_value'] = pd.to_numeric(df['q_value'], errors='coerce')
    valid_q_df = df.dropna(subset=['q_value'])
    
    for thresh in thresholds:
        # Count SNPs with q_value < threshold (FDR significance)
        significant_count = (valid_q_df['q_value'] < thresh).sum()
        
        # Get the minimum q-value observed in the dataset
        min_q = valid_q_df['q_value'].min() if not valid_q_df.empty else np.nan
        
        results.append({
            'threshold': f"{thresh:.2e}",
            'snp_count': len(df),
            'min_q_value': min_q,
            'significant_count': int(significant_count)
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
        print("This file must be produced by code/04_apply_fdr.sh (T022) which applies BH correction.")
        sys.exit(1)

    # Read data
    try:
        df = pd.read_csv(args.input, sep='\t')
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    # Verify required columns
    if 'q_value' not in df.columns:
        print("Error: Required column 'q_value' missing from input.")
        print("This file must be the output of T022 (FDR correction).")
        sys.exit(1)
        
    if 'P' not in df.columns:
        print("Error: Required column 'P' missing from input.")
        sys.exit(1)

    # Generate thresholds
    thresholds = generate_thresholds()

    # Run analysis
    report_df = run_sensitivity_analysis(df, thresholds)

    # Write report
    # Ensure output directory exists
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(args.output, sep='\t', index=False)
    
    print(f"Sensitivity analysis complete.")
    print(f"Report saved to {args.output}")
    print(f"Processed {len(df)} SNPs across {len(thresholds)} thresholds.")
    print(f"Minimum q-value observed: {report_df['min_q_value'].min():.2e}")

if __name__ == "__main__":
    main()