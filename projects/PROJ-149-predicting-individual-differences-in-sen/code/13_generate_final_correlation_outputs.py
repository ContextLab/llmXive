"""
Task T025: Generate final correlation and non-linear comparison outputs.

This script aggregates results from the Bonferroni-corrected correlations (T021)
and the non-linear analysis (T024) into final deliverable files:
- data/processed/correlations.csv
- data/processed/non_linear_comparison.json

It depends on T021 and T024 being complete.
"""
import os
import sys
import json
import argparse
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

# Import from config for path resolution
# Note: We assume config.py is in the same directory or PYTHONPATH includes it
try:
    from config import get_path, ensure_dirs
except ImportError:
    # Fallback for direct execution without config in path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import get_path, ensure_dirs

def load_bonferroni_results() -> Optional[pd.DataFrame]:
    """
    Load Bonferroni-corrected correlation results.
    
    Expected input: data/interim/bonferroni_results.csv (produced by T021/09_apply_bonferroni.py)
    """
    try:
        # Try to get path from config first
        path = get_path("interim", "bonferroni_results.csv")
    except (ValueError, TypeError):
        # Fallback to hardcoded path if config fails
        path = "data/interim/bonferroni_results.csv"
    
    if not os.path.exists(path):
        print(f"Warning: Bonferroni results file not found at {path}")
        return None
        
    df = pd.read_csv(path)
    print(f"Loaded Bonferroni results: {len(df)} rows from {path}")
    return df

def load_nonlinear_results() -> Optional[Dict[str, Any]]:
    """
    Load non-linear analysis results.
    
    Expected input: data/interim/nonlinear_results.json (produced by T024/12_nonlinear_analysis.py)
    """
    try:
        path = get_path("interim", "nonlinear_results.json")
    except (ValueError, TypeError):
        path = "data/interim/nonlinear_results.json"
    
    if not os.path.exists(path):
        print(f"Warning: Non-linear results file not found at {path}")
        return None
        
    with open(path, 'r') as f:
        data = json.load(f)
    print(f"Loaded non-linear results from {path}")
    return data

def save_correlations(bonferroni_df: pd.DataFrame, output_path: str) -> None:
    """
    Save the final correlations CSV.
    
    This is the primary output for T025 as specified in tasks.md.
    """
    ensure_dirs(output_path)
    bonferroni_df.to_csv(output_path, index=False)
    print(f"Saved correlations to {output_path}")

def save_nonlinear_comparison(nonlinear_data: Dict[str, Any], output_path: str) -> None:
    """
    Save the final non-linear comparison JSON.
    
    This is the second primary output for T025.
    """
    ensure_dirs(output_path)
    with open(output_path, 'w') as f:
        json.dump(nonlinear_data, f, indent=2)
    print(f"Saved non-linear comparison to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate final correlation and non-linear outputs (T025)")
    parser.add_argument('--correlations-output', type=str, default=None,
                      help='Output path for correlations CSV (default: data/processed/correlations.csv)')
    parser.add_argument('--nonlinear-output', type=str, default=None,
                      help='Output path for non-linear comparison JSON (default: data/processed/non_linear_comparison.json)')
    args = parser.parse_args()
    
    # Determine output paths
    if args.correlations_output:
        correlations_path = args.correlations_output
    else:
        try:
            correlations_path = get_path("processed", "correlations.csv")
        except (ValueError, TypeError):
            correlations_path = "data/processed/correlations.csv"
    
    if args.nonlinear_output:
        nonlinear_path = args.nonlinear_output
    else:
        try:
            nonlinear_path = get_path("processed", "non_linear_comparison.json")
        except (ValueError, TypeError):
            nonlinear_path = "data/processed/non_linear_comparison.json"
    
    print(f"Starting T025: Generate final correlation outputs")
    print(f"  Correlations output: {correlations_path}")
    print(f"  Non-linear output: {nonlinear_path}")
    
    # Load inputs
    bonferroni_df = load_bonferroni_results()
    nonlinear_data = load_nonlinear_results()
    
    if bonferroni_df is None:
        print("ERROR: Bonferroni results not found. T021 must complete first.")
        sys.exit(1)
    
    if nonlinear_data is None:
        print("ERROR: Non-linear results not found. T024 must complete first.")
        sys.exit(1)
    
    # Ensure output directories exist
    ensure_dirs(correlations_path)
    ensure_dirs(nonlinear_path)
    
    # Save outputs
    save_correlations(bonferroni_df, correlations_path)
    save_nonlinear_comparison(nonlinear_data, nonlinear_path)
    
    print("T025 completed successfully.")

if __name__ == "__main__":
    main()
