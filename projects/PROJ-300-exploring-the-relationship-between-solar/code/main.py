"""
Main pipeline execution script.
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

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation
from code.analysis.lag_search import find_optimal_lag
from code.analysis.sensitivity import analyze_thresholds
from code.viz.plots import plot_scatter, plot_timeseries
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP

def log_quality_warnings(warnings: List[str], output_path: str):
    """
    Log data-quality warnings to a JSON file.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "warnings": warnings
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(log_entry, f, indent=2)

def run_pipeline(start_date: str, end_date: str, output_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Run the full US-1 analysis pipeline.
    """
    results = {}
    warnings = []
    
    # 1. Fetch Data
    print(f"Fetching data from {start_date} to {end_date}...")
    try:
        df_omni = fetch_omni_sw((start_date, end_date))
        df_themis = fetch_themis_ey((start_date, end_date))
    except Exception as e:
        warnings.append(f"Data fetch failed: {str(e)}")
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise e
    
    if df_omni.empty or df_themis.empty:
        warnings.append("One or both datasets are empty after fetching.")
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise ValueError("Empty dataset after fetching.")
    
    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)
    
    if df_omni_clean.empty:
        warnings.append("Data became empty after cleaning.")
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise ValueError("Empty dataset after cleaning.")
    
    # 3. Calculate Physics Lag
    print("Calculating physics-based lag...")
    vsw_mean = df_omni_clean['Vsw'].mean()
    try:
        l_phys = calculate_physics_lag(vsw_mean)
    except ValueError as e:
        warnings.append(f"Physics lag calculation failed: {str(e)}")
        l_phys = 0.0
    
    results['l_phys'] = l_phys
    
    # 4. Apply Lag Shift (using physics lag as initial guess, but optimal lag will be found)
    # For the main correlation, we will use the optimal lag found in step 5
    # But we need to prepare data for the lag search
    
    # 5. Find Optimal Lag
    print("Searching for optimal lag...")
    optimal_lag, lag_corr = find_optimal_lag(
        df_omni_clean['Vsw'], 
        df_themis_clean['Ey'], 
        min_lag=LAG_WINDOW_MIN, 
        max_lag=LAG_WINDOW_MAX, 
        step=LAG_STEP
    )
    results['optimal_lag'] = optimal_lag
    results['lag_correlation_value'] = lag_corr
    
    # 6. Calculate Correlation at Optimal Lag
    print("Calculating correlation at optimal lag...")
    df_themis_shifted = apply_lag_shift(df_themis_clean, optimal_lag)
    
    # Align again after shift
    common_idx = df_omni_clean.index.intersection(df_themis_shifted.index)
    vsw_series = df_omni_clean.loc[common_idx, 'Vsw']
    ey_series = df_themis_shifted.loc[common_idx, 'Ey']
    
    pearson_corr, pearson_p = calculate_correlation(vsw_series, ey_series, method='pearson')
    spearman_corr, spearman_p = calculate_correlation(vsw_series, ey_series, method='spearman')
    
    results['pearson'] = pearson_corr
    results['spearman'] = spearman_corr
    
    # 7. Permutation Test
    print("Running permutation test...")
    try:
        p_permutation = circular_block_permutation(vsw_series, ey_series)
        results['p_val_permutation'] = p_permutation
        results['significant_flag'] = p_permutation < 0.05
    except Exception as e:
        warnings.append(f"Permutation test failed: {str(e)}")
        results['p_val_permutation'] = 1.0
        results['significant_flag'] = False
    
    # 8. Sensitivity Analysis
    print("Running sensitivity analysis...")
    try:
        sensitivity_table = analyze_thresholds(vsw_series, ey_series)
        results['sensitivity_table'] = sensitivity_table
    except Exception as e:
        warnings.append(f"Sensitivity analysis failed: {str(e)}")
        results['sensitivity_table'] = {}
    
    # 9. Generate Plots
    print("Generating plots...")
    os.makedirs(output_dir, exist_ok=True)
    plot_path_scatter = os.path.join(output_dir, "plot_scatter.png")
    plot_path_timeseries = os.path.join(output_dir, "plot_timeseries.png")
    
    try:
        plot_scatter(vsw_series, ey_series, output_path=plot_path_scatter, optimal_lag=optimal_lag)
        plot_timeseries(df_omni_clean, df_themis_shifted, output_path=plot_path_timeseries, optimal_lag=optimal_lag)
    except Exception as e:
        warnings.append(f"Plot generation failed: {str(e)}")
    
    # 10. Log Quality Warnings
    log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
    
    # 11. Save Results
    results_path = os.path.join(output_dir, "us1_correlation.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Pipeline complete. Results saved to {results_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Run Solar Wind - Reconnection Analysis Pipeline")
    parser.add_argument('--start', required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument('--output', default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    run_pipeline(args.start, args.end, args.output)

if __name__ == "__main__":
    main()