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

from code.config import LAG_WINDOW_MIN, LAG_WINDOW_MAX, LAG_STEP, TAIL_DISTANCE_RE, BOOTSTRAP_ITERATIONS
from code.data.ingest import fetch_omni_sw, fetch_themis_ey
from code.data.clean import clean_and_resample, handle_gaps
from code.data.lag import calculate_physics_lag, apply_lag_shift
from code.analysis.correlation import calculate_correlation, circular_block_permutation, moving_block_bootstrap
from code.analysis.lag_search import find_optimal_lag
from code.analysis.sensitivity import analyze_thresholds
from code.viz.plots import plot_scatter, plot_timeseries

def setup_logging(log_path: Path) -> logging.Logger:
    """Configure logging to file and console."""
    # Ensure the directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates in repeated runs
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # File handler
    try:
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
    except FileNotFoundError:
        # Fallback if directory creation failed for some reason
        print(f"Warning: Could not create log file at {log_path}")
        return logger
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def log_quality_warnings(warnings: list, output_path: Path) -> None:
    """
    Log data-quality warnings to a JSON file as required by FR-009.
    
    Args:
        warnings: List of warning dictionaries with keys 'timestamp', 'type', 'message'.
        output_path: Path to the output JSON file.
    """
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing log if it exists, otherwise start fresh
    existing_warnings = []
    if output_path.exists():
        try:
            with open(output_path, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_warnings = data
                elif isinstance(data, dict) and 'warnings' in data:
                    existing_warnings = data['warnings']
        except (json.JSONDecodeError, IOError):
            existing_warnings = []
    
    # Append new warnings
    all_warnings = existing_warnings + warnings
    
    # Write back to file
    with open(output_path, 'w') as f:
        json.dump(all_warnings, f, indent=2, default=str)

def generate_narrative_note() -> str:
    """
    Generate the narrative note for the JSON report as required by FR-013.
    
    Returns:
        The static narrative note string.
    """
    return "Bonferroni correction is conservative for autocorrelated lag searches and that the permutation test is the primary method for significance testing; future work should consider adaptive FDR control."

def run_data_pipeline(start_date: datetime, end_date: datetime, logger: logging.Logger) -> tuple:
    """
    Orchestrate data ingestion and cleaning.
    
    Args:
        start_date: Start of the date range.
        end_date: End of the date range.
        logger: Logger instance.
        
    Returns:
        Tuple of (df_sw, df_ey) cleaned DataFrames.
    """
    logger.info(f"Starting data ingestion for {start_date} to {end_date}")
    
    # Fetch data
    try:
        df_sw = fetch_omni_sw((start_date, end_date))
        df_ey = fetch_themis_ey((start_date, end_date))
    except Exception as e:
        logger.error(f"Data ingestion failed: {e}")
        raise
    
    logger.info(f"Fetched {len(df_sw)} solar wind records and {len(df_ey)} THEMIS records")
    
    # Clean and resample
    df_sw_clean, df_ey_clean = clean_and_resample(df_sw, df_ey)
    
    logger.info(f"Cleaned data: {len(df_sw_clean)} solar wind records, {len(df_ey_clean)} THEMIS records")
    
    # Handle gaps
    df_sw_clean = handle_gaps(df_sw_clean)
    df_ey_clean = handle_gaps(df_ey_clean)
    
    # Save cleaned data
    cleaned_data_path = project_root / 'data' / 'processed' / 'cleaned_data.csv'
    cleaned_data_path.parent.mkdir(parents=True, exist_ok=True)
    combined_df = pd.concat([df_sw_clean, df_ey_clean], axis=1, join='inner')
    combined_df.to_csv(cleaned_data_path)
    logger.info(f"Saved cleaned data to {cleaned_data_path}")
    
    return df_sw_clean, df_ey_clean

def run_analysis_pipeline(df_sw: pd.DataFrame, df_ey: pd.DataFrame, logger: logging.Logger) -> dict:
    """
    Orchestrate the core analysis pipeline.
    
    Args:
        df_sw: Cleaned solar wind DataFrame.
        df_ey: Cleaned THEMIS DataFrame.
        logger: Logger instance.
        
    Returns:
        Dictionary with analysis results.
    """
    logger.info("Starting analysis pipeline")
    
    # Calculate physics-based lag
    vsw_mean = df_sw['Vsw'].mean()
    l_phys = calculate_physics_lag(vsw_mean)
    logger.info(f"Calculated physics lag: {l_phys:.2f} minutes")
    
    # Apply lag shift
    df_sw_lagged = apply_lag_shift(df_sw['Vsw'], int(l_phys))
    
    # Find optimal lag
    optimal_lag_result = find_optimal_lag(
        df_sw_lagged, 
        df_ey['Ey'], 
        LAG_WINDOW_MIN, 
        LAG_WINDOW_MAX, 
        LAG_STEP
    )
    optimal_lag = optimal_lag_result['optimal_lag']
    logger.info(f"Optimal lag found: {optimal_lag} minutes")
    
    # Calculate correlations
    corr_result = calculate_correlation(df_sw_lagged, df_ey['Ey'])
    pearson = corr_result['pearson']
    spearman = corr_result['spearman']
    logger.info(f"Correlations - Pearson: {pearson:.4f}, Spearman: {spearman:.4f}")
    
    # Permutation test for significance
    p_val = circular_block_permutation(df_sw_lagged, df_ey['Ey'])
    logger.info(f"Permutation p-value: {p_val:.4f}")
    
    # Bootstrap confidence intervals
    ci_lower, ci_upper = moving_block_bootstrap(df_sw_lagged, df_ey['Ey'])
    logger.info(f"Bootstrap 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    # Sensitivity analysis
    sensitivity_result = analyze_thresholds(df_sw_lagged, df_ey['Ey'], [400, 500, 600])
    logger.info(f"Sensitivity analysis completed")
    
    # Calculate lag difference
    lag_difference = abs(optimal_lag - l_phys)
    
    # Compile results
    results = {
        'pearson': pearson,
        'spearman': spearman,
        'p_val_permutation': p_val,
        'optimal_lag': optimal_lag,
        'lag_difference': lag_difference,
        'ci_bootstrap': (ci_lower, ci_upper),
        'sensitivity_table': sensitivity_result,
        'notes': generate_narrative_note()
    }
    
    return results

def run_pipeline(start_date: datetime, end_date: datetime) -> None:
    """
    Run the full pipeline from data ingestion to results generation.
    
    Args:
        start_date: Start of the date range.
        end_date: End of the date range.
    """
    # Setup logging
    log_path = project_root / 'data' / 'processed' / 'pipeline.log'
    logger = setup_logging(log_path)
    
    # Quality warnings list
    quality_warnings = []
    
    try:
        # Run data pipeline
        df_sw, df_ey = run_data_pipeline(start_date, end_date, logger)
        
        # Check for data quality issues
        if df_sw['Vsw'].isna().sum() > 0:
            quality_warnings.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'missing_data',
                'message': f"Solar wind data has {df_sw['Vsw'].isna().sum()} NaN values"
            })
        
        if df_ey['Ey'].isna().sum() > 0:
            quality_warnings.append({
                'timestamp': datetime.now().isoformat(),
                'type': 'missing_data',
                'message': f"THEMIS data has {df_ey['Ey'].isna().sum()} NaN values"
            })
        
        # Run analysis pipeline
        results = run_analysis_pipeline(df_sw, df_ey, logger)
        
        # Log quality warnings
        quality_log_path = project_root / 'data' / 'processed' / 'quality_log.json'
        log_quality_warnings(quality_warnings, quality_log_path)
        logger.info(f"Logged {len(quality_warnings)} quality warnings to {quality_log_path}")
        
        # Save results
        results_path = project_root / 'results' / 'us1_correlation.json'
        results_path.parent.mkdir(parents=True, exist_ok=True)
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved results to {results_path}")
        
        # Generate plots
        plot_scatter(df_sw['Vsw'], df_ey['Ey'], results['optimal_lag'], 
                    str(project_root / 'results' / 'plot_scatter.png'))
        plot_timeseries(df_sw, df_ey, str(project_root / 'results' / 'plot_timeseries.png'))
        logger.info("Generated plots")
        
        logger.info("Pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        # Log error as quality warning
        quality_warnings.append({
            'timestamp': datetime.now().isoformat(),
            'type': 'error',
            'message': str(e)
        })
        quality_log_path = project_root / 'data' / 'processed' / 'quality_log.json'
        log_quality_warnings(quality_warnings, quality_log_path)
        raise

def main():
    """Main entry point for the pipeline."""
    parser = argparse.ArgumentParser(description='Solar wind and geomagnetic tail reconnection analysis')
    parser.add_argument('--start', type=str, required=True, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, required=True, help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    start_date = datetime.strptime(args.start, '%Y-%m-%d')
    end_date = datetime.strptime(args.end, '%Y-%m-%d')
    
    run_pipeline(start_date, end_date)

if __name__ == '__main__':
    main()