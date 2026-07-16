"""
Main entry point for the solar wind and geomagnetic tail reconnection analysis pipeline.
This file orchestrates data ingestion, cleaning, lag calculation, correlation analysis,
sensitivity analysis, and report generation.

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
from data.lag import calculate_physics_lag, apply_lag_shift, calculate_and_apply_lag
from analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from analysis.lag_search import find_optimal_lag
from analysis.sensitivity import analyze_thresholds, run_sensitivity_sweep
from viz.plots import plot_scatter, plot_timeseries
from config import (
    LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, 
    TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS,
    EARTH_RADIUS_KM, K_PROPAGATION
)

# Ensure paths are relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# Ensure directories exist
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def log_quality_warnings(warnings: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Log data-quality warnings to a JSON file.
    
    Args:
        warnings: List of warning dictionaries with 'type', 'message', 'timestamp' keys.
        output_path: Path to the output JSON file. Defaults to data/processed/quality_log.json.
    """
    if output_path is None:
        output_path = os.path.join(PROCESSED_DIR, "quality_log.json")
    
    # Load existing warnings if file exists
    existing_warnings = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_warnings = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_warnings = []
    
    # Append new warnings
    all_warnings = existing_warnings + warnings
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(all_warnings, f, indent=2, default=str)
    
    print(f"Quality warnings logged to {output_path}")

def run_pipeline(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Run the full analysis pipeline for the specified date range.
    
    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        
    Returns:
        Dictionary containing all analysis results.
    """
    warnings = []
    results = {
        "metadata": {
            "start_date": start_date,
            "end_date": end_date,
            "timestamp": datetime.now().isoformat(),
            "pipeline_version": "1.0.0"
        },
        "data_quality": [],
        "lag_analysis": {},
        "correlation_analysis": {},
        "sensitivity_analysis": {},
        "notes": []
    }
    
    print(f"Starting pipeline for {start_date} to {end_date}")
    
    # 1. Fetch Data
    print("Fetching OMNI solar wind data...")
    try:
        df_omni = fetch_omni_sw((start_date, end_date))
        if df_omni.empty:
            warnings.append({
                "type": "data_fetch",
                "message": f"OMNI data is empty for {start_date} to {end_date}",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        warnings.append({
            "type": "data_fetch_error",
            "message": f"Failed to fetch OMNI data: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        raise
    
    print("Fetching THEMIS Ey data...")
    try:
        df_themis = fetch_themis_ey((start_date, end_date))
        if df_themis.empty:
            warnings.append({
                "type": "data_fetch",
                "message": f"THEMIS data is empty for {start_date} to {end_date}",
                "timestamp": datetime.now().isoformat()
            })
    except Exception as e:
        warnings.append({
            "type": "data_fetch_error",
            "message": f"Failed to fetch THEMIS data: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        raise
    
    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    try:
        df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)
    except Exception as e:
        warnings.append({
            "type": "data_cleaning_error",
            "message": f"Failed to clean data: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        raise
    
    # Log quality warnings
    if warnings:
        log_quality_warnings(warnings)
        results["data_quality"] = warnings
    
    # 3. Calculate Physics-based Lag
    print("Calculating physics-based lag...")
    try:
        vsw_mean = df_omni_clean['Vsw'].mean()
        l_phys = calculate_physics_lag(vsw_mean)
        results["lag_analysis"]["physics_lag_minutes"] = l_phys
        print(f"Physics-based lag (L_phys): {l_phys:.2f} minutes")
    except Exception as e:
        warnings.append({
            "type": "lag_calculation_error",
            "message": f"Failed to calculate physics lag: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        results["lag_analysis"]["physics_lag_minutes"] = None
    
    # 4. Find Optimal Lag
    print("Searching for optimal lag...")
    try:
        optimal_lag, lag_correlation, lag_results = find_optimal_lag(
            df_omni_clean, df_themis_clean,
            min_lag=LAG_WINDOW_MIN,
            max_lag=LAG_WINDOW_MAX,
            step=LAG_STEP
        )
        results["lag_analysis"]["optimal_lag_minutes"] = optimal_lag
        results["lag_analysis"]["optimal_lag_correlation"] = lag_correlation
        results["lag_analysis"]["lag_sweep_results"] = lag_results
        print(f"Optimal lag (L*): {optimal_lag:.2f} minutes (correlation: {lag_correlation:.4f})")
        
        # SC-002: Calculate |L* - L_phys|
        if optimal_lag is not None and l_phys is not None:
            lag_diff = abs(optimal_lag - l_phys)
            results["lag_analysis"]["lag_difference"] = lag_diff
            print(f"Absolute difference |L* - L_phys|: {lag_diff:.2f} minutes")
        else:
            results["lag_analysis"]["lag_difference"] = None
            
    except Exception as e:
        warnings.append({
            "type": "lag_search_error",
            "message": f"Failed to find optimal lag: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        results["lag_analysis"]["optimal_lag_minutes"] = None
        results["lag_analysis"]["optimal_lag_correlation"] = None
        results["lag_analysis"]["lag_difference"] = None
    
    # 5. Apply Optimal Lag and Calculate Correlation
    print("Applying optimal lag and calculating correlation...")
    try:
        if optimal_lag is not None:
            df_omni_lagged = apply_lag_shift(df_omni_clean, optimal_lag)
            df_themis_lagged = df_themis_clean  # Ey is the response, no lag needed on it usually, or shift depends on definition
            # Note: Usually we shift the predictor (Vsw) by the lag to align with the response (Ey)
            # If L* is the time it takes for Vsw to affect Ey, we shift Vsw forward by L*
            # apply_lag_shift handles the direction based on config or convention
            
            pearson_r, spearman_r, p_val = calculate_correlation(
                df_omni_lagged['Vsw'], 
                df_themis_lagged['Ey'],
                method='both'
            )
            
            # Permutation test for significance
            p_val_permutation = circular_block_permutation(
                df_omni_lagged['Vsw'], 
                df_themis_lagged['Ey'],
                iterations=PERMUTATION_ITERATIONS
            )
            
            results["correlation_analysis"]["pearson"] = pearson_r
            results["correlation_analysis"]["spearman"] = spearman_r
            results["correlation_analysis"]["p_value_pearson"] = p_val
            results["correlation_analysis"]["p_value_permutation"] = p_val_permutation
            results["correlation_analysis"]["significant_flag"] = p_val_permutation < 0.05
            
            print(f"Pearson: {pearson_r:.4f}, Spearman: {spearman_r:.4f}")
            print(f"Permutation p-value: {p_val_permutation:.4f}, Significant: {results['correlation_analysis']['significant_flag']}")
            
            # FR-013: Add note if permutation test was successful
            if p_val_permutation is not None:
                results["notes"].append(
                    "Note: Bonferroni correction is conservative for autocorrelated lag searches; "
                    "the permutation test (FR-005) is the primary method for significance testing. "
                    "Future work should consider adaptive FDR control."
                )
        else:
            results["correlation_analysis"]["pearson"] = None
            results["correlation_analysis"]["spearman"] = None
            results["correlation_analysis"]["p_value_permutation"] = None
            results["correlation_analysis"]["significant_flag"] = False
            
    except Exception as e:
        warnings.append({
            "type": "correlation_error",
            "message": f"Failed to calculate correlation: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        results["correlation_analysis"]["pearson"] = None
        results["correlation_analysis"]["spearman"] = None
        results["correlation_analysis"]["p_value_permutation"] = None
        results["correlation_analysis"]["significant_flag"] = False
    
    # 6. Sensitivity Analysis (SC-003)
    print("Running sensitivity analysis...")
    try:
        # Thresholds in km/s as per spec (T011, T028)
        thresholds = [400, 500, 600]
        sensitivity_results = run_sensitivity_sweep(
            df_omni_clean, df_themis_clean,
            thresholds=thresholds,
            min_lag=LAG_WINDOW_MIN,
            max_lag=LAG_WINDOW_MAX,
            step=LAG_STEP
        )
        
        results["sensitivity_analysis"]["thresholds"] = thresholds
        results["sensitivity_analysis"]["results"] = sensitivity_results
        
        # Format for JSON report
        sensitivity_table = []
        for res in sensitivity_results:
            sensitivity_table.append({
                "threshold_km_s": res["threshold"],
                "n_samples": res["n_samples"],
                "pearson": res["pearson"],
                "spearman": res["spearman"],
                "p_value_permutation": res["p_value_permutation"],
                "significant": res["significant"]
            })
        
        results["sensitivity_analysis"]["table"] = sensitivity_table
        print(f"Sensitivity analysis complete. Found {len(sensitivity_results)} threshold results.")
        
    except Exception as e:
        warnings.append({
            "type": "sensitivity_error",
            "message": f"Failed to run sensitivity analysis: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
        results["sensitivity_analysis"]["table"] = []
    
    # 7. Visualization
    print("Generating plots...")
    try:
        if optimal_lag is not None:
            # Ensure data is lagged for plotting
            df_omni_plot = apply_lag_shift(df_omni_clean, optimal_lag)
            df_themis_plot = df_themis_clean
            
            # Scatter plot
            scatter_path = os.path.join(RESULTS_DIR, "plot_scatter.png")
            plot_scatter(df_omni_plot['Vsw'], df_themis_plot['Ey'], optimal_lag, scatter_path)
            print(f"Scatter plot saved to {scatter_path}")
            
            # Time series plot
            ts_path = os.path.join(RESULTS_DIR, "plot_timeseries.png")
            plot_timeseries(df_omni_clean, df_themis_clean, optimal_lag, ts_path)
            print(f"Time series plot saved to {ts_path}")
    except Exception as e:
        warnings.append({
            "type": "plotting_error",
            "message": f"Failed to generate plots: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })
    
    # Finalize results
    results["metadata"]["warnings_count"] = len(warnings)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Solar Wind and Geomagnetic Tail Reconnection Analysis")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    
    args = parser.parse_args()
    
    try:
        results = run_pipeline(args.start, args.end)
        
        # Save results to JSON
        if args.output:
            output_path = args.output
        else:
            output_path = os.path.join(RESULTS_DIR, "us1_correlation.json")
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\nResults saved to {output_path}")
        print("Pipeline completed successfully.")
        
    except Exception as e:
        print(f"Pipeline failed with error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()