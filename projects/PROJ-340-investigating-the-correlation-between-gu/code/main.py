import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

from config import get_config
from ingest import load_schema, validate_variables, save_variable_metrics, load_data, detect_outliers_iqr, filter_outliers, calculate_checksum, register_checksum_in_state, main as ingest_main
from analysis import set_analysis_seed, run_correlation_analysis
from diagnostics import set_diagnostics_seed, run_collinearity_diagnostics, generate_diagnostics_report

def setup_paths():
    """Initialize project paths based on configuration."""
    config = get_config()
    base_path = Path(config.get('base_path', '.'))
    data_path = base_path / 'data'
    results_path = data_path / 'results'
    processed_path = data_path / 'processed'
    figures_path = base_path / 'figures'
    
    # Ensure directories exist
    results_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)
    figures_path.mkdir(parents=True, exist_ok=True)
    
    return {
        'base': base_path,
        'data': data_path,
        'results': results_path,
        'processed': processed_path,
        'figures': figures_path
    }

def run_ingestion_and_validation(paths):
    """Execute data ingestion, validation, and filtering steps."""
    print("Starting ingestion and validation...")
    
    # Load schema
    schema_path = paths['base'] / 'specs' / '001-gut-microbiome-sleep-architecture' / 'contracts' / 'dataset.schema.yaml'
    schema = load_schema(schema_path)
    
    # Validate variables
    validate_variables(schema, paths['data'])
    save_variable_metrics(paths['results'] / 'variable_load_metrics.json')
    
    # Load data (will exit if validation fails)
    raw_data = load_data(paths['data'], schema)
    
    # Detect outliers
    outliers = detect_outliers_iqr(raw_data)
    
    # Filter outliers
    filtered_data = filter_outliers(raw_data, outliers)
    
    # Calculate and register checksum
    checksum = calculate_checksum(filtered_data)
    register_checksum_in_state(checksum, paths['results'] / 'state.yaml')
    
    # Save filtered data
    filtered_path = paths['processed'] / 'filtered_data.parquet'
    filtered_data.to_parquet(filtered_path)
    print(f"Filtered data saved to {filtered_path}")
    
    return filtered_data

def run_analysis(paths, data):
    """Execute correlation analysis."""
    print("Starting correlation analysis...")
    
    # Set seeds for reproducibility
    set_analysis_seed()
    
    # Run analysis
    results = run_correlation_analysis(data)
    
    # Save results
    results_path = paths['results'] / 'correlation_results.json'
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Correlation results saved to {results_path}")
    
    return results

def run_diagnostics(paths, results):
    """Execute diagnostics and generate report."""
    print("Starting diagnostics...")
    
    # Set seeds for reproducibility
    set_diagnostics_seed()
    
    # Run diagnostics
    diagnostics = run_collinearity_diagnostics(paths['processed'] / 'filtered_data.parquet')
    
    # Generate report
    report = generate_diagnostics_report(diagnostics, results)
    
    # Save report
    report_path = paths['results'] / 'diagnostics_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Diagnostics report saved to {report_path}")
    
    return report

def main():
    """Main pipeline orchestration with timing evidence generation."""
    start_time = time.time()
    start_datetime = datetime.now().isoformat()
    
    print(f"Pipeline started at {start_datetime}")
    
    # Setup paths
    paths = setup_paths()
    
    try:
        # Run ingestion and validation
        data = run_ingestion_and_validation(paths)
        
        # Run analysis
        results = run_analysis(paths, data)
        
        # Run diagnostics
        diagnostics = run_diagnostics(paths, results)
        
    except Exception as e:
        end_time = time.time()
        end_datetime = datetime.now().isoformat()
        duration_seconds = end_time - start_time
        duration_hours = duration_seconds / 3600
        
        timing_evidence = {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'duration_seconds': duration_seconds,
            'duration_hours': duration_hours,
            'status': 'failed',
            'error': str(e)
        }
        
        # Save timing evidence even on failure
        timing_path = paths['results'] / 'timing_evidence.json'
        with open(timing_path, 'w') as f:
            json.dump(timing_evidence, f, indent=2)
        
        print(f"Pipeline failed after {duration_hours:.2f} hours. Timing evidence saved.")
        sys.exit(1)
    
    end_time = time.time()
    end_datetime = datetime.now().isoformat()
    duration_seconds = end_time - start_time
    duration_hours = duration_seconds / 3600
    
    # Check timing constraint (SC-004)
    max_hours = 6.0
    if duration_hours > max_hours:
        error_msg = f"Pipeline exceeded maximum allowed runtime of {max_hours} hours. Actual: {duration_hours:.2f} hours."
        print(f"ERROR: {error_msg}")
        
        timing_evidence = {
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'duration_seconds': duration_seconds,
            'duration_hours': duration_hours,
            'status': 'timeout',
            'error': error_msg
        }
        
        timing_path = paths['results'] / 'timing_evidence.json'
        with open(timing_path, 'w') as f:
            json.dump(timing_evidence, f, indent=2)
        
        sys.exit(1)
    
    # Generate timing evidence artifact
    timing_evidence = {
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'duration_seconds': duration_seconds,
        'duration_hours': duration_hours,
        'status': 'success',
        'max_allowed_hours': max_hours,
        'within_budget': True
    }
    
    timing_path = paths['results'] / 'timing_evidence.json'
    with open(timing_path, 'w') as f:
        json.dump(timing_evidence, f, indent=2)
    
    print(f"Pipeline completed successfully in {duration_hours:.2f} hours.")
    print(f"Timing evidence saved to {timing_path}")
    
    return timing_evidence

if __name__ == "__main__":
    main()