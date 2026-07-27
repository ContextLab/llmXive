"""
Script to run the correlation analysis with FDR correction (T025).
This script is invoked by the main pipeline to ensure T025 is executed.
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis import run_correlation_analysis, select_correlation_method, set_analysis_seed

def main():
    parser = argparse.ArgumentParser(description="Run T025: Benjamini-Hochberg FDR Correction")
    parser.add_argument("--input", type=str, required=True, help="Path to processed data (Parquet)")
    parser.add_argument("--output", type=str, required=True, help="Path to output correlation matrix JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    set_analysis_seed(args.seed)
    
    # Load data
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)
    
    import pandas as pd
    if args.input.endswith('.parquet'):
        df = pd.read_parquet(args.input)
    else:
        df = pd.read_csv(args.input)
    
    # Select method (auto-detect based on data properties if flags exist)
    # For T025, we assume the method has been selected or we use a default if flags missing
    # In a full run, we would read distribution_flags.json
    method_config = select_correlation_method(df)
    
    # Run analysis and save
    result_df = run_correlation_analysis(df, method_config, args.output)
    
    print(f"T025 Complete: FDR correction applied. Output: {args.output}")
    print(f"Significant correlations (q <= 0.05): {result_df['is_significant'].sum()}")

if __name__ == "__main__":
    main()