"""
Main pipeline entry point for PROJ-300.
Orchestrates data ingestion, cleaning, lag adjustment, correlation analysis,
and result reporting for User Story 1.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List

# Local imports (relative to code/ root)
from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample
from data.lag import calculate_physics_lag, apply_lag_shift, calculate_and_apply_lag
from analysis.correlation import calculate_correlation, circular_block_permutation
from analysis.lag_search import find_optimal_lag
from viz.plots import plot_scatter, plot_timeseries
from config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, PERMUTATION_ITERATIONS

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

def run_pipeline(
    start_date: str,
    end_date: str,
    output_dir: str = "data/processed",
    results_dir: str = "results"
) -> Dict[str, Any]:
    """
    Execute the full analysis pipeline for User Story 1.
    1. Ingest OMNI (Vsw, Bz) and THEMIS (Ey) data.
    2. Clean and resample.
    3. Calculate physics-based lag and apply shifts.
    4. Search for optimal lag.
    5. Calculate correlations and permutation p-values.
    6. Generate plots and write JSON report.
    """
    # Ensure output directories exist
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    warnings = []

    # 1. Ingest Data
    print(f"Fetching OMNI data for {start_date} to {end_date}...")
    try:
        df_omni = fetch_omni_sw((start_date, end_date))
        if df_omni.empty:
            warnings.append({"source": "OMNI", "issue": "No data returned for range"})
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OMNI data: {e}")

    print(f"Fetching THEMIS data for {start_date} to {end_date}...")
    try:
        df_themis = fetch_themis_ey((start_date, end_date))
        if df_themis.empty:
            warnings.append({"source": "THEMIS", "issue": "No data returned for range"})
    except Exception as e:
        raise RuntimeError(f"Failed to fetch THEMIS data: {e}")

    # Log warnings
    log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))

    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)

    if df_omni_clean.empty or df_themis_clean.empty:
        raise ValueError("Data cleaning resulted in empty DataFrames.")

    # 3. Physics Lag & Initial Shift (optional, but good for baseline)
    # The main pipeline focuses on the search for optimal lag L*
    # But we calculate L_phys for reporting (SC-002)
    vsw_mean = df_omni_clean['Vsw'].mean()
    if pd.isna(vsw_mean) or vsw_mean == 0:
        raise ValueError("Cannot calculate physics lag with zero or NaN mean Vsw.")
    
    l_phys = calculate_physics_lag(vsw_mean)
    print(f"Physics-based lag L_phys: {l_phys:.2f} min")

    # 4. Optimal Lag Search (US-2 integration, required for US-1 report completeness)
    print(f"Searching for optimal lag in window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}] min...")
    optimal_lag, lag_corr_val = find_optimal_lag(
        df_omni_clean['Vsw'], 
        df_themis_clean['Ey'], 
        min_lag=LAG_WINDOW_MIN, 
        max_lag=LAG_WINDOW_MAX, 
        step=LAG_STEP
    )
    print(f"Optimal lag L*: {optimal_lag} min, Correlation: {lag_corr_val:.4f}")

    # 5. Apply Optimal Lag for final analysis
    # We shift the time series to align them based on L*
    # Note: apply_lag_shift typically shifts the 'response' (Ey) back by the lag
    # relative to the 'driver' (Vsw).
    df_vsw_lagged = df_omni_clean.copy()
    df_ey_lagged = df_themis_clean.copy()
    
    # Apply shift: Ey is delayed by L* relative to Vsw, so we shift Ey forward in time
    # or Vsw backward. The function `apply_lag_shift` handles the logic.
    # Assuming signature: apply_lag_shift(driver, response, lag_minutes)
    # We want to align them for correlation.
    df_vsw_final, df_ey_final = calculate_and_apply_lag(
        df_omni_clean, df_themis_clean, optimal_lag
    )

    # 6. Calculate Correlations
    print("Calculating correlations...")
    pearson_r, spearman_r = calculate_correlation(
        df_vsw_final['Vsw'], df_ey_final['Ey']
    )
    print(f"Pearson: {pearson_r:.4f}, Spearman: {spearman_r:.4f}")

    # 7. Permutation Test for Significance
    print(f"Running permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    try:
        p_val = circular_block_permutation(
            df_vsw_final['Vsw'], df_ey_final['Ey'], 
            iterations=PERMUTATION_ITERATIONS
        )
        significant = p_val < 0.05
    except Exception as e:
        # Fallback if permutation fails (e.g., insufficient data), but log it
        warnings.append({"method": "permutation", "issue": str(e), "result": "skipped"})
        p_val = None
        significant = False

    # 8. Prepare Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "date_range": {"start": start_date, "end": end_date},
        "statistics": {
            "pearson": float(pearson_r),
            "spearman": float(spearman_r),
            "p_val_permutation": float(p_val) if p_val is not None else None,
            "significant_flag": bool(significant) if p_val is not None else False,
            "optimal_lag": int(optimal_lag),
            "lag_correlation_value": float(lag_corr_val),
            "lag_difference": abs(optimal_lag - l_phys),
            "l_phys": float(l_phys)
        },
        "data_quality": warnings
    }

    # 9. Write JSON Report
    report_path = os.path.join(results_dir, "us1_correlation.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Report written to {report_path}")

    # 10. Generate Plots
    print("Generating plots...")
    plot_scatter(df_vsw_final['Vsw'], df_ey_final['Ey'], optimal_lag, 
                os.path.join(results_dir, "plot_scatter.png"))
    plot_timeseries(df_vsw_final, df_ey_final, optimal_lag, 
                   os.path.join(results_dir, "plot_timeseries.png"))
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Run Solar Wind Reconnection Analysis")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default="data/processed", help="Output directory for logs")
    parser.add_argument("--results", default="results", help="Directory for results/plots")
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args.start, args.end, args.output, args.results)
        print("Pipeline completed successfully.")
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()