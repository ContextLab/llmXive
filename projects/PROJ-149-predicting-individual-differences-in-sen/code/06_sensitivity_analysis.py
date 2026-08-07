"""
T028: Sensitivity Analysis - P-value Threshold Sweep

This script implements FR-009: Sweep p-value threshold from a stringent to a lenient level.
It consumes correlation results (with Bonferroni correction) and model results to determine
at what threshold the findings become non-significant.

Dependencies:
- data/processed/correlations.csv (from T021/T025)
- data/processed/model_results.json (from T017/T019)
- code/config.py (for paths and seeds)
- code/utils/stats_helpers.py (for statistical utilities if needed)
"""

import os
import sys
import json
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, get_seed
from utils.stats_helpers import bonferroni_correct

def load_correlations():
    """Load the correlation results from T021/T025."""
    path = get_path("correlations.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")
    df = pd.read_csv(path)
    
    # Ensure we have the necessary columns
    required_cols = ['band', 'r_value', 'p_value', 'bonferroni_p_value', 'significant']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Correlations file missing required columns: {missing}")
    
    return df

def load_model_results():
    """Load the main model results to get baseline R2."""
    path = get_path("model_results.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required input file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def run_sensitivity_sweep(correlations_df, thresholds):
    """
    Sweep through p-value thresholds and count how many correlations remain significant.
    
    Args:
        correlations_df: DataFrame with correlation results
        thresholds: List of p-value thresholds to test (e.g., [0.001, 0.005, 0.01, ... 0.05])
        
    Returns:
        DataFrame with sensitivity analysis results
    """
    results = []
    
    # Use Bonferroni corrected p-values for significance determination
    # as per FR-006 specification
    p_col = 'bonferroni_p_value' if 'bonferroni_p_value' in correlations_df.columns else 'p_value'
    
    for thresh in thresholds:
        significant_count = (correlations_df[p_col] < thresh).sum()
        significant_bands = correlations_df[correlations_df[p_col] < thresh]['band'].tolist()
        
        results.append({
            'threshold': thresh,
            'significant_count': int(significant_count),
            'significant_bands': significant_bands,
            'is_any_significant': bool(significant_count > 0)
        })
    
    return pd.DataFrame(results)

def find_critical_threshold(correlations_df):
    """
    Find the exact threshold where the result becomes non-significant.
    This identifies the most stringent threshold at which we still have significance.
    """
    p_col = 'bonferroni_p_value' if 'bonferroni_p_value' in correlations_df.columns else 'p_value'
    
    # Sort by p-value to find the most significant results
    sorted_df = correlations_df.sort_values(by=p_col)
    
    if len(sorted_df) == 0:
        return None, []
    
    # Find the largest p-value that is still < 0.05 (standard threshold)
    significant_rows = sorted_df[sorted_df[p_col] < 0.05]
    
    if significant_rows.empty:
        return 0.0, []
    
    # The critical threshold is the maximum p-value among significant results + epsilon
    # effectively the point just before it becomes non-significant
    max_sig_p = significant_rows[p_col].max()
    
    # Return the bands that are significant at standard 0.05 threshold
    sig_bands = significant_rows['band'].tolist()
    
    return max_sig_p, sig_bands

def main():
    """Main entry point for sensitivity analysis."""
    parser = argparse.ArgumentParser(description="Sensitivity Analysis: P-value Threshold Sweep")
    parser.add_argument('--output', type=str, default=None, help="Output CSV path (default: from config)")
    args = parser.parse_args()

    # Set seed for reproducibility
    seed = get_seed()
    np.random.seed(seed)

    print(f"Starting Sensitivity Analysis (T028) with seed {seed}...")

    # Define sweep range: from very stringent (0.001) to lenient (0.10)
    # Including the standard 0.05 and the Bonferroni corrected 0.0083
    thresholds = [0.001, 0.005, 0.0083, 0.01, 0.02, 0.025, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10]
    
    try:
        # Load dependencies
        correlations_df = load_correlations()
        model_results = load_model_results()
        
        print(f"Loaded {len(correlations_df)} correlation results.")
        
        # Run sensitivity sweep
        sensitivity_df = run_sensitivity_sweep(correlations_df, thresholds)
        
        # Find critical threshold
        critical_thresh, critical_bands = find_critical_threshold(correlations_df)
        
        # Prepare summary output
        summary = {
            'total_bands_tested': len(correlations_df),
            'baseline_significant_at_0.05': int((correlations_df['bonferroni_p_value'] < 0.05).sum()),
            'critical_threshold': critical_thresh,
            'bands_significant_at_critical': critical_bands,
            'sensitivity_results': sensitivity_df.to_dict(orient='records')
        }
        
        # Save results
        output_path = args.output if args.output else get_path("sensitivity_analysis.csv")
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save detailed CSV
        sensitivity_df.to_csv(output_path, index=False)
        print(f"Saved sensitivity analysis to: {output_path}")
        
        # Save JSON summary for downstream tasks (T029, T031)
        json_path = str(output_path).replace('.csv', '_summary.json')
        with open(json_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Saved summary to: {json_path}")
        
        # Print summary to console
        print("\n--- Sensitivity Analysis Summary ---")
        print(f"Bands significant at standard 0.05: {summary['baseline_significant_at_0.05']}")
        print(f"Critical threshold (max p for sig): {summary['critical_threshold']:.4f}")
        print(f"Bands at critical threshold: {summary['bands_significant_at_critical']}")
        print("\nThreshold Sweep:")
        print(sensitivity_df.to_string(index=False))
        
        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Ensure T021 (Bonferroni correction) and T025 (correlation outputs) have completed.")
        return 1
    except Exception as e:
        print(f"Unexpected error during sensitivity analysis: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())