"""
Main entry point for the Solar Wind - Geomagnetic Tail Reconnection Analysis Pipeline.
This file implements the cohesive pipeline for User Story 1 (US-1) by integrating
data cleaning, lag calculation, and correlation analysis.

File Path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import numpy as np

# Relative imports based on project structure
from .data.ingest import fetch_omni_sw, fetch_themis_ey
from .data.clean import clean_and_resample
from .data.lag import calculate_physics_lag, apply_lag_shift
from .analysis.correlation import calculate_correlation, circular_block_permutation
from .analysis.lag_search import find_optimal_lag
from .viz.plots import plot_scatter, plot_timeseries
from .config import (
    LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP,
    EARTH_RADIUS_KM, TAIL_DISTANCE_RE, K_PROPAGATION,
    BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS
)

def log_quality_warnings(warnings: Dict[str, Any], output_path: str) -> None:
    """
    Log data-quality warnings to a JSON file.
    
    Args:
        warnings: Dictionary containing warning messages and metadata.
        output_path: Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(warnings, f, indent=2, default=str)
    print(f"Quality warnings logged to {output_path}")

def run_pipeline(start_date: str, end_date: str, output_dir: str = "results") -> Dict[str, Any]:
    """
    Execute the full analysis pipeline for User Story 1.
    
    1. Fetch real data from OMNIWeb and CDAWeb.
    2. Clean and resample data.
    3. Calculate physics-based lag and find optimal lag.
    4. Compute correlations and permutation tests.
    5. Generate plots and JSON report.
    
    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        output_dir: Directory to save results.
        
    Returns:
        Dictionary containing analysis results.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)

    # 1. Ingest Data
    print(f"Fetching data from {start_date} to {end_date}...")
    try:
        df_omni = fetch_omni_sw((start_date, end_date))
        df_themis = fetch_themis_ey((start_date, end_date))
    except Exception as e:
        # Fail loudly if real data cannot be fetched
        raise RuntimeError(f"Failed to fetch real data from NASA APIs: {e}")

    # Log initial data quality
    warnings = {
        "timestamp": datetime.now().isoformat(),
        "date_range": f"{start_date} to {end_date}",
        "raw_counts": {
            "omni": len(df_omni),
            "themis": len(df_themis)
        },
        "issues": []
    }

    if df_omni.empty or df_themis.empty:
        warnings["issues"].append("One or more datasets are empty after fetch.")
        log_quality_warnings(warnings, "data/processed/quality_log.json")
        raise ValueError("Cannot proceed with empty datasets.")

    # 2. Clean and Resample
    print("Cleaning and resampling data...")
    df_vsw, df_ey = clean_and_resample(df_omni, df_themis)
    
    # Update warnings with cleaning stats
    warnings["cleaned_counts"] = {
        "vsw": len(df_vsw),
        "ey": len(df_ey)
    }
    nan_count_vsw = df_vsw['Vsw'].isna().sum()
    nan_count_ey = df_ey['Ey'].isna().sum()
    if nan_count_vsw > 0 or nan_count_ey > 0:
        warnings["issues"].append(f"NaNs remaining after cleaning: Vsw={nan_count_vsw}, Ey={nan_count_ey}")
    
    log_quality_warnings(warnings, "data/processed/quality_log.json")

    # 3. Calculate Physics Lag
    print("Calculating physics-based lag...")
    # Apply lag shift based on physics first
    L_phys = calculate_physics_lag(df_vsw)
    df_vsw_lagged = apply_lag_shift(df_vsw, df_ey, L_phys)
    
    # 4. Find Optimal Lag (L*)
    print("Searching for optimal lag...")
    # We sweep the window around the physics lag or the defined window
    # Using the defined window from config
    optimal_lag, lag_corr_val = find_optimal_lag(df_vsw, df_ey, LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP)
    
    # Apply the optimal lag shift for the final analysis
    df_vsw_opt, df_ey_opt = apply_lag_shift(df_vsw, df_ey, optimal_lag, return_aligned=True)
    
    # 5. Calculate Correlations
    print("Calculating correlations...")
    pearson, spearman, p_pearson, p_spearman = calculate_correlation(
        df_vsw_opt['Vsw'], df_ey_opt['Ey']
    )

    # 6. Permutation Test for Significance
    print(f"Running permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    try:
        p_val_permutation, significant = circular_block_permutation(
            df_vsw_opt['Vsw'], df_ey_opt['Ey'], 
            iterations=PERMUTATION_ITERATIONS
        )
        permutation_success = True
    except Exception as e:
        print(f"Warning: Permutation test failed: {e}")
        p_val_permutation = None
        significant = False
        permutation_success = False

    # 7. Prepare Results
    results = {
        "date_range": {"start": start_date, "end": end_date},
        "data_stats": {
            "n_points": len(df_vsw_opt),
            "physics_lag_minutes": float(L_phys) if L_phys else None,
            "optimal_lag_minutes": float(optimal_lag)
        },
        "correlation": {
            "pearson": float(pearson),
            "spearman": float(spearman),
            "p_val_permutation": float(p_val_permutation) if p_val_permutation is not None else None,
            "significant_flag": bool(significant)
        },
        "lag_difference": abs(float(optimal_lag) - float(L_phys)) if L_phys else None,
        "notes": []
    }

    # FR-013: Insert narrative note if permutation test succeeded
    if permutation_success:
        results["notes"].append(
            "Note: Bonferroni correction is conservative for autocorrelated lag searches; "
            "the permutation test (FR-005) is the primary method for significance testing. "
            "Future work should consider adaptive FDR control."
        )

    # 8. Generate Plots
    print("Generating plots...")
    try:
        plot_scatter(df_vsw_opt['Vsw'], df_ey_opt['Ey'], optimal_lag, 
                     output_path=os.path.join(output_dir, "plot_scatter.png"))
        plot_timeseries(df_vsw, df_ey, optimal_lag,
                        output_path=os.path.join(output_dir, "plot_timeseries.png"))
    except Exception as e:
        print(f"Warning: Plot generation failed: {e}")

    # 9. Save JSON Report
    report_path = os.path.join(output_dir, "us1_correlation.json")
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Pipeline complete. Results saved to {report_path}")
    return results

def main():
    """
    CLI entry point.
    Usage: python -m main --start YYYY-MM-DD --end YYYY-MM-DD
    """
    import argparse
    parser = argparse.ArgumentParser(description="Solar Wind Reconnection Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", default="results", help="Output directory")
    args = parser.parse_args()

    try:
        run_pipeline(args.start, args.end, args.output)
    except Exception as e:
        print(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()