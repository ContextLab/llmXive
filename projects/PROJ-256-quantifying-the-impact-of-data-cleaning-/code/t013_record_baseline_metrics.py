"""
Task T013: Record baseline metrics (p-value, 95% CI, Cohen's d/R²) to data/processed/baseline_metrics.json.

This script aggregates results from baseline analyses run on raw datasets and
writes a consolidated JSON report with ≥3 decimal precision.
"""
import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Import from local modules
from utils import setup_logging, compute_file_checksum, pin_random_seed
from config import get_config
from analysis import run_baseline_analysis, load_datasets_from_raw

def format_metric_value(value: float, precision: int = 3) -> float:
    """Format a numeric metric to specified decimal precision."""
    if value is None or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float):
        return round(value, precision)
    if isinstance(value, list):
        return [format_metric_value(v, precision) for v in value]
    if isinstance(value, dict):
        return {k: format_metric_value(v, precision) for k, v in value.items()}
    return value

def log_metrics_summary(metrics: List[Dict[str, Any]], logger: logging.Logger):
    """Log a summary of the collected metrics."""
    logger.info("=== Baseline Metrics Summary ===")
    for entry in metrics:
        ds_name = entry.get('dataset_name', 'Unknown')
        t_test_p = entry.get('t_test', {}).get('p_value', 'N/A')
        reg_r2 = entry.get('regression', {}).get('r_squared', 'N/A')
        logger.info(f"Dataset: {ds_name} | p-value: {t_test_p} | R²: {reg_r2}")

def process_dataset_for_baseline(dataset_path: str, dataset_name: str, config: Dict[str, Any], logger: logging.Logger) -> Optional[Dict[str, Any]]:
    """
    Run baseline analysis on a single dataset and format the result.
    
    Args:
        dataset_path: Path to the CSV file
        dataset_name: Name identifier for the dataset
        config: Configuration dictionary
        logger: Logger instance
        
    Returns:
        Dictionary containing formatted metrics or None if processing fails
    """
    try:
        # Load the dataset
        df = load_datasets_from_raw(dataset_path, dataset_name)
        if df is None or df.empty:
            logger.warning(f"Dataset {dataset_name} is empty or failed to load. Skipping.")
            return None

        # Pin random seed for reproducibility
        seed = config.get('RANDOM_SEED', 42)
        pin_random_seed(seed)

        # Run baseline analysis
        # run_baseline_analysis accepts (df, dataset_name=..., config=...)
        result = run_baseline_analysis(df, dataset_name=dataset_name, config=config)
        
        if not result or not result.get('success'):
            logger.error(f"Baseline analysis failed for {dataset_name}")
            return None

        analysis_data = result.get('analysis', {})
        
        # Extract and format metrics
        formatted_entry = {
            'dataset_name': dataset_name,
            'dataset_path': dataset_path,
            'checksum': compute_file_checksum(dataset_path),
            'timestamp': datetime.now().isoformat(),
            'dataset_size': len(df),
            't_test': {
                'p_value': format_metric_value(analysis_data.get('t_test', {}).get('p_value')),
                'ci_lower': format_metric_value(analysis_data.get('t_test', {}).get('ci', [None, None])[0] if analysis_data.get('t_test', {}).get('ci') else None),
                'ci_upper': format_metric_value(analysis_data.get('t_test', {}).get('ci', [None, None])[1] if analysis_data.get('t_test', {}).get('ci') else None),
                'effect_size_cohen_d': format_metric_value(analysis_data.get('t_test', {}).get('effect_size_cohen_d'))
            },
            'regression': {
                'r_squared': format_metric_value(analysis_data.get('regression', {}).get('r_squared')),
                'adj_r_squared': format_metric_value(analysis_data.get('regression', {}).get('adj_r_squared')),
                'f_statistic': format_metric_value(analysis_data.get('regression', {}).get('f_statistic')),
                'p_value_f': format_metric_value(analysis_data.get('regression', {}).get('p_value_f'))
            }
        }
        
        logger.info(f"Successfully processed {dataset_name}: p={formatted_entry['t_test']['p_value']}, R²={formatted_entry['regression']['r_squared']}")
        return formatted_entry

    except Exception as e:
        logger.error(f"Error processing dataset {dataset_name}: {e}", exc_info=True)
        return None

def main():
    """Main entry point for T013."""
    logger = setup_logging()
    logger.info("Starting Task T013: Record Baseline Metrics")
    
    config = get_config()
    raw_data_path = config.get('RAW_DATA_PATH', 'data/raw')
    output_path = config.get('PROCESSED_DATA_PATH', 'data/processed')
    output_file = os.path.join(output_path, 'baseline_metrics.json')
    
    # Ensure output directory exists
    os.makedirs(output_path, exist_ok=True)
    
    # Find all CSV files in raw data directory
    if not os.path.exists(raw_data_path):
        logger.error(f"Raw data path does not exist: {raw_data_path}")
        sys.exit(1)
        
    csv_files = [f for f in os.listdir(raw_data_path) if f.endswith('.csv')]
    if not csv_files:
        logger.warning(f"No CSV files found in {raw_data_path}. Creating empty report.")
        empty_report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'tool': 'llmXive T013',
                'datasets_processed': 0,
                'datasets_failed': 0
            },
            'datasets': []
        }
        with open(output_file, 'w') as f:
            json.dump(empty_report, f, indent=2)
        logger.info(f"Empty baseline report written to {output_file}")
        return 0

    results = []
    failed_count = 0
    
    logger.info(f"Found {len(csv_files)} datasets to process")
    
    for csv_file in csv_files:
        dataset_path = os.path.join(raw_data_path, csv_file)
        dataset_name = os.path.splitext(csv_file)[0]
        
        entry = process_dataset_for_baseline(dataset_path, dataset_name, config, logger)
        if entry:
            results.append(entry)
        else:
            failed_count += 1
    
    # Compile final report
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'tool': 'llmXive T013',
            'datasets_processed': len(results),
            'datasets_failed': failed_count,
            'config': {
                'random_seed': config.get('RANDOM_SEED', 42),
                'raw_data_path': raw_data_path
            }
        },
        'datasets': results
    }
    
    # Write output
    try:
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Baseline metrics written to {output_file}")
        
        # Log summary
        log_metrics_summary(results, logger)
        
        if failed_count > 0:
            logger.warning(f"Failed to process {failed_count} datasets")
            
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)
        
    logger.info("Task T013 completed successfully")
    return 0

if __name__ == '__main__':
    sys.exit(main())
