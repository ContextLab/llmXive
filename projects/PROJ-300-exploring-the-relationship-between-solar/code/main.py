"""
Main entry point for the solar wind and geomagnetic tail reconnection analysis pipeline.
This file integrates data cleaning, lag adjustment, and correlation analysis modules
to produce the US-1 results.

File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, PERMUTATION_ITERATIONS
from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample, handle_gaps
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation
from code.analysis.lag_search import find_optimal_lag
from code.viz.plots import plot_scatter, plot_timeseries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_DIR = project_root / "results"
DATA_PROCESSED_DIR = project_root / "data" / "processed"
QUALITY_LOG_PATH = DATA_PROCESSED_DIR / "quality_log.json"

def ensure_directories():
    """Ensure output directories exist."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def log_quality_warnings(warnings_list):
    """
    Log data-quality warnings to a JSON file.
    """
    if not warnings_list:
        logger.info("No quality warnings to log.")
        return

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "warnings": warnings_list
    }

    try:
        # Append to existing log if it exists, otherwise create new
        if QUALITY_LOG_PATH.exists():
            with open(QUALITY_LOG_PATH, 'r') as f:
                try:
                    existing_log = json.load(f)
                    if isinstance(existing_log, list):
                        existing_log.append(log_entry)
                    else:
                        existing_log = [existing_log, log_entry]
                except json.JSONDecodeError:
                    existing_log = [log_entry]
            with open(QUALITY_LOG_PATH, 'w') as f:
                json.dump(existing_log, f, indent=2)
        else:
            with open(QUALITY_LOG_PATH, 'w') as f:
                json.dump([log_entry], f, indent=2)
        
        logger.info(f"Quality warnings logged to {QUALITY_LOG_PATH}")
    except Exception as e:
        logger.error(f"Failed to write quality log: {e}")

def generate_narrative_note(method_used):
    """
    Dynamically generate the narrative note for the results.
    """
    note = (
        f"Analysis performed using {method_used} for significance testing. "
        "Bonferroni correction is conservative for autocorrelated lag searches "
        "and the permutation test is the primary method for significance testing. "
        "Future work should consider adaptive FDR control."
    )
    return note

def run_pipeline(start_date_str, end_date_str):
    """
    Execute the full US-1 analysis pipeline.
    """
    ensure_directories()
    warnings_list = []

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
    except ValueError as e:
        logger.error(f"Invalid date format. Use YYYY-MM-DD. Error: {e}")
        return

    logger.info(f"Fetching solar wind data from {start_date_str} to {end_date_str}...")
    
    # 1. Ingest Data
    try:
        df_sw = fetch_omni_sw((start_date, end_date))
        df_ey = fetch_themis_ey((start_date, end_date))
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        # Fail loudly - do not generate synthetic data
        raise RuntimeError(f"Real data fetch failed. Cannot proceed without real data. Error: {e}")

    if df_sw is None or df_ey is None:
        raise RuntimeError("Data fetch returned None. Cannot proceed.")

    if df_sw.empty or df_ey.empty:
        warnings_list.append("One or both datasets are empty after fetching.")
        log_quality_warnings(warnings_list)
        raise ValueError("Empty dataset after fetching. Check date range and API availability.")

    # 2. Clean and Resample
    logger.info("Cleaning and resampling data...")
    try:
        df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    except Exception as e:
        logger.error(f"Data cleaning failed: {e}")
        raise

    # 3. Handle Gaps
    logger.info("Checking for data gaps...")
    try:
        df_sw_clean = handle_gaps(df_sw_clean)
        df_ey_clean = handle_gaps(df_ey_clean)
    except Exception as e:
        # handle_gaps might return the dataframe or log warnings internally
        logger.warning(f"Gap handling encountered an issue: {e}")
        warnings_list.append(f"Gap handling issue: {str(e)}")

    # 4. Calculate Physics Lag
    logger.info("Calculating physics-based propagation lag...")
    vsw_mean = df_sw_clean['Vsw'].mean()
    l_phys_minutes = calculate_physics_lag(vsw_mean)
    logger.info(f"Physics lag (L_phys): {l_phys_minutes:.2f} minutes")

    # 5. Find Optimal Lag (L*)
    logger.info("Searching for optimal lag...")
    lag_results = find_optimal_lag(
        df_sw_clean['Vsw'], 
        df_ey_clean['Ey'], 
        LAG_WINDOW_MIN, 
        LAG_WINDOW_MAX, 
        LAG_STEP
    )
    optimal_lag = lag_results['optimal_lag']
    max_corr = lag_results['max_correlation']
    logger.info(f"Optimal lag (L*): {optimal_lag} minutes")

    # 6. Apply Optimal Lag Shift
    logger.info("Applying optimal lag shift...")
    vsw_shifted = apply_lag_shift(df_sw_clean['Vsw'], optimal_lag)
    
    # Align series for correlation (drop NaNs introduced by shift)
    common_idx = vsw_shifted.dropna().index.intersection(df_ey_clean['Ey'].dropna().index)
    vsw_final = vsw_shifted.loc[common_idx]
    ey_final = df_ey_clean['Ey'].loc[common_idx]

    if len(vsw_final) < 10:
        warnings_list.append(f"Insufficient data points after lag shift ({len(vsw_final)} points).")
        log_quality_warnings(warnings_list)
        raise ValueError("Insufficient data points for correlation analysis after lag shift.")

    # 7. Calculate Correlation
    logger.info("Calculating correlations...")
    corr_stats = calculate_correlation(vsw_final, ey_final)
    
    # 8. Permutation Test for Significance
    logger.info(f"Running permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    p_val_perm = circular_block_permutation(vsw_final, ey_final, n_iterations=PERMUTATION_ITERATIONS)
    significant_flag = p_val_perm < 0.05

    # 9. Generate Narrative Note
    narrative_note = generate_narrative_note("circular block permutation test")

    # 10. Prepare Results
    results = {
        "timestamp": datetime.now().isoformat(),
        "date_range": {
            "start": start_date_str,
            "end": end_date_str
        },
        "data_quality": {
            "n_points": len(vsw_final),
            "warnings": warnings_list
        },
        "physics_lag": {
            "l_phys_minutes": l_phys_minutes,
            "vsw_mean_km_s": vsw_mean
        },
        "lag_search": {
            "optimal_lag_minutes": optimal_lag,
            "max_correlation": max_corr,
            "lag_correlation_values": lag_results.get('lag_correlation_values', {})
        },
        "correlation": {
            "pearson": corr_stats['pearson'],
            "spearman": corr_stats['spearman'],
            "p_val_pearson": corr_stats['p_val_pearson'],
            "p_val_spearman": corr_stats['p_val_spearman'],
            "p_val_permutation": p_val_perm,
            "significant_flag": significant_flag
        },
        "notes": narrative_note
    }

    # 11. Write Results
    results_json_path = RESULTS_DIR / "us1_correlation.json"
    with open(results_json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results written to {results_json_path}")

    # 12. Generate Plots
    logger.info("Generating plots...")
    try:
        plot_scatter(vsw_final, ey_final, optimal_lag, str(RESULTS_DIR / "plot_scatter.png"))
        logger.info(f"Scatter plot written to {RESULTS_DIR / 'plot_scatter.png'}")
    except Exception as e:
        logger.error(f"Failed to generate scatter plot: {e}")
        warnings_list.append(f"Plot generation failed: {e}")

    try:
        plot_timeseries(df_sw_clean, df_ey_clean, str(RESULTS_DIR / "plot_timeseries.png"))
        logger.info(f"Time series plot written to {RESULTS_DIR / 'plot_timeseries.png'}")
    except Exception as e:
        logger.error(f"Failed to generate time series plot: {e}")
        warnings_list.append(f"Plot generation failed: {e}")

    # 13. Final Quality Log Update
    if warnings_list:
        log_quality_warnings(warnings_list)

    logger.info("Pipeline completed successfully.")
    return results

def main():
    parser = argparse.ArgumentParser(description="Solar Wind and Reconnection Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    
    args = parser.parse_args()
    
    try:
        run_pipeline(args.start, args.end)
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
