"""
Main entry point for the solar wind - geomagnetic tail reconnection analysis pipeline.
This module orchestrates data ingestion, cleaning, lag analysis, correlation calculation,
and visualization.

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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample, handle_gaps
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from code.analysis.lag_search import find_optimal_lag
from code.analysis.sensitivity import analyze_thresholds
from code.viz.plots import plot_scatter, plot_timeseries
from code.config import (
    LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP,
    TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS, PERMUTATION_ITERATIONS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'data' / 'processed' / 'pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    directories = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'results'
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {directories}")

def log_quality_warnings(warnings_list, output_path):
    """Log data-quality warnings to a JSON file."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "warnings": warnings_list
    }
    
    # Load existing log if it exists
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                existing_log = json.load(f)
            if "entries" not in existing_log:
                existing_log["entries"] = []
            existing_log["entries"].append(log_entry)
        except (json.JSONDecodeError, KeyError):
            existing_log = {"entries": [log_entry]}
    else:
        existing_log = {"entries": [log_entry]}
    
    with open(output_path, 'w') as f:
        json.dump(existing_log, f, indent=2)
    logger.info(f"Quality warnings logged to {output_path}")

def generate_narrative_note():
    """Generate the static narrative note for the JSON report as per FR-013."""
    return "Bonferroni correction is conservative for autocorrelated lag searches and that the permutation test is the primary method for significance testing; future work should consider adaptive FDR control."

def run_data_pipeline(start_date, end_date):
    """
    Orchestrate data ingestion and cleaning.
    
    Args:
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.
        
    Returns:
        tuple: (df_sw_clean, df_ey_clean) cleaned DataFrames.
    """
    logger.info(f"Fetching solar wind data from {start_date} to {end_date}...")
    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    try:
        df_sw = fetch_omni_sw((start_dt, end_dt))
        df_ey = fetch_themis_ey((start_dt, end_dt))
    except Exception as e:
        logger.error(f"Failed to fetch real data: {e}")
        raise RuntimeError("Real OMNIWeb/CDAWeb API fetch is required. Network access to NASA APIs is needed.")

    if df_sw.empty or df_ey.empty:
        raise ValueError("Fetched data is empty. Check date range and API connectivity.")

    logger.info("Cleaning and resampling data...")
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    
    # Handle gaps
    warnings = []
    df_sw_clean = handle_gaps(df_sw_clean)
    df_ey_clean = handle_gaps(df_ey_clean)
    
    if df_sw_clean.empty or df_ey_clean.empty:
        raise ValueError("Data became empty after cleaning/gap handling.")

    # Save cleaned data
    output_path = project_root / 'data' / 'processed' / 'cleaned_data.csv'
    combined_df = pd.concat([df_sw_clean.reset_index(drop=True), df_ey_clean.reset_index(drop=True)], axis=1)
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Cleaned data saved to {output_path}")

    return df_sw_clean, df_ey_clean

def run_analysis_pipeline(df_sw, df_ey):
    """
    Orchestrate the core analysis pipeline.
    
    Args:
        df_sw (pd.DataFrame): Cleaned solar wind data.
        df_ey (pd.DataFrame): Cleaned THEMIS data.
        
    Returns:
        dict: Results dictionary containing correlation stats, lags, and sensitivity.
    """
    logger.info("Starting analysis pipeline...")
    
    # 1. Calculate physics-based lag
    vsw_mean = df_sw['Vsw'].mean()
    l_phys = calculate_physics_lag(vsw_mean)
    logger.info(f"Physics-based lag L_phys: {l_phys:.2f} minutes")

    # 2. Apply lag shift
    # Assuming 5-minute cadence from clean_and_resample
    cadence = 5 
    lag_periods = int(l_phys / cadence)
    df_sw_lagged = df_sw.copy()
    df_sw_lagged['Vsw'] = apply_lag_shift(df_sw['Vsw'], lag_periods)
    
    # Drop NaNs introduced by shift
    valid_mask = df_sw_lagged['Vsw'].notna() & df_ey['Ey'].notna()
    x = df_sw_lagged.loc[valid_mask, 'Vsw']
    y = df_ey.loc[valid_mask, 'Ey']

    if len(x) < 10:
        raise ValueError("Insufficient data points after lagging and alignment.")

    # 3. Find optimal lag
    logger.info(f"Searching optimal lag in window [{LAG_WINDOW_MIN}, {LAG_WINDOW_MAX}] with step {LAG_STEP}...")
    lag_results = find_optimal_lag(df_sw['Vsw'], df_ey['Ey'], LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP)
    optimal_lag = lag_results['optimal_lag']
    max_corr = lag_results['max_correlation']
    
    lag_difference = abs(optimal_lag - l_phys)
    logger.info(f"Optimal lag L*: {optimal_lag} min, |L* - L_phys| = {lag_difference:.2f} min")

    # 4. Calculate correlations at optimal lag
    # Re-apply optimal lag for final correlation
    optimal_periods = int(optimal_lag / cadence)
    x_opt = apply_lag_shift(df_sw['Vsw'], optimal_periods)
    valid_mask_opt = x_opt.notna() & df_ey['Ey'].notna()
    x_final = x_opt[valid_mask_opt]
    y_final = df_ey['Ey'][valid_mask_opt]

    corr_stats = calculate_correlation(x_final, y_final)
    logger.info(f"Pearson: {corr_stats['pearson']:.4f}, Spearman: {corr_stats['spearman']:.4f}")

    # 5. Permutation test for p-value
    logger.info(f"Running circular block permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    p_val = circular_block_permutation(x_final, y_final, n_iterations=PERMUTATION_ITERATIONS)
    logger.info(f"Permutation p-value: {p_val:.4f}")

    # 6. Bootstrap confidence interval
    logger.info(f"Running moving block bootstrap ({BOOTSTRAP_ITERATIONS} iterations)...")
    ci_lower, ci_upper = moving_block_bootstrap(x_final, y_final, n_iterations=BOOTSTRAP_ITERATIONS)
    logger.info(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    # 7. Sensitivity analysis
    logger.info("Running sensitivity analysis on thresholds [400, 500, 600] km/s...")
    sensitivity_results = analyze_thresholds(df_sw['Vsw'], df_ey['Ey'], [400, 500, 600])

    # 8. Narrative note
    notes = generate_narrative_note()

    results = {
        "pearson": corr_stats['pearson'],
        "spearman": corr_stats['spearman'],
        "p_val_permutation": p_val,
        "optimal_lag": optimal_lag,
        "lag_difference": lag_difference,
        "ci_bootstrap": {"lower": ci_lower, "upper": ci_upper},
        "sensitivity_table": sensitivity_results,
        "notes": notes,
        "metadata": {
            "vsw_mean": vsw_mean,
            "l_phys": l_phys,
            "data_points": len(x_final)
        }
    }

    return results

def run_pipeline(start_date, end_date):
    """
    Full pipeline execution: ingest, clean, analyze, visualize, save.
    """
    ensure_directories()
    warnings_log_path = project_root / 'data' / 'processed' / 'quality_log.json'
    results_path = project_root / 'results' / 'us1_correlation.json'
    scatter_path = project_root / 'results' / 'plot_scatter.png'
    timeseries_path = project_root / 'results' / 'plot_timeseries.png'

    try:
        # Data Pipeline
        df_sw, df_ey = run_data_pipeline(start_date, end_date)
        
        # Analysis Pipeline
        results = run_analysis_pipeline(df_sw, df_ey)

        # Save Results
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {results_path}")

        # Visualizations
        # Prepare data for plotting (apply optimal lag)
        optimal_lag = results['optimal_lag']
        cadence = 5
        lag_periods = int(optimal_lag / cadence)
        df_sw_lagged = df_sw.copy()
        df_sw_lagged['Vsw'] = apply_lag_shift(df_sw['Vsw'], lag_periods)
        
        # Merge on index for plotting
        plot_df = pd.concat([df_sw_lagged['Vsw'], df_ey['Ey']], axis=1).dropna()
        
        plot_scatter(plot_df['Vsw'], plot_df['Ey'], optimal_lag, str(scatter_path))
        logger.info(f"Scatter plot saved to {scatter_path}")

        plot_timeseries(df_sw, df_ey, str(timeseries_path))
        logger.info(f"Time series plot saved to {timeseries_path}")

        # Log any quality warnings (empty list if none captured in this run)
        log_quality_warnings([], warnings_log_path)

        logger.info("Pipeline completed successfully.")
        return results

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description="Solar Wind - Reconnection Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    run_pipeline(args.start, args.end)

if __name__ == "__main__":
    main()
