import os
import sys
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Import from existing project modules
from utils import setup_logging, compute_file_checksum
from config import get_config
from analysis import run_baseline_analysis, load_datasets_from_raw

logger = setup_logging("INFO")

def format_metric_value(value: float, precision: int = 3) -> float:
    """Format a metric value to the specified precision."""
    if value is None or (isinstance(value, float) and (value != value)): # Check for NaN
        return None
    return round(float(value), precision)

def validate_metric_entry(entry: Dict[str, Any]) -> bool:
    """Validate that a metric entry has the required structure and valid values."""
    required_keys = ['dataset_name', 'p_value', 'ci', 'effect_size', 'analysis_type']
    if not all(key in entry for key in required_keys):
        return False
    
    # Validate p-value range
    p_val = entry.get('p_value')
    if p_val is not None and not (0 < p_val < 1):
        logger.warning(f"Invalid p-value {p_val} for {entry.get('dataset_name')}")
        return False
    
    # Validate CI bounds
    ci = entry.get('ci')
    if ci:
        if not isinstance(ci, (list, tuple)) or len(ci) != 2:
            logger.warning(f"Invalid CI format {ci} for {entry.get('dataset_name')}")
            return False
        if not all(isinstance(x, (int, float)) and x == x for x in ci): # Check for NaN
            logger.warning(f"Invalid CI values {ci} for {entry.get('dataset_name')}")
            return False
    
    return True

def log_metrics_summary(metrics: Dict[str, Any]) -> None:
    """Log a summary of the recorded metrics."""
    logger.info("=== Baseline Metrics Summary ===")
    datasets = metrics.get('datasets', [])
    logger.info(f"Total datasets analyzed: {len(datasets)}")
    
    valid_p_values = [d['p_value'] for d in datasets if d.get('p_value') is not None]
    if valid_p_values:
        logger.info(f"P-value range: [{min(valid_p_values):.4f}, {max(valid_p_values):.4f}]")
    
    # Log specific details for each dataset
    for ds in datasets:
        name = ds.get('dataset_name', 'Unknown')
        p_val = ds.get('p_value', 'N/A')
        effect = ds.get('effect_size', 'N/A')
        logger.info(f"  - {name}: p={p_val}, effect_size={effect}")

def process_dataset_for_baseline(dataset_path: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset for baseline analysis and record metrics.
    Returns a dictionary containing the metrics or None if analysis fails.
    """
    dataset_name = Path(dataset_path).stem
    logger.info(f"Processing dataset: {dataset_name}")

    try:
        # Run baseline analysis
        # We need to extract the specific test results from the analysis output
        # The run_baseline_analysis function returns a structure containing results
        result = run_baseline_analysis(
            raw_dir=os.path.dirname(dataset_path),
            output_file=None, # We handle writing manually to aggregate
            analysis_config=config
        )

        if not result:
            logger.error(f"Analysis returned no result for {dataset_name}")
            return None

        # Extract metrics based on the structure returned by run_baseline_analysis
        # Assuming result contains 't_test' and 'regression' keys
        metrics_entry = {
            "dataset_name": dataset_name,
            "dataset_path": dataset_path,
            "checksum": compute_file_checksum(dataset_path),
            "timestamp": datetime.now().isoformat(),
            "t_test": None,
            "regression": None,
            "p_value": None,
            "ci": None,
            "effect_size": None,
            "analysis_type": "baseline"
        }

        # Process T-test results
        if 't_test' in result:
            t_res = result['t_test']
            p_val = t_res.get('pvalue')
            ci_bounds = t_res.get('ci', (None, None))
            eff_size = t_res.get('effect_size') # Cohen's d

            if p_val is not None:
                metrics_entry['p_value'] = format_metric_value(p_val)
                metrics_entry['ci'] = [format_metric_value(ci_bounds[0]), format_metric_value(ci_bounds[1])]
                metrics_entry['effect_size'] = format_metric_value(eff_size) if eff_size is not None else None
                metrics_entry['t_test'] = {
                    'statistic': format_metric_value(t_res.get('statistic')),
                    'pvalue': metrics_entry['p_value'],
                    'ci': metrics_entry['ci'],
                    'effect_size': metrics_entry['effect_size']
                }

        # Process Regression results
        if 'regression' in result:
            reg_res = result['regression']
            # For regression, we might use R-squared as effect size and p-value of the model or a specific coefficient
            r_sq = reg_res.get('rsquared')
            coef_pval = reg_res.get('pvalues', [None])[0] if isinstance(reg_res.get('pvalues'), list) else reg_res.get('pvalue')
            
            if coef_pval is not None:
                metrics_entry['p_value'] = format_metric_value(coef_pval) # Use regression p-value if t-test is missing
                metrics_entry['effect_size'] = format_metric_value(r_sq) if r_sq is not None else None
                metrics_entry['regression'] = {
                    'r_squared': format_metric_value(r_sq),
                    'pvalue': metrics_entry['p_value'],
                    'coefficients': [format_metric_value(c) for c in reg_res.get('coefficients', [])]
                }
        
        # Fallback validation: ensure we have at least one valid metric
        if metrics_entry['p_value'] is None:
            logger.warning(f"No valid p-value found for {dataset_name} in analysis result.")
            return None

        return metrics_entry

    except Exception as e:
        logger.error(f"Failed to process dataset {dataset_name}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for T013: Record baseline metrics to data/processed/baseline_metrics.json.
    This script aggregates results from existing datasets and writes the final JSON.
    """
    logger.info("Starting T013: Record Baseline Metrics")
    
    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = config.get("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Load available datasets
    datasets = load_datasets_from_raw(raw_dir)
    
    if not datasets:
        logger.warning(f"No datasets found in {raw_dir}. Exiting.")
        # Create an empty metrics file to satisfy the contract, even if empty
        empty_metrics = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "datasets": [],
            "summary": {"total_datasets": 0, "valid_analyses": 0}
        }
        with open(output_file, 'w') as f:
            json.dump(empty_metrics, f, indent=2)
        return

    logger.info(f"Found {len(datasets)} datasets to process.")

    all_metrics = []
    valid_count = 0

    for dataset_path in datasets:
        metrics = process_dataset_for_baseline(dataset_path, config)
        if metrics and validate_metric_entry(metrics):
            all_metrics.append(metrics)
            valid_count += 1
        else:
            logger.warning(f"Skipping invalid metrics for {dataset_path}")

    # Construct the final output structure
    final_report = {
        "version": "1.0",
        "timestamp": datetime.now().isoformat(),
        "datasets": all_metrics,
        "summary": {
            "total_datasets": len(datasets),
            "valid_analyses": valid_count,
            "failed_analyses": len(datasets) - valid_count
        }
    }

    # Write to disk
    try:
        with open(output_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        logger.info(f"Successfully wrote baseline metrics to {output_file}")
        log_metrics_summary(final_report)
    except IOError as e:
        logger.error(f"Failed to write metrics file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()