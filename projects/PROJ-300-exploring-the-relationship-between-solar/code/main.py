"""
Main entry point for the solar wind - geomagnetic tail reconnection analysis pipeline.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List

# Project root handling
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from code.config import (
    LAG_WINDOW_MIN,
    LAG_WINDOW_MAX,
    LAG_STEP,
    BOOTSTRAP_ITERATIONS,
    PERMUTATION_ITERATIONS
)
from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from code.analysis.lag_search import find_optimal_lag
from code.analysis.sensitivity import analyze_thresholds
from code.viz.plots import plot_scatter, plot_timeseries

def log_quality_warnings(warnings: List[Dict[str, Any]], output_path: str) -> None:
    """
    Log data-quality warnings to a JSON file.
    FR-009: Log data-quality warnings to data/processed/quality_log.json
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"warnings": warnings, "timestamp": datetime.now().isoformat()}, f, indent=2)

def run_pipeline(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline for US-1.
    Integrates data/clean.py, data/lag.py, and analysis/correlation.py.
    """
    warnings = []
    results = {}

    # 1. Ingest Data
    print(f"Fetching OMNI solar wind data from {start_date} to {end_date}...")
    try:
        df_sw = fetch_omni_sw((start_date, end_date))
        if df_sw.empty:
            warnings.append({"type": "data_empty", "source": "OMNI", "message": "No solar wind data retrieved."})
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OMNI data: {e}")

    print(f"Fetching THEMIS Ey data from {start_date} to {end_date}...")
    try:
        df_ey = fetch_themis_ey((start_date, end_date))
        if df_ey.empty:
            warnings.append({"type": "data_empty", "source": "THEMIS", "message": "No THEMIS Ey data retrieved."})
    except Exception as e:
        raise RuntimeError(f"Failed to fetch THEMIS data: {e}")

    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    try:
        df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    except Exception as e:
        raise RuntimeError(f"Failed to clean/resample data: {e}")

    if df_sw_clean.empty or df_ey_clean.empty:
        raise ValueError("Cleaned data is empty. Cannot proceed.")

    # 3. Calculate Physics Lag
    print("Calculating physics-based lag...")
    try:
        vsw_mean = df_sw_clean['Vsw'].mean()
        l_phys = calculate_physics_lag(vsw_mean)
        print(f"Physics lag (L_phys): {l_phys:.2f} minutes")
    except Exception as e:
        raise RuntimeError(f"Failed to calculate physics lag: {e}")

    # 4. Apply Lag Shift (Initial)
    # We will re-apply the optimal lag later, but for initial correlation we use L_phys or 0
    # The main pipeline for US-1 focuses on the correlation after lag adjustment.
    # We will determine L* first, then apply it for the final correlation.
    
    # 5. Find Optimal Lag (L*)
    print("Searching for optimal lag...")
    try:
        optimal_lag, best_corr = find_optimal_lag(df_sw_clean, df_ey_clean, l_phys)
        print(f"Optimal lag (L*): {optimal_lag} minutes, Correlation: {best_corr:.4f}")
    except Exception as e:
        raise RuntimeError(f"Failed to find optimal lag: {e}")

    # 6. Apply Optimal Lag Shift
    print(f"Applying optimal lag shift of {optimal_lag} minutes...")
    try:
        df_sw_shifted, df_ey_shifted = apply_lag_shift(df_sw_clean, df_ey_clean, optimal_lag)
    except Exception as e:
        raise RuntimeError(f"Failed to apply lag shift: {e}")

    # 7. Calculate Correlations (Pearson/Spearman)
    print("Calculating correlations...")
    try:
        pearson_r, spearman_r = calculate_correlation(df_sw_shifted['Vsw'], df_ey_shifted['Ey'])
        print(f"Pearson: {pearson_r:.4f}, Spearman: {spearman_r:.4f}")
    except Exception as e:
        raise RuntimeError(f"Failed to calculate correlations: {e}")

    # 8. Permutation Test for Significance
    print(f"Running permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    try:
        p_val_perm = circular_block_permutation(
            df_sw_shifted['Vsw'].values,
            df_ey_shifted['Ey'].values,
            iterations=PERMUTATION_ITERATIONS
        )
        print(f"Permutation p-value: {p_val_perm:.4f}")
    except Exception as e:
        raise RuntimeError(f"Failed to run permutation test: {e}")

    # 9. Determine Significance
    significant_flag = p_val_perm < 0.05
    
    # 10. Calculate Lag Difference |L* - L_phys|
    lag_difference = abs(optimal_lag - l_phys)
    print(f"Lag difference |L* - L_phys|: {lag_difference:.2f} minutes")

    # 11. Sensitivity Analysis
    print("Running sensitivity analysis...")
    try:
        sensitivity_table = analyze_thresholds(df_sw_clean, df_ey_clean, optimal_lag)
    except Exception as e:
        warnings.append({"type": "sensitivity_error", "message": f"Failed sensitivity analysis: {e}"})
        sensitivity_table = {}

    # 12. Generate Plots
    print("Generating plots...")
    try:
        plot_scatter(df_sw_shifted['Vsw'], df_ey_shifted['Ey'], optimal_lag)
        plot_timeseries(df_sw_shifted, df_ey_shifted, optimal_lag)
    except Exception as e:
        warnings.append({"type": "plot_error", "message": f"Failed to generate plots: {e}"})

    # 13. Assemble Report
    report = {
        "pearson": pearson_r,
        "spearman": spearman_r,
        "p_val_permutation": p_val_perm,
        "significant_flag": significant_flag,
        "optimal_lag": optimal_lag,
        "lag_correlation_value": best_corr,
        "lag_difference": lag_difference,
        "sensitivity_table": sensitivity_table,
        "date_range": {"start": start_date, "end": end_date}
    }

    # FR-013: Add narrative note if permutation test succeeded
    # We assume success if we reached this point without exception
    report["notes"] = "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control."

    return report, warnings

def main():
    parser = argparse.ArgumentParser(description="Solar Wind - Geomagnetic Tail Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    # Ensure output directories exist
    os.makedirs(os.path.join(PROJECT_ROOT, "data", "processed"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "results"), exist_ok=True)

    try:
        report, warnings = run_pipeline(args.start, args.end)
        
        # Save JSON Report
        report_path = os.path.join(PROJECT_ROOT, "results", "us1_correlation.json")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {report_path}")

        # Log Quality Warnings (FR-009)
        quality_log_path = os.path.join(PROJECT_ROOT, "data", "processed", "quality_log.json")
        log_quality_warnings(warnings, quality_log_path)
        print(f"Quality log saved to {quality_log_path}")

    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()