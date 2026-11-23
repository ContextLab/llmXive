"""
T028: Sensitivity Analysis for P-value Thresholds

Implements a sweep of p-value thresholds from 0.01 to 0.10 (step 0.01)
on the correlation results generated in T020/T025 to determine
the stability of significant findings.

Input: data/processed/correlations.csv (from T025)
Output: data/processed/sensitivity_results.json
"""
import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs

def load_correlations():
    """Load the correlation results from T025."""
    path = get_path("processed", "correlations.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Required input file not found: {path}. "
            "Please ensure T025 (generate_final_correlation_outputs) has completed successfully."
        )
    df = pd.read_csv(path)
    
    # Validate expected columns
    required_cols = ['band', 'correlation', 'p_value', 'significant']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {path}: {missing}")
    
    return df

def run_sensitivity_sweep(correlations_df, start=0.01, end=0.10, step=0.01):
    """
    Sweep p-value thresholds and count significant correlations at each step.
    
    Args:
        correlations_df: DataFrame with 'p_value' and 'significant' columns
        start: Start of threshold range (inclusive)
        end: End of threshold range (inclusive)
        step: Step size for the sweep
    
    Returns:
        DataFrame with columns: threshold, count_significant, count_total, proportion
    """
    thresholds = np.arange(start, end + step/2, step) # +epsilon to include end
    results = []
    
    total_correlations = len(correlations_df)
    
    for threshold in thresholds:
        # Count how many p-values are <= threshold
        count_sig = (correlations_df['p_value'] <= threshold).sum()
        proportion = count_sig / total_correlations if total_correlations > 0 else 0.0
        
        results.append({
            'threshold': round(threshold, 2),
            'count_significant': int(count_sig),
            'count_total': int(total_correlations),
            'proportion_significant': round(proportion, 4)
        })
    
    return pd.DataFrame(results)

def find_critical_threshold(sensitivity_df, target_count=None, target_proportion=None):
    """
    Identify the threshold where results change significance status.
    
    If target_count is provided, finds the lowest threshold where count >= target_count.
    If target_proportion is provided, finds the lowest threshold where proportion >= target_proportion.
    
    Returns:
        dict with critical_threshold and description
    """
    if target_count is not None:
        # Find first row where count >= target
        mask = sensitivity_df['count_significant'] >= target_count
        if mask.any():
            first_idx = mask.idxmax()
            return {
                'critical_threshold': float(sensitivity_df.loc[first_idx, 'threshold']),
                'description': f"Lowest threshold where significant count >= {target_count}"
            }
    
    if target_proportion is not None:
        # Find first row where proportion >= target
        mask = sensitivity_df['proportion_significant'] >= target_proportion
        if mask.any():
            first_idx = mask.idxmax()
            return {
                'critical_threshold': float(sensitivity_df.loc[first_idx, 'threshold']),
                'description': f"Lowest threshold where proportion >= {target_proportion}"
            }
    
    return {
        'critical_threshold': None,
        'description': "No critical threshold found for specified targets"
    }

def main():
    parser = argparse.ArgumentParser(description="T028: Sensitivity Analysis for P-value Thresholds")
    parser.add_argument('--start', type=float, default=0.01, help="Start of p-value threshold sweep")
    parser.add_argument('--end', type=float, default=0.10, help="End of p-value threshold sweep")
    parser.add_argument('--step', type=float, default=0.01, help="Step size for sweep")
    parser.add_argument('--output', type=str, default=None, help="Output file path (default: data/processed/sensitivity_results.json)")
    args = parser.parse_args()

    print("Loading correlations data...")
    try:
        correlations_df = load_correlations()
        print(f"Loaded {len(correlations_df)} correlations.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        sys.exit(1)

    print(f"Running sensitivity sweep from {args.start} to {args.end} (step {args.step})...")
    sensitivity_results = run_sensitivity_sweep(
        correlations_df, 
        start=args.start, 
        end=args.end, 
        step=args.step
    )

    # Determine critical threshold (where count becomes non-zero)
    critical_info = find_critical_threshold(sensitivity_results, target_count=1)
    
    # Prepare final output
    output_data = {
        'sweep_parameters': {
            'start': args.start,
            'end': args.end,
            'step': args.step
        },
        'total_correlations_tested': int(len(correlations_df)),
        'results': sensitivity_results.to_dict(orient='records'),
        'critical_threshold_info': critical_info
    }

    # Determine output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = get_path("processed", "sensitivity_results.json")
    
    # Ensure directory exists
    ensure_dirs(out_path)

    print(f"Writing results to {out_path}...")
    with open(out_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print("Sensitivity analysis complete.")
    print(f"  Total correlations: {len(correlations_df)}")
    print(f"  Thresholds tested: {len(sensitivity_results)}")
    if critical_info['critical_threshold']:
        print(f"  Critical threshold (count >= 1): {critical_info['critical_threshold']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())