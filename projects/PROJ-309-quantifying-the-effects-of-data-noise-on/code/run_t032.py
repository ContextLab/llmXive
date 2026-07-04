"""
Task T032: Write metric results and error tables to data/processed/ as metrics_summary.csv

This script aggregates metric results and error calculations from previous tasks
(T017 for ground truth, T030 for error calculation) and exports them to a CSV file.
"""
import os
import sys
import json
import glob
import logging
import argparse
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_ground_truth_metrics_files(base_dir: str = "data/processed") -> List[str]:
    """Find all ground truth metrics JSON files."""
    pattern = os.path.join(base_dir, "ground_truth_metrics_*.json")
    files = glob.glob(pattern)
    logger.info(f"Found {len(files)} ground truth metrics files matching {pattern}")
    return sorted(files)

def find_noisy_metrics_files(base_dir: str = "data/processed") -> List[str]:
    """Find all noisy trajectory metrics JSON files."""
    pattern = os.path.join(base_dir, "noisy_metrics_*.json")
    files = glob.glob(pattern)
    logger.info(f"Found {len(files)} noisy metrics files matching {pattern}")
    return sorted(files)

def find_error_results_files(base_dir: str = "data/processed") -> List[str]:
    """Find all error calculation result JSON files from T030."""
    pattern = os.path.join(base_dir, "error_results_*.json")
    files = glob.glob(pattern)
    logger.info(f"Found {len(files)} error results files matching {pattern}")
    return sorted(files)

def load_ground_truth_metrics(filepath: str) -> Dict[str, Any]:
    """Load ground truth metrics from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_noisy_metrics(filepath: str) -> Dict[str, Any]:
    """Load noisy trajectory metrics from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_error_results(filepath: str) -> Dict[str, Any]:
    """Load error calculation results from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_results_to_dataframe(
    error_files: List[str],
    noisy_files: List[str],
    ground_truth_files: List[str]
) -> pd.DataFrame:
    """
    Aggregate all error results into a single DataFrame.
    
    Expected columns: SNR_dB, noise_type, metric_name, computed_value, 
    ground_truth_value, error_percent
    """
    all_records = []

    # Load ground truth values for reference
    ground_truth_map = {}
    for gt_file in ground_truth_files:
        gt_data = load_ground_truth_metrics(gt_file)
        seed = gt_data.get('seed', 'unknown')
        ground_truth_map[seed] = gt_data.get('metrics', {})

    # Process each error result file
    for error_file in error_files:
        try:
            error_data = load_error_results(error_file)
            
            # Extract metadata
            snr_db = error_data.get('snr_db')
            noise_type = error_data.get('noise_type')
            seed = error_data.get('seed')
            
            # Get metrics and errors
            metrics = error_data.get('metrics', {})
            errors = error_data.get('errors', {})
            
            for metric_name, computed_value in metrics.items():
                ground_truth_value = metrics.get(f"{metric_name}_gt", 
                                                 ground_truth_map.get(seed, {}).get(metric_name))
                
                # Handle case where ground truth might be None
                if ground_truth_value is None:
                    # Try to get from errors dict if available
                    error_record = errors.get(metric_name, {})
                    ground_truth_value = error_record.get('ground_truth_value')
                
                error_percent = errors.get(metric_name, {}).get('error_percent')
                
                record = {
                    'SNR_dB': snr_db,
                    'noise_type': noise_type,
                    'seed': seed,
                    'metric_name': metric_name,
                    'computed_value': computed_value,
                    'ground_truth_value': ground_truth_value,
                    'error_percent': error_percent
                }
                all_records.append(record)
                
        except Exception as e:
            logger.error(f"Error processing {error_file}: {e}")
            continue

    if not all_records:
        logger.warning("No records found to aggregate")
        return pd.DataFrame()

    df = pd.DataFrame(all_records)
    
    # Sort by SNR, noise type, metric name
    df = df.sort_values(by=['SNR_dB', 'noise_type', 'metric_name'])
    
    return df

def export_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """Export DataFrame to CSV file."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Exported {len(df)} records to {output_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Aggregate metric results and errors to CSV (Task T032)"
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        default="data/processed",
        help="Base directory for input files"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/metrics_summary.csv",
        help="Output CSV file path"
    )
    args = parser.parse_args()

    logger.info(f"Starting T032: Aggregating results from {args.base_dir}")

    # Find input files
    error_files = find_error_results_files(args.base_dir)
    noisy_files = find_noisy_metrics_files(args.base_dir)
    ground_truth_files = find_ground_truth_metrics_files(args.base_dir)

    if not error_files:
        logger.error("No error results files found. Ensure T030 has been run.")
        sys.exit(1)

    if not ground_truth_files:
        logger.warning("No ground truth metrics files found. Ensure T017 has been run.")

    # Aggregate results
    df = aggregate_results_to_dataframe(
        error_files,
        noisy_files,
        ground_truth_files
    )

    if df.empty:
        logger.error("No data to export. Check input files.")
        sys.exit(1)

    # Export to CSV
    export_to_csv(df, args.output_path)

    logger.info(f"T032 completed successfully. Output: {args.output_path}")
    print(f"Metrics summary exported to: {args.output_path}")
    print(f"Total records: {len(df)}")
    print(f"SNR levels: {sorted(df['SNR_dB'].unique())}")
    print(f"Metrics: {sorted(df['metric_name'].unique())}")

if __name__ == "__main__":
    main()
