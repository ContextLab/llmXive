"""
Main pipeline execution script for solar wind and geomagnetic tail reconnection analysis.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS
from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample
from code.data.lag import calculate_physics_lag, apply_lag_shift, prepare_lagged_data
from code.analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from code.analysis.lag_search import find_optimal_lag
from code.analysis.sensitivity import analyze_thresholds
from code.viz.plots import plot_scatter, plot_timeseries

def run_pipeline(
    start_date: str,
    end_date: str,
    output_dir: str = "data/processed",
    results_dir: str = "results"
) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline.

    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        output_dir: Directory for processed data.
        results_dir: Directory for JSON reports and plots.

    Returns:
        A dictionary containing the analysis results.
    """
    # Ensure directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    print(f"Starting pipeline for {start_date} to {end_date}")

    # 1. Ingest Data
    print("Fetching OMNI Solar Wind data...")
    df_omni = fetch_omni_sw((start_date, end_date))
    print(f"OMNI data shape: {df_omni.shape}")

    print("Fetching THEMIS Ey data...")
    df_themis = fetch_themis_ey((start_date, end_date))
    print(f"THEMIS data shape: {df_themis.shape}")

    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    df_vsw_clean, df_ey_clean = clean_and_resample(df_omni, df_themis)
    
    # Prepare aligned series
    vsw_series = df_vsw_clean['Vsw']
    ey_series = df_ey_clean['Ey']
    timestamp_series = df_vsw_clean.index

    # 3. Calculate Physics-based Lag
    print("Calculating physics-based lag...")
    vsw_mean = vsw_series.mean()
    if vsw_mean > 0:
        l_phys = calculate_physics_lag(vsw_mean)
    else:
        l_phys = 0
        print("Warning: Mean Vsw is zero or negative, setting L_phys to 0.")
    print(f"Physics-based lag L_phys: {l_phys:.2f} min")

    # 4. Find Optimal Lag
    print(f"Searching for optimal lag in window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}]...")
    optimal_lag, lag_correlation_value, lag_results = find_optimal_lag(
        vsw_series, ey_series, LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
    )
    print(f"Optimal lag L*: {optimal_lag} min, Correlation: {lag_correlation_value:.4f}")

    # 5. Apply Optimal Lag and Calculate Correlation
    print("Applying optimal lag shift...")
    vsw_lagged, ey_lagged = apply_lag_shift(vsw_series, ey_series, optimal_lag)

    # Calculate correlation metrics
    pearson_r, spearman_r, p_val_perm, ci_bootstrap = calculate_correlation(
        vsw_lagged, ey_lagged, 
        permutation_iterations=PERMUTATION_ITERATIONS,
        bootstrap_iterations=BOOTSTRAP_ITERATIONS
    )
    
    significant_flag = p_val_perm < 0.05
    print(f"Pearson: {pearson_r:.4f}, Spearman: {spearman_r:.4f}, p-val: {p_val_perm:.4f}, Significant: {significant_flag}")

    # 6. Sensitivity Analysis
    print("Running sensitivity analysis...")
    sensitivity_table = analyze_thresholds(vsw_series, ey_series, optimal_lag)

    # 7. Generate Visualizations
    print("Generating plots...")
    scatter_path = plot_scatter(
        vsw_lagged, ey_lagged, 
        optimal_lag=optimal_lag, 
        correlation=pearson_r, 
        p_value=p_val_perm
    )
    timeseries_path = plot_timeseries(
        vsw_lagged, ey_lagged, 
        timestamp_series, 
        optimal_lag=optimal_lag
    )

    # 8. Compile Results
    lag_difference = abs(optimal_lag - l_phys)
    
    # Note for FR-013
    note_text = "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control."

    results = {
        "metadata": {
            "start_date": start_date,
            "end_date": end_date,
            "run_timestamp": datetime.now().isoformat()
        },
        "physics_lag": {
            "l_phys_minutes": round(l_phys, 2),
            "mean_vsw_kms": round(vsw_mean, 2)
        },
        "optimal_lag": {
            "l_star_minutes": optimal_lag,
            "lag_correlation": round(lag_correlation_value, 4),
            "lag_difference": round(lag_difference, 2)
        },
        "correlation": {
            "pearson": round(pearson_r, 4),
            "spearman": round(spearman_r, 4),
            "p_val_permutation": round(p_val_perm, 4),
            "significant_flag": significant_flag,
            "confidence_interval_95": [round(ci_bootstrap[0], 4), round(ci_bootstrap[1], 4)]
        },
        "sensitivity_table": sensitivity_table,
        "notes": [note_text] if significant_flag else [],
        "outputs": {
            "scatter_plot": os.path.relpath(scatter_path, PROJECT_ROOT),
            "timeseries_plot": os.path.relpath(timeseries_path, PROJECT_ROOT)
        }
    }

    # 9. Save Results
    report_path = os.path.join(results_dir, "us1_correlation.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Pipeline complete. Report saved to {report_path}")
    print(f"Plots saved to {scatter_path} and {timeseries_path}")

    return results

if __name__ == "__main__":
    # Default sample range for demonstration if no args provided
    # In a real scenario, these would be passed via CLI or config
    start = "2023-06-01"
    end = "2023-06-05"
    
    if len(sys.argv) >= 3:
        start = sys.argv[1]
        end = sys.argv[2]
    
    run_pipeline(start, end)
