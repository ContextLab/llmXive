import os
import sys
import csv
from pathlib import Path
import pandas as pd
import numpy as np
import yaml

def load_config():
    """Load configuration from code/config.yaml."""
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results():
    """
    Load the analysis results containing correlation coefficients and p-values.
    Expected file: data/analysis/correlation_results.csv (produced by code/analysis.py)
    Schema: channel, correlation, p_value, method, significant (bool)
    """
    results_path = Path("data/analysis/correlation_results.csv")
    if not results_path.exists():
        print(f"Error: Analysis results file not found at {results_path}")
        print("Please ensure code/analysis.py has been run successfully first.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(results_path)
        required_cols = ['channel', 'p_value']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"Error: Missing required columns in {results_path}: {missing}")
            sys.exit(1)
        return df
    except Exception as e:
        print(f"Error loading analysis results: {e}")
        sys.exit(1)

def run_sensitivity_analysis(results_df, thresholds=[0.05, 0.01]):
    """
    Count the number of significant electrodes at each p-value threshold.
    
    Args:
        results_df: DataFrame with 'p_value' column
        thresholds: List of p-value thresholds to test
    
    Returns:
        List of dicts with 'threshold' and 'count_significant'
    """
    if results_df.empty:
        print("Warning: Analysis results are empty. Returning zero counts.")
        return [{"threshold": t, "count_significant": 0} for t in thresholds]
    
    results = []
    for t in thresholds:
        count = int((results_df['p_value'] <= t).sum())
        results.append({
            "threshold": float(t),
            "count_significant": count
        })
    return results

def generate_sensitivity_table(results_list, output_path):
    """
    Write the sensitivity analysis table to a CSV file.
    
    Args:
        results_list: List of dicts from run_sensitivity_analysis
        output_path: Path to write the CSV
    """
    df = pd.DataFrame(results_list)
    # Ensure column order matches spec: threshold, count_significant
    df = df[['threshold', 'count_significant']]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"Sensitivity table written to {output_path}")
    print(df.to_string(index=False))

def main():
    """Main entry point for sensitivity analysis."""
    print("Starting sensitivity analysis...")
    
    config = load_config()
    results_df = load_analysis_results()
    
    # Define thresholds as per FR-006
    thresholds = [0.05, 0.01]
    
    # Run analysis
    sensitivity_results = run_sensitivity_analysis(results_df, thresholds)
    
    # Output path as per task description
    output_path = "data/analysis/sensitivity_table.csv"
    generate_sensitivity_table(sensitivity_results, output_path)
    
    print("Sensitivity analysis completed successfully.")

if __name__ == "__main__":
    main()
