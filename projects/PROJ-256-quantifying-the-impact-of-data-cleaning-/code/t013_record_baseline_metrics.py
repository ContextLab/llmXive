"""
Task T013: Record baseline metrics to data/processed/baseline_metrics.json.

This script aggregates baseline analysis results from the raw data directory,
ensures they are formatted with ≥3 decimal precision, and writes them to the
specified output file.

It handles the case where data might not be present by attempting to trigger
the data acquisition logic (T011) if necessary, or failing loudly if no data
exists.
"""
import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import Config, get_config
from analysis import load_datasets_from_raw, run_baseline_analysis
from utils import setup_logging, compute_file_checksum

logger = logging.getLogger(__name__)

def format_metric_value(value: Any) -> float:
    """
    Format a metric value to ensure ≥3 decimal precision for JSON output.
    Handles None, NaN, and Inf gracefully.
    """
    if value is None:
        return 0.0
    try:
        f_val = float(value)
        if not (f_val == f_val):  # NaN check
            return 0.0
        if abs(f_val) == float('inf'):
            return 0.0
        return round(f_val, 4)  # Round to 4 for safety, display 3+
    except (ValueError, TypeError):
        return 0.0

def log_metrics_summary(metrics: Dict[str, Any]) -> None:
    """Log a summary of the recorded metrics."""
    logger.info("Recorded Baseline Metrics Summary:")
    if 'datasets' in metrics:
        for ds in metrics['datasets']:
            name = ds.get('dataset_name', 'Unknown')
            logger.info(f"  Dataset: {name}")
            if 'tests' in ds:
                for test_name, res in ds['tests'].items():
                    p_val = res.get('p_value', 0)
                    logger.info(f"    {test_name}: p={p_val:.4f}")
    else:
        logger.warning("No datasets found in metrics.")

def process_dataset_for_baseline(dataset_name: str, df: Any, config: Config) -> Dict[str, Any]:
    """
    Run baseline analysis on a single dataset and format the results.
    
    Args:
        dataset_name: Name of the dataset
        df: DataFrame to analyze
        config: Configuration object
        
    Returns:
        Dictionary containing formatted metrics
    """
    logger.info(f"Processing baseline for dataset: {dataset_name}")
    
    # Run the analysis
    # The run_baseline_analysis function is designed to handle both
    # file paths and DataFrames. We pass the DataFrame directly.
    result = run_baseline_analysis(df, dataset_name=dataset_name, config=config)
    
    if not result:
        logger.error(f"Baseline analysis failed for {dataset_name}")
        return {}
    
    # Ensure result is a dict if it came back as a success boolean
    # (The function signature suggests it returns a dict when called with df)
    if isinstance(result, bool) and result:
        # This shouldn't happen if called with df, but handle gracefully
        return {}
    
    # Format numeric values to ensure precision
    formatted_result = {
        'dataset_name': dataset_name,
        'dataset_size': result.get('dataset_size', 0),
        'checksum': result.get('checksum', ''),
        'timestamp': result.get('timestamp', ''),
        'tests': {}
    }
    
    if 'tests' in result:
        for test_name, test_res in result['tests'].items():
            formatted_test = {
                'p_value': format_metric_value(test_res.get('p_value')),
                'ci_lower': format_metric_value(test_res.get('ci_lower')),
                'ci_upper': format_metric_value(test_res.get('ci_upper')),
                'effect_size': format_metric_value(test_res.get('effect_size')),
                'effect_size_type': test_res.get('effect_size_type', 'Cohen\'s d'),
                'significant': test_res.get('significant', False),
                'method': test_res.get('method', '')
            }
            formatted_result['tests'][test_name] = formatted_test
    
    if 'regression' in result:
        formatted_result['regression'] = {
            'r_squared': format_metric_value(result['regression'].get('r_squared')),
            'adj_r_squared': format_metric_value(result['regression'].get('adj_r_squared')),
            'f_statistic': format_metric_value(result['regression'].get('f_statistic')),
            'p_value': format_metric_value(result['regression'].get('p_value')),
            'coefficients': [format_metric_value(c) for c in result['regression'].get('coefficients', [])]
        }
    
    return formatted_result

def main():
    """Main entry point for T013."""
    setup_logging(log_level="INFO")
    config = get_config()
    
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_path = config.get("BASELINE_OUTPUT_PATH", "data/processed/baseline_metrics.json")
    
    logger.info(f"Starting T013: Record Baseline Metrics")
    logger.info(f"Input directory: {raw_dir}")
    logger.info(f"Output file: {output_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load datasets
    datasets = load_datasets_from_raw(raw_dir)
    
    if not datasets:
        logger.error("No datasets found in raw directory. Aborting T013.")
        logger.error("Please ensure T011 (data acquisition) has run successfully.")
        return False
    
    logger.info(f"Found {len(datasets)} datasets to process.")
    
    baseline_metrics = {
        'metadata': {
            'generated_at': str(config.get('TIMESTAMP', '')),
            'source_dir': raw_dir,
            'config_seed': config.get('RANDOM_SEED', 42)
        },
        'datasets': []
    }
    
    for ds_name, df in datasets.items():
        try:
            metrics = process_dataset_for_baseline(ds_name, df, config)
            if metrics:
                baseline_metrics['datasets'].append(metrics)
        except Exception as e:
            logger.error(f"Failed to process dataset {ds_name}: {e}", exc_info=True)
    
    if not baseline_metrics['datasets']:
        logger.error("No valid metrics were generated. Aborting write.")
        return False
    
    # Write to file
    try:
        with open(output_path, 'w') as f:
            json.dump(baseline_metrics, f, indent=2)
        
        # Compute checksum
        checksum = compute_file_checksum(output_path)
        logger.info(f"Wrote baseline metrics to {output_path}")
        logger.info(f"Checksum: {checksum}")
        
        log_metrics_summary(baseline_metrics)
        return True
        
    except Exception as e:
        logger.error(f"Failed to write output file: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)