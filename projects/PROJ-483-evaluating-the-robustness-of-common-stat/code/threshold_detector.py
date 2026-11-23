"""
Threshold Detection Module for US2 (T023).

Implements logic to identify the specific dependency strength (r) at which
the Type I error rate first exceeds a nominal alpha threshold (default 0.10).
"""
import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from pathlib import Path

def find_threshold_exceedance(
    aggregated_df: pd.DataFrame,
    alpha_threshold: float = 0.10,
    r_column: str = 'dependency_strength',
    error_column: str = 'type1_error_rate',
    test_type_col: str = 'test_type',
    structure_col: str = 'dependency_structure'
) -> pd.DataFrame:
    """
    Analyzes aggregated simulation results to find the first r where error rate > alpha.

    Args:
        aggregated_df: DataFrame containing columns for dependency strength,
                       error rates, test type, and structure.
        alpha_threshold: The nominal alpha level to exceed (default 0.10).
        r_column: Name of the column containing dependency strength (r).
        error_column: Name of the column containing observed Type I error rate.
        test_type_col: Name of the column identifying the statistical test.
        structure_col: Name of the column identifying the dependency structure.

    Returns:
        A DataFrame containing the specific (r, test_type, structure) combinations
        where the error rate first exceeds the threshold.
    """
    if aggregated_df.empty:
        raise ValueError("Input DataFrame is empty. Cannot detect thresholds.")

    # Ensure numeric types for calculation
    df = aggregated_df.copy()
    df[r_column] = pd.to_numeric(df[r_column], errors='coerce')
    df[error_column] = pd.to_numeric(df[error_column], errors='coerce')

    # Sort by r to ensure we find the "first" exceedance
    df = df.sort_values(by=[test_type_col, structure_col, r_column])

    results = []

    # Group by test type and structure to find the crossing point for each combination
    groups = df.groupby([test_type_col, structure_col])

    for (test_type, structure), group in groups:
        # Filter out NaNs if any
        valid_group = group.dropna(subset=[r_column, error_column])
        if valid_group.empty:
            continue

        # Sort by r ascending
        valid_group = valid_group.sort_values(r_column)

        # Find the first row where error rate > threshold
        exceedance_mask = valid_group[error_column] > alpha_threshold

        if exceedance_mask.any():
            first_exceedance = valid_group[exceedance_mask].iloc[0]
            results.append({
                'test_type': test_type,
                'dependency_structure': structure,
                'threshold_r': first_exceedance[r_column],
                'observed_error_rate': first_exceedance[error_column],
                'alpha_threshold': alpha_threshold,
                'exceeded': True
            })
        else:
            # If never exceeded, record the max r and max error observed
            max_row = valid_group.iloc[-1]
            results.append({
                'test_type': test_type,
                'dependency_structure': structure,
                'threshold_r': None,
                'observed_error_rate': max_row[error_column],
                'alpha_threshold': alpha_threshold,
                'exceeded': False
            })

    return pd.DataFrame(results)


def main():
    """
    Main entry point to run threshold detection on aggregated results.
    
    Reads from results/aggregated.csv (produced by T013/T021) and writes
    results/threshold_detection_report.json.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / 'results' / 'aggregated.csv'
    output_path = project_root / 'results' / 'threshold_detection_report.json'

    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please run T013/T021 to generate results/aggregated.csv first."
        )

    print(f"Loading aggregated results from {input_path}...")
    df = pd.read_csv(input_path)

    print(f"Running threshold detection (alpha=0.10)...")
    try:
        threshold_results = find_threshold_exceedance(df)
    except Exception as e:
        raise RuntimeError(f"Threshold detection failed: {e}")

    # Save results
    print(f"Saving threshold detection report to {output_path}...")
    
    # Convert DataFrame to list of dicts for JSON serialization
    # Handle None values in threshold_r by converting to null in JSON
    report_data = threshold_results.to_dict(orient='records')
    
    with open(output_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"Threshold detection complete. Found {len(threshold_results)} test/structure combinations.")
    exceeded_count = threshold_results['exceeded'].sum()
    print(f"  - Combinations exceeding alpha=0.10: {exceeded_count}")
    print(f"  - Combinations not exceeding alpha=0.10: {len(threshold_results) - exceeded_count}")

    return report_data


if __name__ == '__main__':
    main()