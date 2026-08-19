import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta

# Ensure project root is in path for relative imports if run as script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample, handle_gaps
from data.lag import calculate_l_phys, apply_lag_shift, log_lag_derivation
from analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from analysis.lag_search import find_optimal_lag
from analysis.sensitivity import analyze_thresholds
from viz.plots import plot_scatter, plot_timeseries
from config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS
import pandas as pd
import portalocker

# Configure logging
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join(project_root, 'data', 'processed', 'pipeline.log'))
        ]
    )

def log_data_quality_warnings(warnings: list) -> None:
    """
    Logs data-quality warnings to data/processed/quality_log.json.
    Uses portalocker to prevent race conditions with T006c.
    """
    log_path = os.path.join(project_root, 'data', 'processed', 'quality_log.json')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Load existing entries or create new list
    try:
        with open(log_path, 'r') as f:
            try:
                entries = json.load(f)
                if not isinstance(entries, list):
                    entries = []
            except json.JSONDecodeError:
                entries = []
    except FileNotFoundError:
        entries = []

    # Prepare new entries
    now_iso = datetime.utcnow().isoformat() + "Z"
    for w in warnings:
        entry = {
            "timestamp": now_iso,
            "level": "WARN",
            "source": w.get("source", "pipeline"),
            "message": w.get("message", "Unknown warning")
        }
        entries.append(entry)

    # Write with locking
    with open(log_path, 'w') as f:
        portalocker.lock(f, portalocker.LOCK_EX)
        try:
            json.dump(entries, f, indent=2)
        finally:
            portalocker.unlock(f)

    logging.info(f"Logged {len([e for e in entries if e.get('level') == 'WARN'])} warnings to {log_path}")

def run_data_pipeline(start_date: str, end_date: str) -> str:
    """
    Orchestrates data ingestion and cleaning.
    Saves cleaned data to data/processed/cleaned_data.csv.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting data pipeline for {start_date} to {end_date}")

    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)

    # Fetch data
    logger.info("Fetching OMNI SW data...")
    df_sw = fetch_omni_sw((start, end))
    
    logger.info("Fetching THEMIS EY data...")
    df_ey = fetch_themis_ey((start, end))

    if df_sw.empty or df_ey.empty:
        raise ValueError("One or both data sources returned empty DataFrames.")

    # Clean and resample
    logger.info("Cleaning and resampling data...")
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)

    # Handle gaps
    warnings = []
    if not df_sw_clean.empty:
        df_sw_clean = handle_gaps(df_sw_clean)
    if not df_ey_clean.empty:
        df_ey_clean = handle_gaps(df_ey_clean)

    # Log any warnings from gap handling if necessary (simplified here)
    if len(df_sw_clean) == 0 or len(df_ey_clean) == 0:
        warnings.append({"source": "clean", "message": "Data empty after gap handling"})
    
    if warnings:
        log_data_quality_warnings(warnings)

    # Save cleaned data
    output_path = os.path.join(project_root, 'data', 'processed', 'cleaned_data.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    combined_df = pd.concat([
        df_sw_clean.rename(columns={'Vsw': 'Vsw_raw'}),
        df_ey_clean.rename(columns={'Ey': 'Ey_raw'}),
    ], axis=1)
    
    # Align indices explicitly
    combined_df = combined_df.loc[combined_df.index.dropna()]
    combined_df.to_csv(output_path)
    logger.info(f"Cleaned data saved to {output_path}")

    return output_path

def run_analysis_pipeline(cleaned_data_path: str = None, start_date: str = None, end_date: str = None) -> dict:
    """
    Orchestrates the core analysis pipeline.
    Loads cleaned data, calculates lag, performs correlation analysis,
    sensitivity analysis, and generates plots.
    """
    logger = logging.getLogger(__name__)
    
    # If no path provided, run the ingestion pipeline first
    if cleaned_data_path is None:
        if not start_date or not end_date:
            raise ValueError("Either cleaned_data_path or start/end dates must be provided.")
        cleaned_data_path = run_data_pipeline(start_date, end_date)

    logger.info(f"Loading cleaned data from {cleaned_data_path}")
    df = pd.read_csv(cleaned_data_path, index_col=0, parse_dates=True)

    if df.empty:
        raise ValueError("Cleaned data is empty. Cannot proceed with analysis.")

    # Extract series
    # Assuming columns are aligned as Vsw_raw and Ey_raw after concat in run_data_pipeline
    # If they are just Vsw and Ey, adjust accordingly. Based on T020a logic:
    # df_sw_clean has 'Vsw', df_ey_clean has 'Ey'.
    # Let's re-read carefully: run_data_pipeline does concat with rename.
    # So columns should be 'Vsw_raw' and 'Ey_raw'.
    
    if 'Vsw_raw' not in df.columns or 'Ey_raw' not in df.columns:
        # Fallback if column names are different
        if 'Vsw' in df.columns and 'Ey' in df.columns:
            vsw_series = df['Vsw']
            ey_series = df['Ey']
        else:
            raise KeyError(f"Expected 'Vsw_raw'/'Ey_raw' or 'Vsw'/'Ey' columns. Found: {df.columns.tolist()}")
    else:
        vsw_series = df['Vsw_raw']
        ey_series = df['Ey_raw']

    # Drop NaNs just in case
    valid_mask = vsw_series.notna() & ey_series.notna()
    vsw_series = vsw_series[valid_mask]
    ey_series = ey_series[valid_mask]

    if len(vsw_series) == 0:
        raise ValueError("No valid data points after filtering NaNs.")

    # 1. Calculate Physics-based Lag
    vsw_mean = vsw_series.mean()
    l_phys = calculate_l_phys(vsw_mean)
    logger.info(f"Calculated physics-based lag (L_phys): {l_phys:.2f} minutes (Vsw mean: {vsw_mean:.2f} km/s)")

    # 2. Log Lag Derivation
    log_lag_derivation(vsw_mean, l_phys)

    # 3. Find Optimal Lag
    logger.info("Searching for optimal lag...")
    lag_results = find_optimal_lag(
        vsw_series, 
        ey_series, 
        min_lag=LAG_WINDOW_MIN, 
        max_lag=LAG_WINDOW_MAX, 
        step=LAG_STEP
    )
    optimal_lag = lag_results['optimal_lag']
    max_corr = lag_results['max_correlation']
    lag_diff = abs(optimal_lag - l_phys)
    logger.info(f"Optimal lag found: {optimal_lag} min (Max Correlation: {max_corr:.4f}, |L* - L_phys|: {lag_diff:.2f})")

    # 4. Apply Lag Shift for Final Correlation
    vsw_lagged = apply_lag_shift(vsw_series, optimal_lag)
    
    # Re-align for correlation
    valid_lag_mask = vsw_lagged.notna() & ey_series.notna()
    vsw_final = vsw_lagged[valid_lag_mask]
    ey_final = ey_series[valid_lag_mask]

    if len(vsw_final) == 0:
        raise ValueError("No valid data points after applying lag shift.")

    # 5. Calculate Correlation
    logger.info("Calculating correlations...")
    corr_stats = calculate_correlation(vsw_final, ey_final)
    pearson = corr_stats['pearson']
    spearman = corr_stats['spearman']

    # 6. Permutation Test for P-value
    logger.info("Running permutation test...")
    p_val = circular_block_permutation(vsw_final, ey_final)
    logger.info(f"Permutation p-value: {p_val:.4f}")

    # 7. Bootstrap Confidence Interval
    logger.info("Running bootstrap for CI...")
    ci_lower, ci_upper = moving_block_bootstrap(vsw_final, ey_final)
    logger.info(f"Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    # 8. Sensitivity Analysis
    logger.info("Running sensitivity analysis...")
    thresholds = [400, 500, 600]
    sensitivity_table = analyze_thresholds(vsw_series, ey_series, thresholds)

    # 9. Generate Plots
    results_dir = os.path.join(project_root, 'results')
    os.makedirs(results_dir, exist_ok=True)
    
    scatter_path = os.path.join(results_dir, 'plot_scatter.png')
    timeseries_path = os.path.join(results_dir, 'plot_timeseries.png')
    
    logger.info("Generating plots...")
    plot_scatter(vsw_final, ey_final, optimal_lag, scatter_path)
    plot_timeseries(
        pd.DataFrame({'Vsw': vsw_series}, index=vsw_series.index),
        pd.DataFrame({'Ey': ey_series}, index=ey_series.index),
        timeseries_path
    )

    # 10. Compile Results
    results = {
        "pearson": pearson,
        "spearman": spearman,
        "p_val_permutation": p_val,
        "optimal_lag": optimal_lag,
        "lag_difference": lag_diff,
        "ci_bootstrap": {"lower": ci_lower, "upper": ci_upper},
        "sensitivity_table": sensitivity_table,
        "notes": [
            f"Analysis performed on data from {start_date} to {end_date}.",
            f"Physics-based lag (L_phys) calculated as {l_phys:.2f} min based on Vsw mean {vsw_mean:.2f} km/s.",
            f"Optimal lag L* = {optimal_lag} min differs from L_phys by {lag_diff:.2f} min.",
            f"Reference Frame: GSM for Ey, Solar Wind Rest Frame for Vsw (aligned via propagation model)."
        ]
    }

    # Save results JSON
    results_json_path = os.path.join(results_dir, 'us1_correlation.json')
    with open(results_json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {results_json_path}")
    
    return results

def run_pipeline(start_date: str, end_date: str) -> dict:
    """
    Full pipeline orchestration: Ingest -> Clean -> Analyze -> Plot.
    """
    cleaned_path = run_data_pipeline(start_date, end_date)
    return run_analysis_pipeline(cleaned_data_path=cleaned_path, start_date=start_date, end_date=end_date)

def main():
    parser = argparse.ArgumentParser(description="Solar Wind - Reconnection Analysis Pipeline")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger(__name__)

    try:
        results = run_pipeline(args.start, args.end)
        logger.info("Pipeline executed successfully.")
        print(json.dumps(results, indent=2))
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()