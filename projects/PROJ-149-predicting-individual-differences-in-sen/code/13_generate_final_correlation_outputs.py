"""
T025 Implementation: Generate final correlation and non-linear comparison outputs.

This script aggregates results from the Bonferroni-corrected correlations (T021)
and the non-linear analysis (T024) to produce the final deliverables:
1. data/processed/correlations.csv
2. data/processed/non_linear_comparison.json

Dependencies:
- code/09_apply_bonferroni.py (produces data/interim/correlations_bonferroni.csv)
- code/12_nonlinear_analysis.py (produces data/interim/nonlinear_results.json)
"""

import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

def load_bonferroni_results():
    """
    Load the Bonferroni-corrected correlation results.
    Expected input: data/interim/correlations_bonferroni.csv
    """
    input_path = get_path("interim", "correlations_bonferroni.csv")
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Bonferroni results not found at {input_path}. "
            "Please ensure code/09_apply_bonferroni.py has run successfully."
        )
    df = pd.read_csv(input_path)
    return df

def load_nonlinear_results():
    """
    Load the non-linear analysis results.
    Expected input: data/interim/nonlinear_results.json
    """
    input_path = get_path("interim", "nonlinear_results.json")
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Non-linear results not found at {input_path}. "
            "Please ensure code/12_nonlinear_analysis.py has run successfully."
        )
    with open(input_path, 'r') as f:
        data = json.load(f)
    return data

def save_correlations(df, output_path):
    """
    Save the final correlations dataframe to CSV.
    """
    ensure_dirs(output_path)
    df.to_csv(output_path, index=False)
    print(f"Saved correlations to {output_path}")

def save_nonlinear_comparison(data, output_path):
    """
    Save the final non-linear comparison results to JSON.
    """
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved non-linear comparison to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate final correlation and non-linear outputs (T025).")
    args = parser.parse_args()
    
    print("Starting T025: Generating final correlation and non-linear outputs...")
    
    # 1. Load Bonferroni-corrected correlations
    print("Loading Bonferroni-corrected correlations...")
    try:
        corr_df = load_bonferroni_results()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # 2. Load non-linear analysis results
    print("Loading non-linear analysis results...")
    try:
        nonlinear_data = load_nonlinear_results()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # 3. Save final artifacts
    print("Saving final artifacts...")
    
    # Output 1: correlations.csv
    corr_output_path = get_path("processed", "correlations.csv")
    save_correlations(corr_df, corr_output_path)
    
    # Output 2: non_linear_comparison.json
    nonlinear_output_path = get_path("processed", "non_linear_comparison.json")
    save_nonlinear_comparison(nonlinear_data, nonlinear_output_path)
    
    print("T025 completed successfully.")

if __name__ == "__main__":
    main()