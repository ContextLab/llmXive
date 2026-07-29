"""
Main entry point for the Solar Wind - Geomagnetic Tail Reconnection Analysis Pipeline.
Orchestrates data ingestion, cleaning, lag analysis, correlation calculation, and reporting.
File path: projects/PROJ-300-exploring-the-relationship-between-solar/code/main.py
"""
import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for relative imports if running as script
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from code.config import (
    LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP,
    PERMUTATION_ITERATIONS, TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS
)
from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample, handle_gaps
from code.data.lag import calculate_l_phys, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from code.analysis.lag_search import find_optimal_lag
from code.analysis.sensitivity import analyze_thresholds
from code.viz.plots import plot_scatter, plot_timeseries

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(_project_root / 'data' / 'processed' / 'pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary output directories if they don't exist."""
    dirs = [
        _project_root / 'data' / 'raw',
        _project_root / 'data' / 'processed',
        _project_root / 'results',
        _project_root / 'figures'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directories exist: {dirs}")

def log_quality_warnings(warnings_list, output_path=None):
    """
    Log data-quality warnings to a JSON file.
    FR-009: Log data-quality warnings to data/processed/quality_log.json.
    """
    if output_path is None:
        output_path = _project_root / 'data' / 'processed' / 'quality_log.json'
    
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "warnings": warnings_list
    }
    
    # Load existing logs if present to append, otherwise start fresh
    existing_logs = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                content = f.read().strip()
                if content:
                    # Handle potential JSONL or single JSON list
                    try:
                        existing_logs = json.loads(content)
                        if not isinstance(existing_logs, list):
                            existing_logs = [existing_logs]
                    except json.JSONDecodeError:
                        existing_logs = []
        except Exception as e:
            logger.warning(f"Could not read existing quality log: {e}")

    existing_logs.append(log_entry)

    with open(output_path, 'w') as f:
        json.dump(existing_logs, f, indent=2)
    
    logger.info(f"Quality warnings logged to {output_path}")
    return output_path

def generate_narrative_note(method_used):
    """
    Generate the narrative note for the JSON report based on the method used.
    FR-013: Dynamically generate note stating Bonferroni is conservative and 
    permutation test is primary.
    """
    base_note = (
        "Bonferroni correction is conservative for autocorrelated lag searches "
        "and that the permutation test is the primary method for significance testing; "
        "future work should consider adaptive FDR control."
    )
    if method_used == "permutation":
        return f"Method: Permutation Test. {base_note}"
    elif method_used == "bootstrap":
        return f"Method: Bootstrap CI. {base_note}"
    else:
        return f"Method: {method_used}. {base_note}"

def run_data_pipeline(start_date, end_date):
    """
    Orchestrate data ingestion and cleaning.
    Saves cleaned data to data/processed/cleaned_data.csv.
    """
    logger.info(f"Starting data pipeline for {start_date} to {end_date}")
    warnings = []

    # Fetch data
    logger.info(f"Fetching solar wind data from {start_date} to {end_date}...")
    try:
        df_sw = fetch_omni_sw((start_date, end_date))
    except Exception as e:
        msg = f"Failed to fetch OMNI data: {e}"
        logger.error(msg)
        warnings.append({"type": "fetch_error", "source": "OMNI", "message": str(e)})
        raise RuntimeError(msg)

    logger.info(f"Fetching THEMIS data from {start_date} to {end_date}...")
    try:
        df_ey = fetch_themis_ey((start_date, end_date))
    except Exception as e:
        msg = f"Failed to fetch THEMIS data: {e}"
        logger.error(msg)
        warnings.append({"type": "fetch_error", "source": "THEMIS", "message": str(e)})
        raise RuntimeError(msg)

    # Clean and resample
    logger.info("Cleaning and resampling data...")
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)

    # Handle gaps
    logger.info("Handling data gaps...")
    try:
        df_sw_clean = handle_gaps(df_sw_clean)
    except Exception as e:
        warnings.append({"type": "gap_handling", "message": str(e)})
    
    try:
        df_ey_clean = handle_gaps(df_ey_clean)
    except Exception as e:
        warnings.append({"type": "gap_handling", "message": str(e)})

    # Save cleaned data
    output_csv = _project_root / 'data' / 'processed' / 'cleaned_data.csv'
    combined_df = pd.concat([df_sw_clean, df_ey_clean], axis=1, join='inner')
    combined_df.to_csv(output_csv)
    logger.info(f"Cleaned data saved to {output_csv}")

    # Log warnings
    if warnings:
        log_quality_warnings(warnings)

    return df_sw_clean, df_ey_clean

def run_analysis_pipeline(df_sw, df_ey):
    """
    Orchestrate the core analysis: lag calculation, shift, correlation, permutation, bootstrap, sensitivity.
    Returns a dictionary of results.
    """
    logger.info("Starting analysis pipeline...")
    
    # 1. Calculate Physics Lag
    vsw_mean = df_sw['Vsw'].mean()
    l_phys = calculate_l_phys(vsw_mean)
    logger.info(f"Calculated physics-based lag (L_phys): {l_phys:.2f} minutes")

    # 2. Find Optimal Lag (L*)
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
    logger.info(f"Optimal lag (L*) found: {optimal_lag} minutes with correlation {max_corr:.4f}")

    # 3. Apply Optimal Lag Shift
    df_sw_lagged = apply_lag_shift(df_sw['Vsw'], optimal_lag)

    # 4. Calculate Correlation
    corr_stats = calculate_correlation(df_sw_lagged, df_ey['Ey'])
    logger.info(f"Pearson: {corr_stats['pearson']:.4f}, Spearman: {corr_stats['spearman']:.4f}")

    # 5. Permutation Test for Significance
    logger.info(f"Running circular block permutation test ({PERMUTATION_ITERATIONS} iterations)...")
    p_val_perm = circular_block_permutation(df_sw_lagged, df_ey['Ey'], n_iterations=PERMUTATION_ITERATIONS)
    logger.info(f"Permutation p-value: {p_val_perm:.4f}")

    # 6. Bootstrap Confidence Interval
    logger.info(f"Running moving block bootstrap ({BOOTSTRAP_ITERATIONS} iterations)...")
    ci_lower, ci_upper = moving_block_bootstrap(df_sw_lagged, df_ey['Ey'], n_iterations=BOOTSTRAP_ITERATIONS)
    logger.info(f"95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    # 7. Sensitivity Analysis
    logger.info("Running sensitivity analysis on speed thresholds...")
    thresholds = [400, 500, 600]
    sensitivity_results = analyze_thresholds(df_sw['Vsw'], df_ey['Ey'], thresholds)

    # 8. Calculate Lag Difference (SC-002)
    # T017 Implementation: Calculate |L* - L_phys|
    if optimal_lag is None or optimal_lag != optimal_lag: # Check for None or NaN
        raise ValueError("Missing L* or L_phys for SC-002 calculation. Cannot compute difference.")
    if l_phys is None or l_phys != l_phys: # Check for None or NaN
        raise ValueError("Missing L* or L_phys for SC-002 calculation. Cannot compute difference.")
    
    lag_difference = abs(optimal_lag - l_phys)
    logger.info(f"SC-002 Lag Difference |L* - L_phys|: {lag_difference:.2f} minutes")

    # Compile results
    results = {
        "optimal_lag": float(optimal_lag),
        "lag_correlation_value": float(max_corr),
        "lag_difference": float(lag_difference),
        "l_phys": float(l_phys),
        "pearson": float(corr_stats['pearson']),
        "spearman": float(corr_stats['spearman']),
        "p_val_permutation": float(p_val_perm),
        "bootstrap_ci": {
            "lower": float(ci_lower),
            "upper": float(ci_upper)
        },
        "sensitivity_table": sensitivity_results,
        "n_samples": len(df_sw_lagged),
        "date_range": {
            "start": str(df_sw.index.min()),
            "end": str(df_sw.index.max())
        }
    }

    return results

def run_pipeline(start_date, end_date, output_json_path=None, output_scatter=None, output_timeseries=None):
    """
    Full end-to-end pipeline execution.
    """
    ensure_directories()
    
    # Data Pipeline
    df_sw, df_ey = run_data_pipeline(start_date, end_date)
    
    # Analysis Pipeline
    results = run_analysis_pipeline(df_sw, df_ey)
    
    # Generate Narrative Note
    results['narrative_note'] = generate_narrative_note("permutation")
    
    # Save Results JSON
    if output_json_path is None:
        output_json_path = _project_root / 'results' / 'us1_correlation.json'
    with open(output_json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_json_path}")
    
    # Generate Plots
    if output_scatter is None:
        output_scatter = _project_root / 'results' / 'plot_scatter.png'
    plot_scatter(df_sw['Vsw'], df_ey['Ey'], results['optimal_lag'], output_scatter)
    logger.info(f"Scatter plot saved to {output_scatter}")
    
    if output_timeseries is None:
        output_timeseries = _project_root / 'results' / 'plot_timeseries.png'
    plot_timeseries(df_sw, df_ey, output_timeseries)
    logger.info(f"Time series plot saved to {output_timeseries}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Solar Wind - Reconnection Analysis Pipeline")
    parser.add_argument("--start", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d")
    end = datetime.strptime(args.end, "%Y-%m-%d")

    try:
        results = run_pipeline(start, end)
        print(f"Pipeline completed successfully.")
        print(f"Optimal Lag: {results['optimal_lag']} min")
        print(f"Lag Difference (SC-002): {results['lag_difference']} min")
        print(f"P-value: {results['p_val_permutation']}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
