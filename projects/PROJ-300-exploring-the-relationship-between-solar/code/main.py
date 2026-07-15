"""
Main entry point for the solar wind - geomagnetic tail reconnection analysis pipeline.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List
import pandas as pd
import numpy as np

# Adjust path to ensure imports work when run as script or module
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation
from code.analysis.lag_search import find_optimal_lag
from code.viz.plots import plot_scatter, plot_timeseries
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS, EARTH_RADIUS_KM, K_PROPAGATION

def log_quality_warnings(warnings: List[Dict[str, Any]], output_path: str) -> None:
    """
    Log data-quality warnings to a JSON file.
    FR-009: Log data-quality warnings to data/processed/quality_log.json.
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "datasets": {
            "omni": {},
            "themis": {}
        },
        "warnings": [],
        "summary": {}
    }

    # Analyze OMNI Data
    omni_warnings = []
    if df_omni is not None and not df_omni.empty:
        # NaN Analysis
        nan_counts = df_omni.isna().sum()
        total_rows = len(df_omni)
        nan_pct = (nan_counts / total_rows * 100).round(2)
        
        report["datasets"]["omni"]["nan_counts"] = nan_counts.to_dict()
        report["datasets"]["omni"]["nan_percentages"] = nan_pct.to_dict()

        # Gap Analysis
        if 'timestamp' in df_omni.columns:
            df_sorted = df_omni.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff()
            # Assuming 5-min cadence after cleaning, but checking for larger gaps
            median_diff = time_diffs.median()
            large_gaps = time_diffs[time_diffs > (median_diff * 2)]
            if len(large_gaps) > 0:
                omni_warnings.append(f"Detected {len(large_gaps)} significant time gaps (> 2x median cadence) in OMNI data.")
        
        # Outlier Analysis (Vsw)
        if 'Vsw' in df_omni.columns:
            vsw_mean = df_omni['Vsw'].mean()
            vsw_std = df_omni['Vsw'].std()
            if vsw_std > 0:
                outliers = df_omni[abs(df_omni['Vsw'] - vsw_mean) > (5 * vsw_std)]
                if len(outliers) > 0:
                    omni_warnings.append(f"Detected {len(outliers)} extreme outliers in OMNI Vsw (> 5 std dev).")

        report["datasets"]["omni"]["warnings"] = omni_warnings
    else:
        omni_warnings.append("OMNI data is empty or None.")
        report["datasets"]["omni"]["warnings"] = omni_warnings

    # Analyze THEMIS Data
    themis_warnings = []
    if df_themis is not None and not df_themis.empty:
        # NaN Analysis
        nan_counts = df_themis.isna().sum()
        total_rows = len(df_themis)
        nan_pct = (nan_counts / total_rows * 100).round(2)
        
        report["datasets"]["themis"]["nan_counts"] = nan_counts.to_dict()
        report["datasets"]["themis"]["nan_percentages"] = nan_pct.to_dict()

        # Gap Analysis
        if 'timestamp' in df_themis.columns:
            df_sorted = df_themis.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff()
            median_diff = time_diffs.median()
            large_gaps = time_diffs[time_diffs > (median_diff * 2)]
            if len(large_gaps) > 0:
                themis_warnings.append(f"Detected {len(large_gaps)} significant time gaps (> 2x median cadence) in THEMIS data.")

        # Outlier Analysis (Ey)
        if 'Ey' in df_themis.columns:
            ey_mean = df_themis['Ey'].mean()
            ey_std = df_themis['Ey'].std()
            if ey_std > 0:
                outliers = df_themis[abs(df_themis['Ey'] - ey_mean) > (5 * ey_std)]
                if len(outliers) > 0:
                    themis_warnings.append(f"Detected {len(outliers)} extreme outliers in THEMIS Ey (> 5 std dev).")

        report["datasets"]["themis"]["warnings"] = themis_warnings
    else:
        themis_warnings.append("THEMIS data is empty or None.")
        report["datasets"]["themis"]["warnings"] = themis_warnings

    # Aggregate Warnings
    all_warnings = omni_warnings + themis_warnings
    report["warnings"] = all_warnings
    report["summary"]["total_warnings"] = len(all_warnings)
    report["summary"]["has_critical_issues"] = len(all_warnings) > 0

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write to file
    with open(output_path, 'w') as f:
        json.dump(warnings, f, indent=2, default=str)
    print(f"Quality warnings logged to {output_path}")

def run_pipeline(start_date: str, end_date: str, output_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Execute the full analysis pipeline for US-1.
    Integrates data cleaning, lag calculation, and correlation analysis.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        output_dir: Directory for output artifacts
        
    Returns:
        Dictionary containing analysis results
    """
    warnings = []
    
    print(f"Fetching data for {start_date} to {end_date}...")
    try:
        # Fetch raw data
        df_omni = fetch_omni_sw((start_date, end_date))
        df_themis = fetch_themis_ey((start_date, end_date))
        
        if df_omni.empty:
            warnings.append({"type": "data_empty", "source": "OMNI", "message": "OMNI data is empty"})
        if df_themis.empty:
            warnings.append({"type": "data_empty", "source": "THEMIS", "message": "THEMIS data is empty"})
            
        if df_omni.empty or df_themis.empty:
            raise ValueError("One or both datasets are empty. Cannot proceed.")
            
    except Exception as e:
        warnings.append({"type": "fetch_error", "message": str(e)})
        # Log warnings before failing
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise RuntimeError(f"Data fetching failed: {e}")

    # Clean and resample
    print("Cleaning and resampling data...")
    try:
        df_vsw, df_ey = clean_and_resample(df_omni, df_themis)
        if df_vsw.empty or df_ey.empty:
            warnings.append({"type": "cleaning_result_empty", "message": "Data cleaning resulted in empty DataFrames"})
            log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
            raise ValueError("Cleaned data is empty.")
    except Exception as e:
        warnings.append({"type": "cleaning_error", "message": str(e)})
        log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
        raise RuntimeError(f"Data cleaning failed: {e}")

    # Calculate physics-based lag
    print("Calculating physics-based lag...")
    try:
        vsw_mean = df_vsw['Vsw'].mean()
        if pd.isna(vsw_mean) or vsw_mean == 0:
            warnings.append({"type": "invalid_vsw", "message": f"Invalid Vsw mean: {vsw_mean}"})
            vsw_mean = 400.0  # Default fallback for calculation to avoid division by zero, but warn
        
        lag_phys_minutes = calculate_physics_lag(vsw_mean, TAIL_DISTANCE_RE, EARTH_RADIUS_KM, K_PROPAGATION)
        print(f"Physics-based lag (L_phys): {lag_phys_minutes:.2f} minutes")
    except Exception as e:
        warnings.append({"type": "lag_calc_error", "message": str(e)})
        lag_phys_minutes = 45.0  # Fallback
        print(f"Warning: Lag calculation failed ({e}), using default 45 min.")

    # Find optimal lag within window
    print(f"Searching for optimal lag in window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}] min...")
    try:
        optimal_lag, lag_corr_value, lag_search_results = find_optimal_lag(
            df_vsw, df_ey, 
            min_lag=LAG_WINDOW_MIN, 
            max_lag=LAG_WINDOW_MAX, 
            step=LAG_STEP
        )
        print(f"Optimal lag (L*): {optimal_lag} min, Correlation: {lag_corr_value:.4f}")
    except Exception as e:
        warnings.append({"type": "lag_search_error", "message": str(e)})
        optimal_lag = int(lag_phys_minutes)
        lag_corr_value = 0.0
        print(f"Warning: Lag search failed ({e}), using physics lag.")

    # Apply optimal lag shift
    print(f"Applying optimal lag shift of {optimal_lag} minutes...")
    df_vsw_lagged = apply_lag_shift(df_vsw, optimal_lag, lag_type='positive')
    
    # Calculate correlations
    print("Calculating correlations...")
    pearson, spearman, p_val_perm, p_val_pearson, p_val_spearman = None, None, None, None, None
    significant_flag = False
    
    try:
        pearson, spearman, p_val_perm, p_val_pearson, p_val_spearman = calculate_correlation(
            df_vsw_lagged['Vsw'], 
            df_ey['Ey']
        )
        
        # Determine significance based on permutation p-value
        alpha = 0.05
        if p_val_perm is not None:
            significant_flag = p_val_perm < alpha
            print(f"Pearson: {pearson:.4f} (p={p_val_pearson:.4f}), Spearman: {spearman:.4f} (p={p_val_spearman:.4f})")
            print(f"Permutation p-value: {p_val_perm:.4f} -> Significant: {significant_flag}")
        else:
            warnings.append({"type": "p_value_missing", "message": "Permutation p-value could not be calculated"})
            print("Warning: Permutation p-value missing.")
            
    except Exception as e:
        warnings.append({"type": "correlation_error", "message": str(e)})
        print(f"Error calculating correlation: {e}")

    # Calculate lag difference
    lag_difference = abs(optimal_lag - lag_phys_minutes)
    
    # Prepare results
    results = {
        "pearson": float(pearson) if pearson is not None else None,
        "spearman": float(spearman) if spearman is not None else None,
        "p_val_permutation": float(p_val_perm) if p_val_perm is not None else None,
        "p_val_pearson": float(p_val_pearson) if p_val_pearson is not None else None,
        "p_val_spearman": float(p_val_spearman) if p_val_spearman is not None else None,
        "significant_flag": bool(significant_flag),
        "optimal_lag": int(optimal_lag),
        "lag_correlation_value": float(lag_corr_value) if lag_corr_value is not None else None,
        "lag_phys": float(lag_phys_minutes),
        "lag_difference": float(lag_difference),
        "date_range": {"start": start_date, "end": end_date},
        "n_samples": len(df_vsw_lagged),
        "warnings": warnings
    }
    
    # Write results to JSON
    os.makedirs(output_dir, exist_ok=True)
    results_path = os.path.join(output_dir, "us1_correlation.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {results_path}")
    
    # Log warnings
    log_quality_warnings(warnings, os.path.join(output_dir, "quality_log.json"))
    
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run solar wind - reconnection analysis pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default="data/processed", help="Output directory")
    args = parser.parse_args()
    
    try:
        results = run_pipeline(args.start, args.end, args.output)
        print("\nPipeline completed successfully.")
        print(f"Significant correlation found: {results['significant_flag']}")
    except Exception as e:
        print(f"\nPipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()