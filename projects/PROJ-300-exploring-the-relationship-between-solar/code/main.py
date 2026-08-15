"""
Main orchestration module for the Solar Wind - Geomagnetic Tail Reconnection analysis.
"""
import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
import pandas as pd
import portalocker

# Local imports
from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample
from data.lag import calculate_l_phys, log_lag_derivation
from analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from analysis.lag_search import find_optimal_lag
from analysis.sensitivity import analyze_thresholds
from viz.plots import plot_scatter, plot_timeseries

# Setup logging
def setup_logging():
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def log_data_quality_warnings(warnings: list, logger: logging.Logger = None) -> None:
    """
    Log data-quality warnings to data/processed/quality_log.json.
    
    Uses portalocker to prevent race conditions with log_lag_derivation.
    
    Args:
        warnings: List of warning dictionaries.
        logger: Optional logger instance.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    log_path = "data/processed/quality_log.json"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    # Read existing log if it exists
    existing_logs = []
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_logs = json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Existing quality_log.json is not valid JSON, starting fresh.")
            existing_logs = []
    
    # Add new warnings
    for warning in warnings:
        # Ensure required keys are present
        if not all(key in warning for key in ['timestamp', 'level', 'source', 'message']):
            warning['timestamp'] = datetime.utcnow().isoformat()
            warning['level'] = 'WARN'
            if 'source' not in warning:
                warning['source'] = 'pipeline'
            if 'message' not in warning:
                warning['message'] = 'Unknown warning'
        existing_logs.append(warning)
    
    # Write with file locking
    with open(log_path, 'w') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        try:
            json.dump(existing_logs, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        finally:
            portalocker.unlock(f)
    
    logger.info(f"Logged {len(warnings)} warnings to {log_path}")

def run_data_pipeline(start_date: str, end_date: str, logger: logging.Logger = None) -> pd.DataFrame:
    """
    Orchestrate data ingestion and cleaning.
    
    Fetches solar wind (Vsw, Bz) and THEMIS (Ey) data, cleans and resamples them,
    and saves the result to data/processed/cleaned_data.csv.
    
    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        logger: Optional logger instance.
        
    Returns:
        Combined cleaned DataFrame with columns: timestamp, Vsw, Bz, Ey.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info(f"Starting data pipeline for {start_date} to {end_date}")
    
    # Parse dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = (start, end)
    
    # Fetch data
    logger.info("Fetching OMNI solar wind data...")
    df_sw = fetch_omni_sw(date_range)
    
    logger.info("Fetching THEMIS Ey data...")
    df_ey = fetch_themis_ey(date_range)
    
    # Clean and resample
    logger.info("Cleaning and resampling data...")
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    
    # Merge on timestamp
    df_combined = pd.merge(
        df_sw_clean, 
        df_ey_clean, 
        on='timestamp', 
        how='inner',
        suffixes=('_sw', '_ey')
    )
    
    # Rename columns for clarity if needed (ensure standard names)
    # Assuming clean_and_resample returns 'timestamp', 'Vsw', 'Bz' for sw and 'timestamp', 'Ey' for ey
    # Merge might create duplicate timestamp columns if not careful, but 'on' handles that.
    # We need to ensure column names are exactly as expected downstream.
    # Let's enforce: timestamp, Vsw, Bz, Ey
    if 'Vsw' in df_combined.columns and 'Bz' in df_combined.columns and 'Ey' in df_combined.columns:
        pass # Good
    else:
        # Fallback renaming if the merge produced suffixes unexpectedly
        if 'Vsw_sw' in df_combined.columns:
            df_combined.rename(columns={'Vsw_sw': 'Vsw', 'Bz_sw': 'Bz', 'Ey_ey': 'Ey'}, inplace=True)
    
    # Save to disk
    output_path = "data/processed/cleaned_data.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_combined.to_csv(output_path, index=False)
    logger.info(f"Saved cleaned data to {output_path}")
    
    return df_combined

def run_analysis_pipeline(df: pd.DataFrame, logger: logging.Logger = None) -> dict:
    """
    Orchestrate the core analysis pipeline.
    
    Args:
        df: Cleaned DataFrame with columns timestamp, Vsw, Bz, Ey.
        logger: Optional logger instance.
        
    Returns:
        Dictionary containing analysis results.
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    logger.info("Starting analysis pipeline")
    
    # Extract series
    vsw = df['Vsw']
    ey = df['Ey']
    timestamps = df['timestamp']
    
    # Calculate physics-based lag
    vsw_mean = vsw.mean()
    l_phys = calculate_l_phys(vsw_mean)
    log_lag_derivation(vsw_mean, l_phys)
    logger.info(f"Calculated physics-based lag: {l_phys:.2f} minutes")
    
    # Find optimal lag
    # Use config values if not passed, but task description implies using defaults
    # From T003a: LAG_WINDOW_MIN=30, LAG_WINDOW_MAX=90, LAG_STEP=5
    # We need to import these or use them directly. Assuming they are in config.
    from config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP
    
    lag_results = find_optimal_lag(vsw, ey, LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP)
    optimal_lag = lag_results['optimal_lag']
    max_corr = lag_results['max_correlation']
    logger.info(f"Optimal lag found: {optimal_lag} minutes, correlation: {max_corr:.4f}")
    
    # Apply lag shift to Vsw
    vsw_lagged = apply_lag_shift(vsw, optimal_lag)
    
    # Calculate correlation on lagged data
    corr_stats = calculate_correlation(vsw_lagged, ey)
    pearson = corr_stats['pearson']
    spearman = corr_stats['spearman']
    logger.info(f"Correlation (Pearson): {pearson:.4f}, (Spearman): {spearman:.4f}")
    
    # Permutation test for p-value
    p_val = circular_block_permutation(vsw_lagged, ey)
    logger.info(f"Permutation p-value: {p_val:.4f}")
    
    # Bootstrap for confidence interval
    ci_lower, ci_upper = moving_block_bootstrap(vsw_lagged, ey)
    logger.info(f"Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    # Sensitivity analysis
    thresholds = [400, 500, 600]
    sensitivity_results = analyze_thresholds(vsw, ey, thresholds)
    
    # Log any data quality warnings
    warnings = []
    if vsw.isna().any() or ey.isna().any():
        warnings.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": "WARN",
            "source": "data_cleaning",
            "message": "NaN values detected in input data after cleaning."
        })
    if warnings:
        log_data_quality_warnings(warnings, logger)
    
    # Compile results
    results = {
        "pearson": float(pearson),
        "spearman": float(spearman),
        "p_val_permutation": float(p_val),
        "optimal_lag": int(optimal_lag),
        "lag_difference": float(abs(optimal_lag - l_phys)),
        "ci_bootstrap": [float(ci_lower), float(ci_upper)],
        "sensitivity_table": sensitivity_results,
        "notes": [
            f"Analysis performed on {len(df)} data points.",
            "Reference frame: GSM for Ey, Solar Wind Rest Frame for Vsw (approximate).",
            f"Physics-based lag (L_phys) calculated as {l_phys:.2f} minutes."
        ]
    }
    
    # Save results
    results_path = "results/us1_correlation.json"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved results to {results_path}")
    
    return results

def run_pipeline(start_date: str, end_date: str, logger: logging.Logger = None) -> None:
    """
    Full pipeline orchestration: ingest, clean, analyze, visualize.
    
    Args:
        start_date: Start date string (YYYY-MM-DD).
        end_date: End date string (YYYY-MM-DD).
        logger: Optional logger instance.
    """
    if logger is None:
        logger = setup_logging()
    
    # 1. Data Pipeline
    df = run_data_pipeline(start_date, end_date, logger)
    
    # 2. Analysis Pipeline
    results = run_analysis_pipeline(df, logger)
    
    # 3. Visualization
    logger.info("Generating plots...")
    # Plot scatter
    plot_scatter(df['Vsw'], df['Ey'], results['optimal_lag'], "results/plot_scatter.png")
    # Plot timeseries
    plot_timeseries(
        df[['timestamp', 'Vsw', 'Bz']], 
        df[['timestamp', 'Ey']], 
        "results/plot_timeseries.png"
    )
    logger.info("Plots generated.")
    
    logger.info("Pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Solar Wind - Reconnection Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    logger = setup_logging()
    run_pipeline(args.start, args.end, logger)

if __name__ == "__main__":
    main()
