"""
Main pipeline for US-1: Lag-Adjusted Coupling Analysis.
This file orchestrates the data ingestion, cleaning, lag application,
and correlation analysis for the solar wind and geomagnetic tail reconnection study.
"""
import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import numpy as np

from config import (
    LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP,
    PERMUTATION_ITERATIONS, BOOTSTRAP_ITERATIONS
)
from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample, handle_gaps
from data.lag import calculate_physics_lag, apply_lag_shift
from analysis.correlation import calculate_correlation, circular_block_permutation
from analysis.lag_search import find_optimal_lag
from viz.plots import plot_scatter, plot_timeseries

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR = Path("data/processed")
QUALITY_LOG_PATH = RESULTS_DIR / "quality_log.json"
JSON_REPORT_PATH = RESULTS_DIR / "us1_correlation.json"

def log_quality_warnings(warnings: list):
    """
    Log data-quality warnings to data/processed/quality_log.json.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    existing_warnings = []
    if QUALITY_LOG_PATH.exists():
        try:
            with open(QUALITY_LOG_PATH, 'r') as f:
                existing_warnings = json.load(f)
        except json.JSONDecodeError:
            existing_warnings = []

    existing_warnings.extend(warnings)

    with open(QUALITY_LOG_PATH, 'w') as f:
        json.dump(existing_warnings, f, indent=2)
    logger.info(f"Logged {len(warnings)} warnings to {QUALITY_LOG_PATH}")

def generate_narrative_note(method: str) -> str:
    """
    Dynamically generate the narrative note for the JSON report.
    """
    note = (
        f"Analysis performed using {method}. "
        "Bonferroni correction is conservative for autocorrelated lag searches; "
        "the permutation test is the primary method for significance testing. "
        "Future work should consider adaptive FDR control."
    )
    return note

def run_pipeline(start_date: str, end_date: str):
    """
    Execute the full US-1 pipeline:
    1. Fetch OMNI and THEMIS data.
    2. Clean and resample.
    3. Calculate physics-based lag.
    4. Search for optimal lag.
    5. Compute correlations and significance.
    6. Generate plots and reports.
    """
    logger.info(f"Starting pipeline for {start_date} to {end_date}")
    warnings = []

    # 1. Ingest Data
    try:
        logger.info("Fetching solar wind data (OMNI)...")
        df_sw = fetch_omni_sw((start_date, end_date))
        if df_sw is None or df_sw.empty:
            raise ValueError("Failed to fetch OMNI data or data is empty.")
    except Exception as e:
        logger.error(f"Failed to fetch OMNI data: {e}")
        raise

    try:
        logger.info("Fetching THEMIS data (Ey)...")
        df_ey = fetch_themis_ey((start_date, end_date))
        if df_ey is None or df_ey.empty:
            raise ValueError("Failed to fetch THEMIS data or data is empty.")
    except Exception as e:
        logger.error(f"Failed to fetch THEMIS data: {e}")
        raise

    # 2. Clean and Resample
    logger.info("Cleaning and resampling data...")
    try:
        df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        raise

    # Check for gaps
    if len(df_sw_clean) < len(df_sw) or len(df_ey_clean) < len(df_ey):
        warnings.append({
            "type": "data_loss",
            "message": "Data rows were dropped during cleaning/resampling."
        })

    # 3. Calculate Physics Lag
    vsw_mean = df_sw_clean['Vsw'].mean()
    if pd.isna(vsw_mean) or vsw_mean <= 0:
        raise ValueError("Invalid mean solar wind speed for lag calculation.")
    
    lag_phys = calculate_physics_lag(vsw_mean)
    logger.info(f"Calculated physics lag: {lag_phys:.2f} minutes")

    # 4. Lag Search
    logger.info("Searching for optimal lag...")
    # Ensure we use integer minutes for the search
    min_lag = int(LAG_WINDOW_MIN)
    max_lag = int(LAG_WINDOW_MAX)
    step = int(LAG_STEP)
    
    lag_results = find_optimal_lag(
        df_sw_clean['Vsw'], 
        df_ey_clean['Ey'], 
        min_lag, 
        max_lag, 
        step
    )
    
    optimal_lag = lag_results['optimal_lag']
    max_corr = lag_results['max_correlation']
    logger.info(f"Optimal lag found: {optimal_lag} minutes (Correlation: {max_corr:.4f})")

    # 5. Apply Optimal Lag and Compute Final Stats
    # Shift Vsw by optimal_lag to align with Ey
    # Note: apply_lag_shift expects a Series and lag in minutes (assuming 5min cadence)
    vsw_shifted = apply_lag_shift(df_sw_clean['Vsw'], optimal_lag)
    
    # Drop NaNs introduced by shift
    valid_indices = vsw_shifted.notna() & df_ey_clean['Ey'].notna()
    vsw_final = vsw_shifted[valid_indices]
    ey_final = df_ey_clean['Ey'][valid_indices]

    if len(vsw_final) < 10:
        raise ValueError("Insufficient data points after lag application.")

    # Calculate Correlations
    corr_stats = calculate_correlation(vsw_final, ey_final)
    
    # Permutation Test for Significance
    logger.info(f"Running permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    p_val_perm = circular_block_permutation(
        vsw_final, 
        ey_final, 
        n_iterations=PERMUTATION_ITERATIONS
    )
    
    significant_flag = p_val_perm < 0.05

    # 6. Generate Report
    report = {
        "start_date": start_date,
        "end_date": end_date,
        "data_points": len(vsw_final),
        "physics_lag_minutes": round(lag_phys, 2),
        "optimal_lag_minutes": optimal_lag,
        "lag_difference": round(abs(optimal_lag - lag_phys), 2),
        "pearson": round(corr_stats['pearson'], 4),
        "spearman": round(corr_stats['spearman'], 4),
        "p_val_pearson": round(corr_stats['p_val_pearson'], 4),
        "p_val_spearman": round(corr_stats['p_val_spearman'], 4),
        "p_val_permutation": round(p_val_perm, 4),
        "significant_flag": significant_flag,
        "n_permutation_iterations": PERMUTATION_ITERATIONS,
        "notes": generate_narrative_note("circular block permutation test")
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(JSON_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Report saved to {JSON_REPORT_PATH}")

    # 7. Generate Plots
    logger.info("Generating plots...")
    plot_scatter(vsw_final, ey_final, optimal_lag, str(RESULTS_DIR / "plot_scatter.png"))
    plot_timeseries(df_sw_clean, df_ey_clean, str(RESULTS_DIR / "plot_timeseries.png"))
    logger.info("Plots saved.")

    # 8. Log Warnings
    if warnings:
        log_quality_warnings(warnings)

    return report

def main():
    parser = argparse.ArgumentParser(description="Run US-1 Solar Wind Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    try:
        run_pipeline(args.start, args.end)
        print("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
