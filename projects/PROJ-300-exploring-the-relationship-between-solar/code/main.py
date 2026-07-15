"""
Main entry point for the solar wind and geomagnetic tail reconnection analysis pipeline.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List

import pandas as pd
import numpy as np

# Local imports
from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample
from data.lag import calculate_physics_lag, apply_lag_shift
from analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from analysis.lag_search import find_optimal_lag
from analysis.sensitivity import analyze_thresholds
from viz.plots import plot_scatter, plot_timeseries
from config import (
    LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP,
    BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS,
    EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION
)

# Ensure results directory exists
RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'processed')
os.makedirs(RESULTS_DIR, exist_ok=True)

def log_quality_warnings(warnings_list: List[Dict[str, Any]]) -> None:
    """
    Log data-quality warnings to a JSON file.
    """
    log_path = os.path.join(RESULTS_DIR, 'quality_log.json')
    with open(log_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "warnings": warnings_list
        }, f, indent=2)
    print(f"Quality warnings logged to {log_path}")

def run_pipeline(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline for the given date range.
    """
    print(f"Starting pipeline for {start_date} to {end_date}")
    
    # 1. Ingest Data
    print("Fetching OMNI solar wind data...")
    df_omni = fetch_omni_sw((start_date, end_date))
    print(f"OMNI data shape: {df_omni.shape}")

    print("Fetching THEMIS Ey data...")
    df_themis = fetch_themis_ey((start_date, end_date))
    print(f"THEMIS data shape: {df_themis.shape}")

    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    df_vsw, df_ey = clean_and_resample(df_omni, df_themis)
    
    # Check for empty data after cleaning
    if df_vsw.empty or df_ey.empty:
        raise ValueError("Data cleaning resulted in empty DataFrames. Cannot proceed.")

    # 3. Calculate Physics Lag (L_phys)
    print("Calculating physics-based lag (L_phys)...")
    vsw_mean = df_vsw['Vsw'].mean()
    if vsw_mean <= 0:
        raise ValueError("Mean solar wind speed is zero or negative. Cannot calculate L_phys.")
    
    L_phys = calculate_physics_lag(vsw_mean)
    print(f"Calculated L_phys: {L_phys:.2f} minutes")

    # 4. Find Optimal Lag (L*)
    print(f"Sweeping lag window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}] with step {LAG_STEP}...")
    optimal_lag, lag_corr_val, lag_results = find_optimal_lag(df_vsw, df_ey)
    print(f"Optimal Lag (L*): {optimal_lag} minutes, Correlation: {lag_corr_val:.4f}")

    # 5. Calculate |L* - L_phys| (SC-002)
    lag_difference = abs(optimal_lag - L_phys)
    print(f"Absolute difference |L* - L_phys|: {lag_difference:.2f} minutes")

    # 6. Correlation Analysis with Permutation Test
    print("Calculating lag-adjusted correlation and running permutation test...")
    # Apply optimal lag shift
    df_vsw_lagged = apply_lag_shift(df_vsw, optimal_lag)
    
    pearson, spearman, p_val_perm, significant = circular_block_permutation(
        df_vsw_lagged['Vsw'], 
        df_ey['Ey'], 
        iterations=PERMUTATION_ITERATIONS
    )
    
    print(f"Pearson: {pearson:.4f}, Spearman: {spearman:.4f}, p-val (perm): {p_val_perm:.4f}")
    print(f"Significant (p < 0.05): {significant}")

    # 7. Bootstrap Confidence Intervals
    print("Running moving block bootstrap for confidence intervals...")
    ci_low, ci_high = moving_block_bootstrap(
        df_vsw_lagged['Vsw'], 
        df_ey['Ey'], 
        iterations=BOOTSTRAP_ITERATIONS
    )
    print(f"95% CI: [{ci_low:.4f}, {ci_high:.4f}]")

    # 8. Sensitivity Analysis
    print("Running sensitivity analysis on Vsw thresholds...")
    sensitivity_table = analyze_thresholds(df_vsw, df_ey, optimal_lag)
    print(f"Sensitivity table generated with {len(sensitivity_table)} entries.")

    # 9. Visualization
    print("Generating plots...")
    plot_scatter(df_vsw_lagged, df_ey, optimal_lag)
    plot_timeseries(df_vsw_lagged, df_ey, optimal_lag)

    # 10. Compile Report
    report = {
        "metadata": {
            "start_date": start_date,
            "end_date": end_date,
            "execution_time": datetime.now().isoformat(),
            "physics_lag_minutes": L_phys,
            "optimal_lag_minutes": optimal_lag,
            "lag_difference_minutes": lag_difference, # SC-002
            "vsw_mean_km_s": float(vsw_mean)
        },
        "correlation": {
            "pearson": float(pearson),
            "spearman": float(spearman),
            "p_value_permutation": float(p_val_perm),
            "significant_flag": bool(significant),
            "confidence_interval_95": [float(ci_low), float(ci_high)]
        },
        "lag_analysis": {
            "optimal_lag": int(optimal_lag),
            "lag_correlation_value": float(lag_corr_val),
            "lag_difference_from_physics": float(lag_difference)
        },
        "sensitivity": sensitivity_table,
        "notes": []
    }

    # FR-013: Add note if permutation test was successful
    if p_val_perm is not None:
        report["notes"].append(
            "Note: Bonferroni correction is conservative for autocorrelated lag searches; "
            "the permutation test (FR-005) is the primary method for significance testing. "
            "Future work should consider adaptive FDR control."
        )

    # Save Report
    report_path = os.path.join(RESULTS_DIR, 'us1_correlation.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Pipeline complete. Report saved to {report_path}")

    return report

def main():
    parser = argparse.ArgumentParser(description="Solar Wind & Tail Reconnection Analysis")
    parser.add_argument('--start', required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', required=True, help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args.start, args.end)
        
        # Log quality warnings (FR-009)
        # In a real scenario, we might collect specific warnings during ingestion/cleaning
        # For now, we log an empty list or generic info if no specific warnings were captured
        log_quality_warnings([
            {"type": "info", "message": "Pipeline executed successfully for requested range."}
        ])
        
    except Exception as e:
        print(f"Pipeline failed: {e}")
        # Log the failure as a warning
        log_quality_warnings([
            {"type": "error", "message": str(e), "timestamp": datetime.now().isoformat()}
        ])
        sys.exit(1)

if __name__ == "__main__":
    main()