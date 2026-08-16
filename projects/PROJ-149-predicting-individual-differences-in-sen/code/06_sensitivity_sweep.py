"""
T028a: Implement sensitivity sweep across p-value thresholds.

Sweeps p-value thresholds from 0.01 to 0.10 in 0.01 increments.
For each threshold, counts the number of significant correlations.
Reads correlations from data/processed/correlations.csv (produced by T025).
Outputs results to data/processed/sensitivity_sweep.csv.

Dependencies:
  - T025 (produces data/processed/correlations.csv)
  - T007, T008a (data availability)
"""
import os
import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# Import from config using the defined API
from config import get_path, ensure_dirs


def load_correlations() -> pd.DataFrame:
    """
    Load the correlations dataframe from the processed directory.
    
    Returns:
        pd.DataFrame: Correlations with columns including 'p_value' and 'significant'.
    
    Raises:
        FileNotFoundError: If the correlations file does not exist.
    """
    # Use the unified get_path signature: get_path("processed", "correlations.csv")
    # This matches the call sites in the execution failure logs.
    try:
        path = get_path("processed", "correlations.csv")
    except (ValueError, TypeError):
        # Fallback for callers using different signatures if necessary,
        # though the primary fix is to ensure get_path handles all shapes.
        # Based on the failure log: get_path("processed", "correlations.csv") is the intended call.
        # If the config module hasn't been fully patched yet, we try a direct path construction
        # as a last resort to allow this script to run while config is being fixed.
        base = Path(__file__).resolve().parent.parent
        path = base / "data" / "processed" / "correlations.csv"
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"Correlations file not found at {path}. "
                                "Ensure T025 has been run and data/processed/correlations.csv exists.")
    
    df = pd.read_csv(path)
    required_cols = ['p_value']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Correlations file missing required columns: {missing}")
    
    return df


def run_sensitivity_sweep(
    correlations_df: pd.DataFrame,
    p_min: float = 0.01,
    p_max: float = 0.10,
    step: float = 0.01
) -> pd.DataFrame:
    """
    Sweep p-value thresholds and count significant correlations at each step.
    
    Args:
        correlations_df: DataFrame containing correlation results with 'p_value' column.
        p_min: Minimum p-value threshold (inclusive).
        p_max: Maximum p-value threshold (inclusive).
        step: Increment step for the sweep.
    
    Returns:
        pd.DataFrame: Summary of thresholds and counts of significant correlations.
    """
    results = []
    
    # Generate thresholds
    thresholds = np.arange(p_min, p_max + step/2, step)
    
    for threshold in thresholds:
        # Count correlations where p_value <= threshold
        # We assume the 'p_value' column contains the raw p-values.
        # The 'significant' column might exist but is based on a fixed threshold (e.g., Bonferroni),
        # so we recompute significance dynamically based on the current sweep threshold.
        count = (correlations_df['p_value'] <= threshold).sum()
        results.append({
            'threshold': round(threshold, 2),
            'n_significant': int(count),
            'total_tests': len(correlations_df)
        })
    
    return pd.DataFrame(results)


def find_critical_threshold(sweep_results: pd.DataFrame) -> Dict[str, Any]:
    """
    Identify the exact threshold where results become non-significant.
    
    Args:
        sweep_results: DataFrame from run_sensitivity_sweep.
    
    Returns:
        Dict with 'critical_threshold' (float) and 'description' (str).
    """
    # Find the highest threshold where n_significant > 0
    # If n_significant is 0 at the lowest threshold, then no threshold yields significance.
    significant_rows = sweep_results[sweep_results['n_significant'] > 0]
    
    if significant_rows.empty:
        return {
            'critical_threshold': None,
            'description': "No p-value threshold in the sweep range yielded any significant correlations."
        }
    
    # The critical threshold is the highest threshold with at least one significant result.
    # The "non-significant" point is just above this.
    max_sig_threshold = significant_rows['threshold'].max()
    
    # Determine the next threshold in the sequence (where it becomes non-significant)
    next_threshold = max_sig_threshold + 0.01
    if next_threshold > 0.10:
        next_threshold_str = "> 0.10"
    else:
        next_threshold_str = str(round(next_threshold, 2))
    
    return {
        'critical_threshold': max_sig_threshold,
        'description': f"Significant results found up to threshold {max_sig_threshold}. "
                       f"Results become non-significant at {next_threshold_str}."
    }


def main():
    """
    Main entry point for the sensitivity sweep.
    """
    parser = argparse.ArgumentParser(
        description="T028a: Sensitivity sweep of p-value thresholds for correlations."
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help="Path to correlations CSV. Defaults to data/processed/correlations.csv."
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help="Path to output CSV. Defaults to data/processed/sensitivity_sweep.csv."
    )
    args = parser.parse_args()
    
    print("Loading correlations data...")
    try:
        correlations_df = load_correlations()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR loading correlations: {e}")
        sys.exit(1)
    
    if correlations_df.empty:
        print("ERROR: Correlations dataframe is empty. Cannot perform sweep.")
        sys.exit(1)
    
    print(f"Loaded {len(correlations_df)} correlation tests.")
    
    print("Running sensitivity sweep (p=0.01 to 0.10, step=0.01)...")
    sweep_results = run_sensitivity_sweep(correlations_df)
    
    print(f"Sweep complete. Found {len(sweep_results)} thresholds.")
    
    # Find critical threshold
    critical_info = find_critical_threshold(sweep_results)
    
    # Prepare output path
    output_path = args.output or get_path("processed", "sensitivity_sweep.csv")
    if not isinstance(output_path, str):
        output_path = str(output_path)
    
    # Ensure output directory exists
    ensure_dirs(Path(output_path).parent)
    
    # Save sweep results
    sweep_results.to_csv(output_path, index=False)
    print(f"Sensitivity sweep results saved to: {output_path}")
    
    # Save critical threshold info to a separate JSON file for easy access
    critical_path = Path(output_path).parent / "sensitivity_critical_threshold.json"
    import json
    with open(critical_path, 'w') as f:
        json.dump(critical_info, f, indent=2)
    print(f"Critical threshold info saved to: {critical_path}")
    
    # Print summary
    print("\n--- Sensitivity Sweep Summary ---")
    print(f"Total tests: {sweep_results['total_tests'].iloc[0]}")
    print(f"Threshold range: {sweep_results['threshold'].min()} to {sweep_results['threshold'].max()}")
    print(f"Critical threshold: {critical_info['critical_threshold']}")
    print(critical_info['description'])
    print("---------------------------------\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())