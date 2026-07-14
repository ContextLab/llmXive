"""
Task T013: Record baseline metrics (p-value, 95% CI, Cohen's d/R²) to data/processed/baseline_metrics.json.

This script orchestrates the full baseline analysis pipeline for all available datasets,
calling the analysis module to compute statistics, and then aggregating the results
into a single JSON artifact with high precision.

It handles the API contract for run_baseline_analysis (accepting both dict and tuple returns)
and ensures the output file is written to the exact path required by the run-book.
"""
import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path to resolve imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from analysis import run_baseline_analysis
from utils import setup_logging, compute_file_checksum
from config import get_config

logger = setup_logging("INFO")
config = get_config()

def format_metric_value(value: Any, precision: int = 6) -> Any:
    """
    Format numeric metrics to a specific precision, handling None or non-numeric types.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
            return None
        return round(float(value), precision)
    return value

def log_metrics_summary(metrics: Dict[str, Any]) -> None:
    """
    Log a summary of the collected metrics to the console.
    """
    logger.info("=== Baseline Metrics Summary ===")
    total_datasets = len(metrics.get('datasets', []))
    logger.info(f"Total datasets processed: {total_datasets}")

    for ds in metrics.get('datasets', []):
        name = ds.get('dataset_name', 'Unknown')
        logger.info(f"  - {name}: {len(ds.get('tests', []))} tests performed")
        for test_name, test_data in ds.get('tests', {}).items():
            p_val = test_data.get('p_value')
            effect = test_data.get('effect_size')
            logger.info(f"      {test_name}: p={p_val:.4f}, effect={effect:.4f}")
    logger.info("================================")

def process_dataset_for_baseline(
    df: Any,
    dataset_name: str,
    output_dir: str,
    raw_checksum: str
) -> Dict[str, Any]:
    """
    Run baseline analysis on a single dataset and return the structured result.

    Handles the dual API signature of run_baseline_analysis:
    1. run_baseline_analysis(df, dataset_name=..., config=config) -> returns dict
    2. run_baseline_analysis(raw_dir, output_file, config) -> writes file, returns bool
    (We use signature 1 here as we have the dataframe in memory).
    """
    logger.info(f"Processing baseline for dataset: {dataset_name}")

    # Prepare config for the analysis call
    analysis_config = {
        'output_path': output_dir,
        'random_seed': config.get('RANDOM_SEED', 42),
        'bootstrap_iterations': config.get('BOOTSTRAP_ITERATIONS', 1000)
    }

    # Call the analysis function
    # The function is expected to return a dict with 'success' and 'results' keys
    # or a tuple (success, results) in older implementations.
    result = run_baseline_analysis(
        df,
        dataset_name=dataset_name,
        config=analysis_config
    )

    # Handle potential return type variations for robustness
    if isinstance(result, tuple):
        success, results = result
    else:
        success = result.get('success', False)
        results = result.get('results', {})

    if not success:
        logger.error(f"Baseline analysis failed for {dataset_name}")
        return {
            "dataset_name": dataset_name,
            "success": False,
            "error": "Analysis failed",
            "checksum": raw_checksum,
            "timestamp": datetime.now().isoformat()
        }

    # Structure the output to match the expected baseline_metrics.json schema
    # We need to extract p-values, CIs, and effect sizes
    formatted_results = {
        "dataset_name": dataset_name,
        "checksum": raw_checksum,
        "timestamp": datetime.now().isoformat(),
        "success": True,
        "tests": {}
    }

    # The 'results' dict from analysis.py typically contains:
    # { 't_test': {...}, 'regression': {...} }
    # We normalize this into a flat list of tests for the report.
    if 't_test' in results:
        tt = results['t_test']
        formatted_results['tests']['t_test'] = {
            "p_value": format_metric_value(tt.get('p_value'), 6),
            "ci_lower": format_metric_value(tt.get('ci_lower'), 6),
            "ci_upper": format_metric_value(tt.get('ci_upper'), 6),
            "ci_width": format_metric_value(tt.get('ci_upper') - tt.get('ci_lower'), 6),
            "effect_size": format_metric_value(tt.get('effect_size'), 6), # Cohen's d
            "statistic": format_metric_value(tt.get('statistic'), 6)
        }

    if 'regression' in results:
        reg = results['regression']
        # R-squared is the effect size for regression
        r2 = reg.get('r_squared')
        formatted_results['tests']['linear_regression'] = {
            "p_value": format_metric_value(reg.get('p_value'), 6),
            "ci_lower": format_metric_value(reg.get('ci_lower'), 6),
            "ci_upper": format_metric_value(reg.get('ci_upper'), 6),
            "ci_width": format_metric_value(reg.get('ci_upper') - reg.get('ci_lower'), 6),
            "effect_size": format_metric_value(r2, 6), # R-squared
            "coefficients": [format_metric_value(c, 6) for c in reg.get('coefficients', [])]
        }

    return formatted_results

def main():
    """
    Main entry point for T013.
    1. Loads datasets from data/raw (using data_loader logic or direct loading).
    2. Runs baseline analysis on each.
    3. Aggregates results.
    4. Writes to data/processed/baseline_metrics.json.
    """
    logger.info("Starting T013: Record Baseline Metrics")

    # Ensure output directory exists
    output_dir = config.get('PROCESSED_DATA_PATH', 'data/processed')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'baseline_metrics.json')

    # Load datasets. We rely on data_loader.load_datasets_from_raw if available,
    # or we scan the raw directory manually.
    # Since data_loader is available in the API surface:
    from data_loader import load_datasets_from_raw

    raw_dir = config.get('RAW_DATA_PATH', 'data/raw')
    datasets = load_datasets_from_raw(raw_dir)

    if not datasets:
        logger.error("No datasets found in raw directory. Aborting.")
        return 1

    all_metrics = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "tool": "llmXive_pipeline",
            "task_id": "T013",
            "dataset_count": len(datasets)
        },
        "datasets": []
    }

    for dataset_path, dataset_name in datasets:
        # Calculate checksum
        checksum = compute_file_checksum(dataset_path)

        # Process the dataset
        # load_datasets_from_raw returns a list of (path, name) or (df, name) depending on impl.
        # We assume it returns (df, name) or we need to load it.
        # Looking at the API surface, load_datasets_from_raw is in data_loader.
        # Let's assume it returns a list of (df, name) tuples based on context.
        # If it returns paths, we load them here.
        
        # Re-checking typical pattern: load_datasets_from_raw usually returns a list of DataFrames or (df, name)
        # If the function returns paths, we handle that.
        # To be safe, we try to load if it's a path.
        
        df = None
        if isinstance(dataset_path, str):
            if os.path.exists(dataset_path):
                import pandas as pd
                df = pd.read_csv(dataset_path)
                dataset_name = dataset_path.split('/')[-1].replace('.csv', '')
            else:
                logger.warning(f"Dataset path not found: {dataset_path}")
                continue
        else:
            # Assume it's already a dataframe
            df = dataset_path
            dataset_name = dataset_name

        result = process_dataset_for_baseline(df, dataset_name, output_dir, checksum)
        all_metrics['datasets'].append(result)

    # Write the final JSON
    try:
        with open(output_file, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        logger.info(f"Successfully wrote baseline metrics to {output_file}")
        
        # Log summary
        log_metrics_summary(all_metrics)
        
        return 0
    except Exception as e:
        logger.error(f"Failed to write output file: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
