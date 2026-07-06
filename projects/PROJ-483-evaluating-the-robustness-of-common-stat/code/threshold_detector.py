import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

def find_threshold_exceedance(
    results_df: pd.DataFrame,
    alpha_threshold: float = 0.10,
    dependency_col: str = "dependency_strength",
    error_rate_col: str = "observed_type1_error"
) -> pd.DataFrame:
    """
    Identifies the specific dependency strength (r) where the observed error rate
    first exceeds the given alpha threshold for each test/structure combination.

    This implements T023: Threshold detection logic to report specific r where
    error rate exceeds alpha=0.10.

    Args:
        results_df: DataFrame containing aggregated simulation results.
            Expected columns: dependency_strength, observed_type1_error,
            test_type, dependency_structure (or similar grouping keys).
        alpha_threshold: The alpha level to check against (default 0.10).
        dependency_col: Column name for dependency strength (r).
        error_rate_col: Column name for observed error rate.

    Returns:
        A DataFrame with columns:
            - test_type
            - dependency_structure
            - threshold_r: The r value where error rate first > alpha_threshold.
            - error_rate_at_threshold: The error rate at that r.
            - status: "exceeded" if found, "never_exceeded" if max error < threshold.
    """
    if results_df.empty:
        return pd.DataFrame(columns=["test_type", "dependency_structure", "threshold_r", "error_rate_at_threshold", "status"])

    # Ensure numeric types
    results_df = results_df.copy()
    results_df[dependency_col] = pd.to_numeric(results_df[dependency_col], errors='coerce')
    results_df[error_rate_col] = pd.to_numeric(results_df[error_rate_col], errors='coerce')

    # Drop rows with invalid numeric data
    clean_df = results_df.dropna(subset=[dependency_col, error_rate_col])

    if clean_df.empty:
        return pd.DataFrame(columns=["test_type", "dependency_structure", "threshold_r", "error_rate_at_threshold", "status"])

    # Group by test type and dependency structure to find thresholds per condition
    # Assuming standard grouping keys based on T021/T022 context
    group_cols = ["test_type", "dependency_structure"]
    
    # Handle cases where grouping columns might have different names or be missing
    # Fallback to available columns if expected ones aren't present
    available_group_cols = [c for c in group_cols if c in clean_df.columns]
    
    if not available_group_cols:
        # If no grouping columns, treat the whole dataset as one group
        clean_df = clean_df.assign(test_type="all", dependency_structure="all")
        available_group_cols = ["test_type", "dependency_structure"]

    results_list = []

    for name, group in clean_df.groupby(available_group_cols):
        # Sort by dependency strength ascending
        sorted_group = group.sort_values(by=dependency_col)
        
        # Find first row where error rate > threshold
        exceeded_rows = sorted_group[sorted_group[error_rate_col] > alpha_threshold]
        
        if not exceeded_rows.empty:
            first_exceedance = exceeded_rows.iloc[0]
            results_list.append({
                "test_type": first_exceedance["test_type"],
                "dependency_structure": first_exceedance["dependency_structure"],
                "threshold_r": float(first_exceedance[dependency_col]),
                "error_rate_at_threshold": float(first_exceedance[error_rate_col]),
                "status": "exceeded"
            })
        else:
            # Check if max error rate is below threshold
            max_error = sorted_group[error_rate_col].max()
            results_list.append({
                "test_type": name[0] if len(name) == 1 else name, # Handle tuple keys
                "dependency_structure": name[1] if len(name) > 1 else "all",
                "threshold_r": None,
                "error_rate_at_threshold": max_error,
                "status": "never_exceeded"
            })

    return pd.DataFrame(results_list)

def main():
    """
    Main entry point to run threshold detection on aggregated results.
    Reads from results/aggregated.csv and outputs to results/threshold_report.json.
    """
    # Paths
    input_path = Path("results/aggregated.csv")
    output_path = Path("results/threshold_report.json")
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} not found. Run T013/T021 first.")
        return

    # Load data
    df = pd.read_csv(input_path)
    
    # Run detection
    threshold_results = find_threshold_exceedance(df, alpha_threshold=0.10)
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to JSON serializable format
    report = {
        "analysis_timestamp": str(pd.Timestamp.now()),
        "alpha_threshold": 0.10,
        "thresholds": threshold_results.to_dict(orient="records")
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"Threshold detection complete. Report saved to {output_path}")
    print(f"Found {len(threshold_results[threshold_results['status'] == 'exceeded'])} cases where error rate exceeded 0.10.")

if __name__ == "__main__":
    main()
