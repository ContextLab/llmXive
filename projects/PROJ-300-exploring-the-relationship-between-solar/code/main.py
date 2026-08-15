import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Import from local modules using relative imports compatible with package execution
# When run as `python code/main.py`, these imports work because code/ is in sys.path
from data.ingest import fetch_omni_sw, fetch_themis_ey
from data.clean import clean_and_resample, handle_gaps
from data.lag import calculate_physics_lag, log_lag_derivation, apply_lag_shift
from analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from analysis.lag_search import find_optimal_lag
from analysis.sensitivity import analyze_thresholds
from viz.plots import plot_scatter, plot_timeseries
from config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS

def setup_logging(log_file: str = "data/processed/pipeline.log") -> logging.Logger:
    """Configure logging for the pipeline."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logger = logging.getLogger("solar_wind_pipeline")
    logger.setLevel(logging.INFO)
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def log_data_quality_warnings(warnings: list, log_file: str = "data/processed/quality_log.json") -> None:
    """
    Log data-quality warnings to a JSON file.
    
    Args:
        warnings: List of warning dictionaries with keys: timestamp, level, source, message
        log_file: Path to the quality log JSON file
    """
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Load existing warnings if file exists
    existing_warnings = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_warnings = json.loads(content)
                else:
                    existing_warnings = []
        except (json.JSONDecodeError, IOError):
            existing_warnings = []
    
    # Append new warnings
    all_warnings = existing_warnings + warnings
    
    # Write with file locking simulation (append mode with careful handling)
    with open(log_file, 'w') as f:
        json.dump(all_warnings, f, indent=2)

def run_data_pipeline(start_date: str, end_date: str, logger: logging.Logger) -> tuple:
    """
    Orchestrate data ingestion and cleaning.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        logger: Logger instance
        
    Returns:
        Tuple of (df_sw, df_ey) cleaned DataFrames
    """
    logger.info(f"Starting data pipeline for {start_date} to {end_date}")
    
    # Fetch data
    logger.info("Fetching OMNI solar wind data...")
    df_sw = fetch_omni_sw((start_date, end_date))
    
    logger.info("Fetching THEMIS Ey data...")
    df_ey = fetch_themis_ey((start_date, end_date))
    
    # Clean and resample
    logger.info("Cleaning and resampling data...")
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    
    # Save cleaned data
    os.makedirs("data/processed", exist_ok=True)
    cleaned_path = "data/processed/cleaned_data.csv"
    # Combine for saving
    combined = pd.merge(df_sw_clean, df_ey_clean, on='timestamp', how='inner')
    combined.to_csv(cleaned_path, index=False)
    logger.info(f"Saved cleaned data to {cleaned_path}")
    
    return df_sw_clean, df_ey_clean

def run_analysis_pipeline(df_sw: pd.DataFrame, df_ey: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    Orchestrate the core analysis pipeline.
    
    Args:
        df_sw: Cleaned solar wind DataFrame
        df_ey: Cleaned THEMIS Ey DataFrame
        logger: Logger instance
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info("Starting analysis pipeline")
    
    # Calculate physics-based lag
    vsw_mean = df_sw['Vsw'].mean()
    l_phys = calculate_physics_lag(vsw_mean)
    logger.info(f"Physics-based lag: {l_phys:.2f} minutes")
    
    # Log lag derivation
    log_lag_derivation(vsw_mean, l_phys)
    
    # Apply lag shift to solar wind data
    # Convert lag to number of periods (assuming 5-minute cadence)
    cadence_minutes = 5
    lag_periods = int(round(l_phys / cadence_minutes))
    df_sw_lagged = df_sw.copy()
    df_sw_lagged['Vsw'] = apply_lag_shift(df_sw['Vsw'], l_phys)
    
    # Find optimal lag
    logger.info("Searching for optimal lag...")
    lag_results = find_optimal_lag(
        df_sw_lagged['Vsw'], 
        df_ey['Ey'], 
        LAG_WINDOW_MIN, 
        LAG_WINDOW_MAX, 
        LAG_STEP
    )
    optimal_lag = lag_results['optimal_lag']
    max_corr = lag_results['max_correlation']
    lag_difference = abs(optimal_lag - l_phys)
    logger.info(f"Optimal lag: {optimal_lag} minutes, Max correlation: {max_corr:.4f}")
    
    # Calculate correlations at optimal lag
    df_sw_opt = df_sw_lagged.copy()
    df_sw_opt['Vsw'] = apply_lag_shift(df_sw['Vsw'], optimal_lag)
    
    corr_stats = calculate_correlation(df_sw_opt['Vsw'], df_ey['Ey'])
    pearson = corr_stats['pearson']
    spearman = corr_stats['spearman']
    
    # Permutation test for p-value
    logger.info("Running permutation test...")
    p_val_permutation = circular_block_permutation(df_sw_opt['Vsw'], df_ey['Ey'])
    logger.info(f"Permutation p-value: {p_val_permutation:.4f}")
    
    # Bootstrap confidence intervals
    logger.info("Running bootstrap for confidence intervals...")
    ci_lower, ci_upper = moving_block_bootstrap(df_sw_opt['Vsw'], df_ey['Ey'])
    logger.info(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    # Sensitivity analysis
    logger.info("Running sensitivity analysis...")
    thresholds = [400, 500, 600]
    sensitivity_results = analyze_thresholds(df_sw_opt['Vsw'], df_ey['Ey'], thresholds)
    
    # Prepare notes with reference frame context
    notes = [
        "Analysis performed on cleaned 5-minute cadence data.",
        f"Physics-based lag (L_phys) calculated as {l_phys:.2f} minutes using vsw_mean={vsw_mean:.2f} km/s.",
        f"Optimal lag (L*) found at {optimal_lag} minutes, difference |L* - L_phys| = {lag_difference:.2f} minutes.",
        "Permutation test used circular block permutation with 10000 iterations.",
        "Bootstrap confidence intervals computed using moving block bootstrap with 1000 iterations."
    ]
    
    # Reference Frame Context (Required by T063)
    # Ey (convection electric field) is measured in the GSM (Geocentric Solar Magnetospheric) frame by THEMIS.
    # Vsw (solar wind speed) is measured in the solar wind rest frame (effectively Earth frame for OMNI).
    # No explicit Lorentz transformation was applied; the correlation assumes the convection electric field
    # (Ey = -Vsw x Bz) naturally couples the solar wind flow to the magnetospheric response.
    reference_frame_context = (
        "Reference Frame Context: "
        "Ey (convection electric field) was measured by THEMIS in the GSM (Geocentric Solar Magnetospheric) frame. "
        "Vsw (solar wind speed) was measured by OMNI in the Earth/solar wind rest frame. "
        "The analysis assumes the standard convection relation Ey ≈ -Vsw × Bz holds, "
        "implicitly linking the solar wind frame measurement to the magnetospheric response in GSM. "
        "No explicit Lorentz transformation was applied; the correlation captures the coupled dynamics "
        "as observed from Earth, consistent with the reference frame of the reconnection proxy (Ey)."
    )
    
    results = {
        'pearson': float(pearson),
        'spearman': float(spearman),
        'p_val_permutation': float(p_val_permutation),
        'optimal_lag': int(optimal_lag),
        'lag_difference': float(lag_difference),
        'ci_bootstrap': {'lower': float(ci_lower), 'upper': float(ci_upper)},
        'sensitivity_table': sensitivity_results,
        'notes': notes,
        'reference_frame_context': reference_frame_context
    }
    
    # Save results
    os.makedirs("results", exist_ok=True)
    results_path = "results/us1_correlation.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved results to {results_path}")
    
    return results

def run_pipeline(start_date: str, end_date: str) -> dict:
    """
    Run the full pipeline from data ingestion to analysis.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Analysis results dictionary
    """
    logger = setup_logging()
    
    # Run data pipeline
    df_sw, df_ey = run_data_pipeline(start_date, end_date, logger)
    
    # Run analysis
    results = run_analysis_pipeline(df_sw, df_ey, logger)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Solar Wind - Reconnection Correlation Pipeline")
    parser.add_argument('--start', required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', required=True, help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    try:
        results = run_pipeline(args.start, args.end)
        print(f"Pipeline completed successfully.")
        print(f"Optimal Lag: {results['optimal_lag']} min")
        print(f"Pearson Correlation: {results['pearson']:.4f}")
        print(f"P-value: {results['p_val_permutation']:.4f}")
    except Exception as e:
        logging.error(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()