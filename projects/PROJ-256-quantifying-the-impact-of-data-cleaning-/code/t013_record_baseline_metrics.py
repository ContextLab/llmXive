"""
T013: Record baseline metrics to data/processed/baseline_metrics.json.

This script aggregates baseline analysis results from all available raw datasets,
ensures the output JSON contains metrics with >=3 decimal precision, and writes
the final artifact to data/processed/baseline_metrics.json.

It depends on T012 (run_baseline_analysis) having been executed for the raw datasets.
"""
import os
import sys
import json
import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils import setup_logging, compute_file_checksum
from config import get_config
from analysis import load_datasets_from_raw

logger = setup_logging("INFO")
config = get_config()

def format_metric_value(value: Any, precision: int = 3) -> Any:
    """
    Format a numeric metric value to the specified precision.
    Handles floats, lists of floats, and nested dicts.
    """
    if value is None:
        return None
    if isinstance(value, float):
        if not (value == value):  # NaN check
            return None
        return round(value, precision)
    if isinstance(value, list):
        return [format_metric_value(v, precision) for v in value]
    if isinstance(value, dict):
        return {k: format_metric_value(v, precision) for k, v in value.items()}
    return value

def log_metrics_summary(metrics: Dict[str, Any]) -> None:
    """Log a summary of the recorded metrics."""
    logger.info("=== Baseline Metrics Summary ===")
    datasets = metrics.get("datasets", [])
    logger.info(f"Total datasets analyzed: {len(datasets)}")
    
    for entry in datasets:
        name = entry.get("dataset_name", "Unknown")
        logger.info(f"  - {name}:")
        tests = entry.get("analysis", {}).get("tests", {})
        for test_name, test_data in tests.items():
            p_val = test_data.get("p_value")
            if p_val is not None:
                logger.info(f"      {test_name}: p={p_val:.3f}")

def process_dataset_for_baseline(dataset_path: str, dataset_name: str, output_dir: str) -> Optional[Dict[str, Any]]:
    """
    Process a single dataset to extract or compute baseline metrics.
    If baseline analysis has already been run (T012), it loads the result.
    Otherwise, it runs the analysis and saves the result.
    """
    # Define the expected output path for this dataset's baseline metrics
    # T012 writes to data/processed/baseline_metrics.json, but we need per-dataset tracking
    # We will aggregate into a master file.
    
    # Check if raw data exists
    if not os.path.exists(dataset_path):
        logger.warning(f"Dataset not found: {dataset_path}. Skipping.")
        return None

    # Calculate checksum for validation
    checksum = compute_file_checksum(dataset_path)
    
    # Load the dataset to ensure it's valid
    try:
        df = load_datasets_from_raw([dataset_path])
        if df is None or df.empty:
            logger.warning(f"Dataset {dataset_name} is empty or invalid. Skipping.")
            return None
    except Exception as e:
        logger.error(f"Failed to load dataset {dataset_name}: {e}")
        return None

    # The T012 script is responsible for running the analysis and writing the initial file.
    # However, T013's job is to ensure the final aggregated file is correct and precise.
    # We will simulate the "aggregation" logic here by running the analysis if not present,
    # or loading existing results if T012 was run successfully.
    
    # Since T012 writes to a single file, we need to reconstruct the per-dataset structure
    # or re-run the analysis logic for each dataset to build the master list.
    # Given the constraint that T012 might have failed or produced a partial file,
    # we will re-run the analysis for this specific dataset to ensure accuracy.
    
    # Import analysis functions dynamically to avoid circular issues if any
    from analysis import run_baseline_analysis
    
    # Temporary output file for this specific dataset run
    temp_output = os.path.join(output_dir, f"baseline_{dataset_name.replace('.csv', '')}.json")
    
    # Run baseline analysis
    logger.info(f"Running baseline analysis for {dataset_name}...")
    success = run_baseline_analysis(dataset_path, temp_output, config={})
    
    if not success or not os.path.exists(temp_output):
        logger.error(f"Baseline analysis failed for {dataset_name}.")
        return None
    
    # Load the result
    with open(temp_output, 'r') as f:
        result = json.load(f)
    
    # Clean up temp file
    os.remove(temp_output)
    
    # Structure the result for the master report
    dataset_entry = {
        "dataset_name": dataset_name,
        "dataset_path": dataset_path,
        "checksum": checksum,
        "timestamp": datetime.now().isoformat(),
        "analysis": result
    }
    
    return dataset_entry

def main():
    """Main entry point for T013."""
    logger.info("Starting T013: Record Baseline Metrics")
    
    output_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    output_file = os.path.join(output_dir, "baseline_metrics.json")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Identify available raw datasets
    # Based on T011, we expect uci_har.csv and shopper.csv
    raw_files = [
        "uci_har.csv",
        "shopper.csv"
    ]
    
    datasets = []
    for filename in raw_files:
        filepath = os.path.join(raw_dir, filename)
        if os.path.exists(filepath):
            result = process_dataset_for_baseline(filepath, filename, output_dir)
            if result:
                datasets.append(result)
    
    if not datasets:
        logger.warning("No datasets were processed. Creating empty report.")
        final_report = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "datasets": [],
            "summary": {
                "total_datasets": 0,
                "precision": 3
            }
        }
    else:
        # Format all numeric values to >=3 decimal precision
        formatted_datasets = []
        for ds in datasets:
            formatted_ds = format_metric_value(ds, precision=3)
            formatted_datasets.append(formatted_ds)
        
        final_report = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "datasets": formatted_datasets,
            "summary": {
                "total_datasets": len(datasets),
                "precision": 3,
                "note": "SC-006 requires >=10 datasets; current count limited by available public datasets."
            }
        }
    
    # Write the final report
    with open(output_file, 'w') as f:
        json.dump(final_report, f, indent=2)
    
    logger.info(f"Baseline metrics written to {output_file}")
    log_metrics_summary(final_report)
    
    # Verify file exists
    if os.path.exists(output_file):
        logger.info(f"Verification: {output_file} exists.")
        checksum = compute_file_checksum(output_file)
        logger.info(f"Output checksum: {checksum}")
        return True
    else:
        logger.error(f"Verification failed: {output_file} does not exist.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
