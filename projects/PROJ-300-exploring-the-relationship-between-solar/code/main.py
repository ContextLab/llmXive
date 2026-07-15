"""
Main pipeline orchestrator for Solar Wind - Geomagnetic Tail Reconnection Analysis.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional, List
import pandas as pd
import numpy as np

# Project imports
from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample
from data.lag import calculate_physics_lag, apply_lag_shift
from analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from analysis.lag_search import find_optimal_lag
from analysis.sensitivity import analyze_thresholds
from viz.plots import plot_scatter, plot_timeseries
from config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS

def log_quality_warnings(df_omni: pd.DataFrame, df_themis: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Analyze data quality of ingested datasets and log warnings to a JSON file.
    
    Checks performed:
    1. NaN counts per column for both datasets.
    2. Percentage of missing data relative to expected time steps.
    3. Outlier detection (values > 5 standard deviations from mean) for Vsw and Ey.
    4. Data continuity gaps (time differences > 2x expected cadence).
    
    Args:
        df_omni: DataFrame with OMNI solar wind data (timestamp, Vsw, Bz).
        df_themis: DataFrame with THEMIS reconnection data (timestamp, Ey).
        output_path: Path to write the quality_log.json file.
        
    Returns:
        Dictionary containing the quality report.
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
        json.dump(report, f, indent=2, default=str)
    
    print(f"Quality log written to: {output_path}")
    return report

def run_pipeline(start_date: str, end_date: str, output_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Execute the full analysis pipeline.
    
    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        output_dir: Directory for output artifacts.
        
    Returns:
        Dictionary containing the final analysis results.
    """
    print(f"Starting pipeline for {start_date} to {end_date}")
    
    # 1. Ingest Data
    print("Fetching OMNI Solar Wind data...")
    try:
        df_omni = fetch_omni_sw((start_date, end_date))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OMNI data: {e}")
        
    print("Fetching THEMIS Ey data...")
    try:
        df_themis = fetch_themis_ey((start_date, end_date))
    except Exception as e:
        raise RuntimeError(f"Failed to fetch THEMIS data: {e}")

    # 2. Quality Check (FR-009)
    quality_log_path = os.path.join(output_dir, "quality_log.json")
    quality_report = log_quality_warnings(df_omni, df_themis, quality_log_path)

    # 3. Clean and Resample
    print("Cleaning and resampling data...")
    df_omni_clean, df_themis_clean = clean_and_resample(df_omni, df_themis)

    # 4. Calculate Physics Lag
    print("Calculating physics-based lag...")
    try:
        l_phys = calculate_physics_lag(df_omni_clean)
    except Exception as e:
        raise RuntimeError(f"Failed to calculate physics lag: {e}")

    # 5. Find Optimal Lag
    print("Searching for optimal lag...")
    try:
        optimal_lag, lag_correlation, lag_results = find_optimal_lag(
            df_omni_clean, df_themis_clean,
            min_lag=LAG_WINDOW_MIN,
            max_lag=LAG_WINDOW_MAX,
            step=LAG_STEP
        )
    except Exception as e:
        raise RuntimeError(f"Failed to find optimal lag: {e}")

    # 6. Apply Optimal Lag Shift
    print(f"Applying optimal lag shift: {optimal_lag} min")
    df_omni_shifted, df_themis_shifted = apply_lag_shift(df_omni_clean, df_themis_clean, optimal_lag)

    # 7. Calculate Correlations
    print("Calculating correlations...")
    pearson, spearman = calculate_correlation(df_omni_shifted['Vsw'], df_themis_shifted['Ey'])

    # 8. Permutation Test (FR-005)
    print("Running permutation test...")
    p_val_perm = None
    significant = False
    try:
        p_val_perm = circular_block_permutation(
            df_omni_shifted['Vsw'], df_themis_shifted['Ey'],
            iterations=PERMUTATION_ITERATIONS
        )
        significant = p_val_perm < 0.05
    except Exception as e:
        print(f"Permutation test failed: {e}")

    # 9. Bootstrap Confidence Intervals (FR-006)
    print("Running bootstrap analysis...")
    ci_pearson = None
    ci_spearman = None
    try:
        ci_pearson, ci_spearman = moving_block_bootstrap(
            df_omni_shifted['Vsw'], df_themis_shifted['Ey'],
            iterations=BOOTSTRAP_ITERATIONS
        )
    except Exception as e:
        print(f"Bootstrap analysis failed: {e}")

    # 10. Sensitivity Analysis (FR-007)
    print("Running sensitivity analysis...")
    try:
        sensitivity_table = analyze_thresholds(
            df_omni_clean, df_themis_clean,
            thresholds=[400, 500, 600]
        )
    except Exception as e:
        print(f"Sensitivity analysis failed: {e}")
        sensitivity_table = {}

    # 11. Generate Visualizations
    print("Generating plots...")
    try:
        plot_scatter(df_omni_shifted['Vsw'], df_themis_shifted['Ey'], optimal_lag, output_dir)
        plot_timeseries(df_omni_shifted, df_themis_shifted, optimal_lag, output_dir)
    except Exception as e:
        print(f"Plot generation failed: {e}")

    # 12. Compile Results
    results = {
        "metadata": {
            "start_date": start_date,
            "end_date": end_date,
            "analysis_timestamp": datetime.now().isoformat(),
            "optimal_lag_minutes": optimal_lag,
            "physics_lag_minutes": l_phys,
            "lag_difference": abs(optimal_lag - l_phys)
        },
        "correlations": {
            "pearson": float(pearson) if pearson is not None else None,
            "spearman": float(spearman) if spearman is not None else None,
            "pearson_ci_95": ci_pearson,
            "spearman_ci_95": ci_spearman
        },
        "significance": {
            "p_value_permutation": float(p_val_perm) if p_val_perm is not None else None,
            "significant_at_0_05": significant
        },
        "sensitivity_table": sensitivity_table,
        "quality_log_path": quality_log_path
    }

    # FR-013: Add note if permutation test succeeded
    if p_val_perm is not None:
        results["notes"] = "Note: Bonferroni correction is conservative for autocorrelated lag searches; the permutation test (FR-005) is the primary method for significance testing. Future work should consider adaptive FDR control."

    # Save JSON report
    report_path = os.path.join(output_dir, "us1_correlation.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Pipeline complete. Report saved to {report_path}")
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Solar Wind - Reconnection Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args.start, args.end, args.output)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()