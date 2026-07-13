"""
Task T013: Record baseline metrics to data/processed/baseline_metrics.json.

This script runs the baseline analysis on available datasets and records
p-values, 95% CIs, and effect sizes (Cohen's d / R²) with ≥3 decimal precision.
"""
import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_loader import load_datasets_from_raw, ensure_data_exists
from analysis import run_baseline_analysis
from utils import setup_logging, compute_file_checksum
from config import get_config

logger = logging.getLogger(__name__)

def format_metric_value(value: float, precision: int = 6) -> float:
    """Round metric values to specified precision."""
    if value is None or (isinstance(value, float) and (value != value)):  # NaN check
        return None
    return round(float(value), precision)

def log_metrics_summary(metrics: List[Dict[str, Any]]) -> None:
    """Log a summary of recorded metrics."""
    logger.info(f"Recording {len(metrics)} baseline metric entries.")
    for entry in metrics:
        ds_name = entry.get('dataset_name', 'Unknown')
        logger.info(f"  - {ds_name}: p-value={entry.get('p_value')}, "
                    f"ci_width={entry.get('ci_width')}, effect_size={entry.get('effect_size')}")

def process_dataset_for_baseline(
    df: Any, 
    dataset_name: str, 
    config: Optional[Any] = None,
    outcome_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run baseline analysis on a single dataset and format results.
    
    Args:
        df: The dataframe to analyze.
        dataset_name: Name identifier for the dataset.
        config: Optional config object (unused here but kept for signature compatibility).
        outcome_col: Optional specific outcome column.
    
    Returns:
        Dictionary containing baseline metrics with required precision.
    """
    logger.info(f"Processing baseline for dataset: {dataset_name}")
    
    # Run the baseline analysis using the shared function
    # The function signature in analysis.py handles both dict and df inputs
    results = run_baseline_analysis(
        df, 
        dataset_name=dataset_name,
        outcome_col=outcome_col
    )
    
    if not results:
        logger.warning(f"No results returned for {dataset_name}")
        return {}

    # The results from run_baseline_analysis are typically a dict of test results
    # We need to aggregate them into the format expected by baseline_metrics.json
    # Expected format: { dataset_name, strategy, metrics: { p_value, ci_width, effect_size } }
    
    formatted_entry = {
        "dataset_name": dataset_name,
        "strategy": "raw_baseline",
        "timestamp": datetime.utcnow().isoformat(),
        "analysis": {}
    }
    
    # Extract metrics from results
    # The results dict usually looks like: { 't_test': {...}, 'regression': {...} }
    for test_name, test_data in results.items():
        p_val = test_data.get('p_value')
        ci = test_data.get('ci')
        effect = test_data.get('effect_size')
        
        # Calculate CI width if available
        ci_width = None
        if ci and isinstance(ci, (list, tuple)) and len(ci) == 2:
            ci_width = abs(ci[1] - ci[0])
        
        formatted_entry['analysis'][test_name] = {
            "p_value": format_metric_value(p_val),
            "ci": [format_metric_value(ci[0]), format_metric_value(ci[1])] if ci else None,
            "ci_width": format_metric_value(ci_width),
            "effect_size": format_metric_value(effect)
        }
        
        # Also store top-level aggregated values if present
        if p_val is not None:
            formatted_entry['p_value'] = format_metric_value(p_val)
        if ci_width is not None:
            formatted_entry['ci_width'] = format_metric_value(ci_width)
        if effect is not None:
            formatted_entry['effect_size'] = format_metric_value(effect)

    return formatted_entry

def main():
    """Main entry point for T013."""
    setup_logging("INFO")
    logger.info("Starting T013: Record baseline metrics")
    
    config = get_config()
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    output_path = os.path.join(processed_dir, "baseline_metrics.json")
    
    # Ensure data exists
    logger.info("Ensuring dataset availability...")
    ensure_data_exists()
    
    # Load datasets
    logger.info("Loading datasets from raw...")
    datasets = load_datasets_from_raw()
    
    if not datasets:
        logger.error("No datasets found to process.")
        # Create an empty file to indicate completion (even if no data)
        os.makedirs(processed_dir, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump({"datasets": [], "metadata": {"error": "No datasets found"}}, f, indent=2)
        return

    all_metrics = []
    
    for ds in datasets:
        df = ds.get('data')
        name = ds.get('name', 'unknown')
        
        if df is None:
            logger.warning(f"Skipping {name}: No data loaded.")
            continue
        
        try:
            entry = process_dataset_for_baseline(df, name, config)
            if entry:
                all_metrics.append(entry)
        except Exception as e:
            logger.error(f"Failed to process {name}: {e}", exc_info=True)
            continue
    
    # Compute checksum of the output file content before writing
    # We write first, then compute checksum of the written file
    os.makedirs(processed_dir, exist_ok=True)
    
    output_data = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "task_id": "T013",
            "total_datasets": len(all_metrics)
        },
        "datasets": all_metrics
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Wrote baseline metrics to {output_path}")
    
    # Compute and log checksum
    checksum = compute_file_checksum(output_path)
    logger.info(f"Output checksum (SHA256): {checksum}")
    
    log_metrics_summary(all_metrics)
    logger.info("T013 completed successfully.")

if __name__ == "__main__":
    main()