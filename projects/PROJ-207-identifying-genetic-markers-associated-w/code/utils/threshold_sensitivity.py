"""
T021: Threshold Sensitivity Analysis
Sweeps across specific significance thresholds to count significant SNPs.
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
    """
    return [1e-7, 5e-8, 1e-8]

def run_sensitivity_analysis(df, thresholds):
    """
    Count significant SNPs for each threshold.
    """
    results = []
    for thresh in thresholds:
        # Count SNPs with P < threshold
        count = (df['P'] < thresh).sum()
        # Also count q-values if available
        if 'q_value' in df.columns:
            q_count = (df['q_value'] < thresh).sum()
        else:
            q_count = 0
        
        results.append({
            'threshold': thresh,
            'p_value_significant_count': int(count),
            'q_value_significant_count': int(q_count)
        })
    
    return pd.DataFrame(results)

def main():
    parser = argparse.ArgumentParser(description="Run threshold sensitivity analysis")
    parser.add_argument("--input", required=True, help="Path to FDR-corrected GWAS results (data/processed/gwas_results_fdr.tsv)")
    parser.add_argument("--output", required=True, help="Path to output report (data/processed/threshold_sensitivity_report.tsv)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Read data
    df = pd.read_csv(args.input, sep='\t')

    # Generate thresholds
    thresholds = generate_thresholds()

    # Run analysis
    report_df = run_sensitivity_analysis(df, thresholds)

    # Write report
    report_df.to_csv(args.output, sep='\t', index=False)
    print(f"Sensitivity analysis complete. Report saved to {args.output}")

if __name__ == "__main__":
    main()
