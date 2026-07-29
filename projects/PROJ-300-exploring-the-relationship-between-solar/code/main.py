"""
Main entry point for the Solar Wind - Reconnection Rate analysis pipeline.
Orchestrates data ingestion, cleaning, lag analysis, correlation, and visualization.
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
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample, handle_gaps
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from code.analysis.lag_search import find_optimal_lag
from code.analysis.sensitivity import analyze_thresholds
from code.viz.plots import plot_scatter, plot_timeseries
from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / 'data' / 'processed' / 'pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    dirs = [
        PROJECT_ROOT / 'data' / 'raw',
        PROJECT_ROOT / 'data' / 'processed',
        PROJECT_ROOT / 'results'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {[str(d) for d in dirs]}")

def log_quality_warnings(warnings_list, output_path):
    """Log data-quality warnings to a JSON file."""
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "warnings": warnings_list
    }
    
    # Load existing log if present, otherwise start fresh
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_log = json.load(f)
            if isinstance(existing_log, list):
                existing_log.append(log_entry)
            else:
                existing_log = [existing_log, log_entry]
        except (json.JSONDecodeError, IOError):
            existing_log = [log_entry]
    else:
        existing_log = [log_entry]

    with open(output_path, 'w') as f:
        json.dump(existing_log, f, indent=2)
    logger.info(f"Quality warnings logged to {output_path}")

def generate_narrative_note():
    """Generate the static narrative note for the JSON report as per FR-013."""
    return "Bonferroni correction is conservative for autocorrelated lag searches and that the permutation test is the primary method for significance testing; future work should consider adaptive FDR control."

def run_data_pipeline(start_date: str, end_date: str):
    """
    Orchestrate data ingestion and cleaning.
    Returns cleaned solar wind and THEMIS DataFrames.
    """
    logger.info(f"Starting data pipeline for range: {start_date} to {end_date}")
    
    # Parse dates
    start = datetime.fromisoformat(start_date)
    end = datetime.fromisoformat(end_date)
    
    # Fetch data
    logger.info("Fetching solar wind data from OMNIWeb...")
    df_sw = fetch_omni_sw((start, end))
    if df_sw is None or df_sw.empty:
        raise ValueError("Failed to fetch solar wind data. Check network access to OMNIWeb API.")
    
    logger.info("Fetching THEMIS Ey data from CDAWeb...")
    df_ey = fetch_themis_ey((start, end))
    if df_ey is None or df_ey.empty:
        raise ValueError("Failed to fetch THEMIS Ey data. Check network access to CDAWeb.")
    
    # Clean and resample
    logger.info("Cleaning and resampling data...")
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    
    # Handle gaps
    warnings = []
    try:
        df_sw_clean = handle_gaps(df_sw_clean)
    except Exception as e:
        warnings.append(f"Warning in handling solar wind gaps: {str(e)}")
    
    try:
        df_ey_clean = handle_gaps(df_ey_clean)
    except Exception as e:
        warnings.append(f"Warning in handling THEMIS gaps: {str(e)}")
    
    # Save cleaned data
    output_path = PROJECT_ROOT / 'data' / 'processed' / 'cleaned_data.csv'
    combined_df = pd.merge(df_sw_clean, df_ey_clean, left_index=True, right_index=True, how='inner')
    combined_df.to_csv(output_path)
    logger.info(f"Cleaned data saved to {output_path}")
    
    # Log quality warnings
    quality_log_path = PROJECT_ROOT / 'data' / 'processed' / 'quality_log.json'
    log_quality_warnings(warnings, quality_log_path)
    
    return df_sw_clean, df_ey_clean

def run_analysis_pipeline(df_sw: pd.DataFrame, df_ey: pd.DataFrame):
    """
    Orchestrate the core analysis: lag, correlation, significance, sensitivity.
    Returns a dictionary of results.
    """
    logger.info("Starting analysis pipeline...")
    
    # Calculate physics-based lag
    vsw_mean = df_sw['Vsw'].mean()
    l_phys = calculate_physics_lag(vsw_mean)
    logger.info(f"Physics-based lag (L_phys): {l_phys:.2f} minutes")
    
    # Find optimal lag
    logger.info("Searching for optimal lag...")
    lag_results = find_optimal_lag(
        df_sw['Vsw'], 
        df_ey['Ey'], 
        min_lag=LAG_WINDOW_MIN, 
        max_lag=LAG_WINDOW_MAX, 
        step=LAG_STEP
    )
    optimal_lag = lag_results['optimal_lag']
    max_corr = lag_results['max_correlation']
    lag_difference = abs(optimal_lag - l_phys)
    logger.info(f"Optimal lag (L*): {optimal_lag} min, Max correlation: {max_corr:.4f}, |L* - L_phys|: {lag_difference:.2f} min")
    
    # Apply optimal lag shift
    df_sw_lagged = apply_lag_shift(df_sw['Vsw'], optimal_lag)
    
    # Calculate correlation
    corr_stats = calculate_correlation(df_sw_lagged, df_ey['Ey'])
    pearson = corr_stats['pearson']
    spearman = corr_stats['spearman']
    logger.info(f"Pearson: {pearson:.4f}, Spearman: {spearman:.4f}")
    
    # Permutation test for p-value
    logger.info("Running circular block permutation test...")
    p_val_perm = circular_block_permutation(df_sw_lagged, df_ey['Ey'])
    logger.info(f"Permutation p-value: {p_val_perm:.4f}")
    
    # Bootstrap for confidence interval
    logger.info("Running moving block bootstrap...")
    ci_lower, ci_upper = moving_block_bootstrap(df_sw_lagged, df_ey['Ey'])
    logger.info(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    # Sensitivity analysis
    logger.info("Running sensitivity analysis...")
    sensitivity_results = analyze_thresholds(df_sw['Vsw'], df_ey['Ey'], thresholds=[400, 500, 600])
    
    # Compile results
    results = {
        "pearson": float(pearson),
        "spearman": float(spearman),
        "p_val_permutation": float(p_val_perm),
        "optimal_lag": int(optimal_lag),
        "lag_difference": float(lag_difference),
        "ci_bootstrap": {"lower": float(ci_lower), "upper": float(ci_upper)},
        "sensitivity_table": sensitivity_results,
        "notes": generate_narrative_note(),
        "metadata": {
            "vsw_mean": float(vsw_mean),
            "l_phys": float(l_phys),
            "n_samples": len(df_sw_lagged)
        }
    }
    
    return results

def run_pipeline(start_date: str, end_date: str):
    """
    Full pipeline execution: ingest -> clean -> analyze -> visualize -> save.
    """
    ensure_directories()
    
    # Run data pipeline
    df_sw, df_ey = run_data_pipeline(start_date, end_date)
    
    # Run analysis
    results = run_analysis_pipeline(df_sw, df_ey)
    
    # Save results JSON
    results_json_path = PROJECT_ROOT / 'results' / 'us1_correlation.json'
    with open(results_json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {results_json_path}")
    
    # Generate plots
    logger.info("Generating scatter plot...")
    plot_scatter(
        df_sw['Vsw'], 
        df_ey['Ey'], 
        optimal_lag=results['optimal_lag'],
        output_path=str(PROJECT_ROOT / 'results' / 'plot_scatter.png')
    )
    
    logger.info("Generating time-series plot...")
    plot_timeseries(
        df_sw, 
        df_ey, 
        output_path=str(PROJECT_ROOT / 'results' / 'plot_timeseries.png')
    )
    
    logger.info("Pipeline completed successfully.")
    return results

def main():
    parser = argparse.ArgumentParser(description="Solar Wind - Reconnection Rate Analysis Pipeline")
    parser.add_argument('--start', type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument('--end', type=str, required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    try:
        run_pipeline(args.start, args.end)
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
