"""
Main pipeline entry point for PROJ-300.
Orchestrates data ingestion, cleaning, lag application, and correlation analysis.
File: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional
import pandas as pd
import argparse

# Import project modules
from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation
from code.analysis.lag_search import find_optimal_lag
from code.viz.plots import plot_scatter, plot_timeseries
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, BOOTSTRAP_ITERATIONS

def log_quality_warnings(warnings: list, output_path: str):
    """
    Log data quality warnings to a JSON file.
    FR-009: Log data-quality warnings to data/processed/quality_log.json.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({"warnings": warnings, "timestamp": datetime.now().isoformat()}, f, indent=2)

def run_pipeline(start_date: str, end_date: str, output_dir: str = "data/processed"):
    """
    Execute the full analysis pipeline for User Story 1.
    
    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        output_dir: Directory to save results.
    
    Returns:
        Dict containing analysis results.
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

    # Check for empty data
    if df_omni.empty or df_themis.empty:
        raise ValueError("One or both datasets are empty after fetching.")

    warnings = []
    if df_omni.isnull().sum().sum() > 0:
        warnings.append("OMNI data contained NaN values before cleaning.")
    if df_themis.isnull().sum().sum() > 0:
        warnings.append("THEMIS data contained NaN values before cleaning.")

    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    try:
        df_clean_omni, df_clean_themis = clean_and_resample(df_omni, df_themis)
    except ValueError as e:
        raise RuntimeError(f"Data alignment failed: {e}")

    # 3. Calculate Physics Lag
    print("Calculating physics-based lag...")
    vsw_mean = df_clean_omni['Vsw'].mean()
    l_phys = calculate_physics_lag(vsw_mean)
    print(f"Physics Lag (L_phys): {l_phys:.2f} minutes")

    # 4. Find Optimal Lag (L*)
    print("Searching for optimal lag...")
    optimal_lag, corr_val = find_optimal_lag(
        df_clean_omni['Vsw'], 
        df_clean_themis['Ey'], 
        min_lag=LAG_WINDOW_MIN, 
        max_lag=LAG_WINDOW_MAX, 
        step=LAG_STEP
    )
    print(f"Optimal Lag (L*): {optimal_lag} minutes (Correlation: {corr_val:.4f})")

    # 5. Apply Optimal Lag Shift
    # We shift the solar wind data forward by the optimal lag to align with the tail response
    df_shifted_omni = apply_lag_shift(df_clean_omni, optimal_lag, 'Vsw')
    
    # Re-merge to ensure alignment after shift (timestamps must match)
    # Since we shifted timestamps, we need to re-merge on the new timestamps
    merged_df = pd.merge(
        df_shifted_omni[['timestamp', 'Vsw']], 
        df_clean_themis[['timestamp', 'Ey']], 
        on='timestamp', 
        how='inner'
    )

    if merged_df.empty:
        raise RuntimeError("No data points aligned after applying optimal lag shift.")

    # 6. Calculate Correlation
    print("Calculating correlation coefficients...")
    pearson, p_val_pearson = calculate_correlation(merged_df['Vsw'], merged_df['Ey'], method='pearson')
    spearman, p_val_spearman = calculate_correlation(merged_df['Vsw'], merged_df['Ey'], method='spearman')
    
    print(f"Pearson: {pearson:.4f} (p={p_val_pearson:.4f})")
    print(f"Spearman: {spearman:.4f} (p={p_val_spearman:.4f})")

    # 7. Permutation Test for Significance
    print("Running circular block permutation test...")
    p_val_perm, is_significant = circular_block_permutation(
        merged_df['Vsw'], 
        merged_df['Ey'], 
        alpha=0.05
    )
    print(f"Permutation p-value: {p_val_perm:.4f}, Significant: {is_significant}")

    # 8. Generate Plots
    print("Generating plots...")
    os.makedirs(output_dir, exist_ok=True)
    plot_scatter(merged_df['Vsw'], merged_df['Ey'], optimal_lag, output_path=f"{output_dir}/plot_scatter.png")
    plot_timeseries(merged_df['timestamp'], merged_df['Vsw'], merged_df['Ey'], optimal_lag, output_path=f"{output_dir}/plot_timeseries.png")

    # 9. Prepare Results
    results = {
        "start_date": start_date,
        "end_date": end_date,
        "vsw_mean_kms": float(vsw_mean),
        "l_phys_min": float(l_phys),
        "optimal_lag_min": int(optimal_lag),
        "lag_difference_min": float(abs(optimal_lag - l_phys)),
        "pearson": float(pearson),
        "p_val_pearson": float(p_val_pearson),
        "spearman": float(spearman),
        "p_val_spearman": float(p_val_spearman),
        "p_val_permutation": float(p_val_perm),
        "significant_flag": bool(is_significant),
        "n_samples": len(merged_df)
    }

    # Save JSON Report
    json_path = f"{output_dir}/us1_correlation.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {json_path}")

    # 10. Log Quality Warnings
    log_warnings_path = f"{output_dir}/quality_log.json"
    log_quality_warnings(warnings, log_warnings_path)
    print(f"Quality log saved to {log_warnings_path}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Run Solar Wind - Tail Reconnection Analysis")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default="data/processed", help="Output directory")
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args.start, args.end, args.output)
        print("Pipeline completed successfully.")
    except Exception as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
