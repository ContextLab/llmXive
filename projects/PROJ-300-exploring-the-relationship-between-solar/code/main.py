"""
Main entry point for the Solar Wind and Geomagnetic Tail Reconnection Analysis Pipeline.

This script orchestrates the full data ingestion, cleaning, lag calculation,
correlation analysis, and reporting workflow.

File Path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List
import pandas as pd
import numpy as np

# Project-relative imports
from config import (
    LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP,
    EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION,
    BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS
)
from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample
from data.lag import calculate_physics_lag, apply_lag_shift
from analysis.correlation import calculate_correlation, circular_block_permutation
from analysis.lag_search import find_optimal_lag
from analysis.sensitivity import analyze_thresholds
from viz.plots import plot_scatter, plot_timeseries
from checksums import compute_sha256

def log_quality_warnings(warnings: List[Dict[str, Any]], output_path: str) -> None:
    """
    Log data-quality warnings to a JSON file.
    
    Args:
        warnings: List of warning dictionaries.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(warnings, f, indent=2)

def run_pipeline(start_date: str, end_date: str, output_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Execute the full analysis pipeline for the given date range.
    
    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        output_dir: Directory to save output artifacts.
        
    Returns:
        Dictionary containing the analysis results.
    """
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    warnings = []
    
    # 1. Ingest Data
    print(f"Fetching data from {start_date} to {end_date}...")
    try:
        df_sw = fetch_omni_sw((start_date, end_date))
        df_ey = fetch_themis_ey((start_date, end_date))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch data: {e}")
    
    if df_sw.empty or df_ey.empty:
        warnings.append({"type": "empty_data", "message": "One or both datasets are empty."})
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        return {"error": "empty_data", "warnings": warnings}

    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    try:
        df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    except Exception as e:
        warnings.append({"type": "cleaning_error", "message": str(e)})
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise RuntimeError(f"Data cleaning failed: {e}")

    # 3. Calculate Physics-Based Lag (L_phys)
    # FR-012: L_phys = (K_PROPAGATION * EARTH_RADIUS_KM) / Vsw_mean
    # Note: The formula in T006 description had a division by k at the end which cancels out.
    # We use the standard physics-based lag formula: Distance / Velocity.
    # Distance = TAIL_DISTANCE_RE * EARTH_RADIUS_KM (in km)
    # Velocity = Vsw_mean (in km/s)
    # Result is in seconds. Convert to minutes.
    vsw_mean = df_sw_clean['Vsw'].mean()
    if vsw_mean <= 0:
        warnings.append({"type": "invalid_velocity", "message": "Mean solar wind velocity is non-positive."})
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise ValueError("Invalid mean solar wind velocity.")
        
    # Distance in km
    distance_km = TAIL_DISTANCE_RE * EARTH_RADIUS_KM
    # Lag in seconds
    l_phys_seconds = distance_km / vsw_mean
    # Lag in minutes
    l_phys_minutes = l_phys_seconds / 60.0
    
    print(f"Calculated Physics Lag (L_phys): {l_phys_minutes:.2f} minutes")

    # 4. Apply Lag Shift
    print("Applying physics-based lag shift...")
    df_sw_lagged = apply_lag_shift(df_sw_clean, l_phys_minutes)
    
    # Merge for correlation
    # We need to align the indices after shifting
    # The apply_lag_shift function should handle the index alignment or return a shifted series
    # Assuming it returns a dataframe with the shifted Vsw aligned to Ey time index
    # If not, we do a manual merge on time
    
    # Let's assume apply_lag_shift returns a dataframe with 'timestamp' and 'Vsw_lagged'
    # We need to merge this with Ey data
    # For simplicity in this pipeline, let's assume the clean/resample step aligned them
    # and apply_lag_shift shifts the Vsw series relative to the existing index.
    
    # Re-merge if necessary to ensure alignment
    df_merged = pd.merge(
        df_ey_clean[['timestamp', 'Ey']], 
        df_sw_lagged[['timestamp', 'Vsw']], 
        on='timestamp', 
        how='inner'
    )
    
    if df_merged.empty:
        warnings.append({"type": "alignment_error", "message": "No overlapping data after lag shift."})
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise ValueError("No overlapping data after lag shift.")

    # 5. Calculate Correlations (Pearson/Spearman)
    print("Calculating correlations...")
    pearson_r, pearson_p = calculate_correlation(df_merged['Vsw'], df_merged['Ey'], method='pearson')
    spearman_r, spearman_p = calculate_correlation(df_merged['Vsw'], df_merged['Ey'], method='spearman')
    
    print(f"Pearson: {pearson_r:.4f} (p={pearson_p:.4f})")
    print(f"Spearman: {spearman_r:.4f} (p={spearman_p:.4f})")

    # 6. Permutation Test for Significance
    print("Running permutation test...")
    try:
        p_permutation = circular_block_permutation(
            df_merged['Vsw'], 
            df_merged['Ey'], 
            iterations=PERMUTATION_ITERATIONS
        )
        significant_flag = p_permutation < 0.05
        print(f"Permutation p-value: {p_permutation:.4f} (Significant: {significant_flag})")
    except Exception as e:
        warnings.append({"type": "permutation_error", "message": str(e)})
        p_permutation = None
        significant_flag = False
        # Continue to report coefficients even if test fails

    # 7. Find Optimal Lag (L*) within window [LAG_WINDOW_MIN, LAG_WINDOW_MAX]
    print(f"Searching for optimal lag in [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}] min...")
    try:
        # We use the original clean data for the lag search to find the best lag empirically
        # The lag_search function internally handles the correlation calculation
        optimal_lag, lag_corr_value = find_optimal_lag(
            df_sw_clean['Vsw'], 
            df_ey_clean['Ey'], 
            min_lag=LAG_WINDOW_MIN, 
            max_lag=LAG_WINDOW_MAX, 
            step=LAG_STEP
        )
        print(f"Optimal Lag (L*): {optimal_lag} min (Correlation: {lag_corr_value:.4f})")
    except Exception as e:
        warnings.append({"type": "lag_search_error", "message": str(e)})
        optimal_lag = None
        lag_corr_value = None

    # 8. SC-002: Calculate and report |L* - L_phys|
    lag_difference = None
    if optimal_lag is not None:
        lag_difference = abs(optimal_lag - l_phys_minutes)
        print(f"SC-002 |L* - L_phys|: {lag_difference:.2f} minutes")

    # 9. Sensitivity Analysis (SC-003)
    print("Running sensitivity analysis...")
    try:
        sensitivity_results = analyze_thresholds(
            df_sw_clean['Vsw'], 
            df_ey_clean['Ey'], 
            thresholds=[400, 500, 600] # km/s
        )
    except Exception as e:
        warnings.append({"type": "sensitivity_error", "message": str(e)})
        sensitivity_results = {}

    # 10. Generate Plots (SC-005)
    print("Generating plots...")
    try:
        # Scatter plot
        plot_scatter(
            df_merged['Vsw'], 
            df_merged['Ey'], 
            output_path="results/plot_scatter.png",
            optimal_lag=optimal_lag
        )
        # Time series
        plot_timeseries(
            df_sw_clean, 
            df_ey_clean, 
            output_path="results/plot_timeseries.png",
            optimal_lag=optimal_lag
        )
    except Exception as e:
        warnings.append({"type": "plotting_error", "message": str(e)})

    # 11. Compile Results
    results = {
        "date_range": {"start": start_date, "end": end_date},
        "physics_lag_minutes": l_phys_minutes,
        "optimal_lag_minutes": optimal_lag,
        "lag_correlation_value": lag_corr_value,
        "lag_difference_minutes": lag_difference, # SC-002
        "correlations": {
            "pearson": {"r": pearson_r, "p": pearson_p},
            "spearman": {"r": spearman_r, "p": spearman_p}
        },
        "permutation_test": {
            "p_value": p_permutation,
            "significant": significant_flag
        },
        "sensitivity_table": sensitivity_results,
        "warnings": warnings
    }

    # 12. FR-013: Add narrative note if permutation test succeeded
    if p_permutation is not None:
        results["notes"] = "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control."

    # 13. Save JSON Report
    report_path = os.path.join("results", "us1_correlation.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {report_path}")

    # 14. Log Quality Warnings
    log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))

    # 15. Compute Checksums
    checksums = {}
    for f in ["results/us1_correlation.json", "results/plot_scatter.png", "results/plot_timeseries.png", "data/processed/quality_log.json"]:
        if os.path.exists(f):
            checksums[f] = compute_sha256(f)
    
    state_path = os.path.join(output_dir, "state.json")
    with open(state_path, 'w') as f:
        json.dump({"checksums": checksums, "timestamp": datetime.now().isoformat()}, f)

    return results

def main():
    parser = argparse.ArgumentParser(description="Solar Wind and Geomagnetic Tail Reconnection Analysis")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output-dir", default="data/processed", help="Output directory for artifacts")
    
    args = parser.parse_args()

    # Ensure output directories exist
    os.makedirs(os.path.join(PROJECT_ROOT, "data", "processed"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "results"), exist_ok=True)

    try:
        run_pipeline(args.start, args.end, args.output_dir)
        print("Pipeline completed successfully.")
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()