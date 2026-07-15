"""
Sensitivity analysis module to generate tables at different significance thresholds.
"""

import os
import sys
import csv
from pathlib import Path
import pandas as pd
import numpy as np

def load_config(config_path="code/config.yaml"):
    """Load configuration from YAML file."""
    import yaml
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_analysis_results(analysis_dir="data/analysis"):
    """Load analysis results from JSON file."""
    import json
    results_path = os.path.join(analysis_dir, "analysis_results.json")
    if not os.path.exists(results_path):
        raise FileNotFoundError(f"Analysis results not found at {results_path}")
    with open(results_path, 'r') as f:
        return json.load(f)

def run_sensitivity_analysis(results, thresholds=[0.01, 0.05, 0.1]):
    """
    Run sensitivity analysis at different p-value thresholds.
    
    Args:
        results (dict): Analysis results containing correlations and adjusted p-values.
        thresholds (list): List of p-value thresholds to test.
        
    Returns:
        list: List of dicts with threshold, significant_count, and total_count.
    """
    adj_p = results.get("adjusted_p_values", [])
    total = len(adj_p)
    
    sensitivity_data = []
    for thresh in thresholds:
        significant = sum(1 for p in adj_p if p <= thresh)
        sensitivity_data.append({
            "threshold": thresh,
            "significant_count": significant,
            "total_count": total,
            "proportion": significant / total if total > 0 else 0
        })
    
    return sensitivity_data

def generate_sensitivity_table(results, output_dir="data/analysis"):
    """
    Generate and save sensitivity analysis table to CSV.
    
    Args:
        results (dict): Analysis results.
        output_dir (str): Directory to save the output file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    sensitivity_data = run_sensitivity_analysis(results)
    
    output_path = os.path.join(output_dir, "sensitivity_table.csv")
    df = pd.DataFrame(sensitivity_data)
    df.to_csv(output_path, index=False)
    
    return output_path

def main():
    """Main entry point for sensitivity analysis script."""
    config = load_config()
    analysis_dir = config.get("paths", {}).get("data_analysis", "data/analysis")
    
    try:
        results = load_analysis_results(analysis_dir)
        output_path = generate_sensitivity_table(results, analysis_dir)
        print(f"Sensitivity table generated at: {output_path}")
        return 0
    except Exception as e:
        print(f"Error generating sensitivity table: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())