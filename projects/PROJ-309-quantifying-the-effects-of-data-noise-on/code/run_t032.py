"""
Task T032: Write metric results and error tables to data/processed/metrics_summary.csv

This script aggregates ground truth metrics, noisy metrics, and error calculations
produced by previous tasks (T017, T030) into a single summary CSV file.
"""
import os
import sys
import json
import glob
import logging
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.io import export_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_ground_truth_metrics_files(ground_truth_dir: str) -> List[str]:
    """Find all ground truth metrics JSON files."""
    pattern = os.path.join(ground_truth_dir, "ground_truth_metrics_*.json")
    files = glob.glob(pattern)
    if not files:
        logger.warning(f"No ground truth metrics files found in {ground_truth_dir}")
    return sorted(files)

def find_noisy_metrics_files(processed_dir: str) -> List[str]:
    """Find all noisy metrics JSON files."""
    pattern = os.path.join(processed_dir, "metrics_*_noise_*.json")
    files = glob.glob(pattern)
    if not files:
        logger.warning(f"No noisy metrics files found in {processed_dir}")
    return sorted(files)

def find_error_results_files(processed_dir: str) -> List[str]:
    """Find all error results JSON files."""
    pattern = os.path.join(processed_dir, "error_results_*_noise_*.json")
    files = glob.glob(pattern)
    if not files:
        logger.warning(f"No error results files found in {processed_dir}")
    return sorted(files)

def load_ground_truth_metrics(filepath: str) -> Dict[str, Any]:
    """Load ground truth metrics from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_noisy_metrics(filepath: str) -> Dict[str, Any]:
    """Load noisy metrics from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def load_error_results(filepath: str) -> Dict[str, Any]:
    """Load error results from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def aggregate_results_to_dataframe(
    ground_truth_files: List[str],
    noisy_files: List[str],
    error_files: List[str]
) -> pd.DataFrame:
    """
    Aggregate all metrics and errors into a single DataFrame.

    Expected columns:
    - system_type: Lorenz or Rössler
    - seed: Random seed used
    - snr_db: Signal-to-noise ratio in dB
    - noise_type: Gaussian or Quantization
    - metric_name: Correlation_Dimension, Lyapunov_Exponent, FNN_Rate
    - ground_truth_value: Value from clean data
    - computed_value: Value from noisy data
    - error_percent: Percentage error
    """
    rows = []

    # Load ground truth values (one per seed/system)
    ground_truth_map = {}
    for filepath in ground_truth_files:
        data = load_ground_truth_metrics(filepath)
        key = (data['system_type'], data['seed'])
        ground_truth_map[key] = {
            'correlation_dimension': data['metrics']['correlation_dimension'],
            'lyapunov_exponent': data['metrics']['lyapunov_exponent'],
            'fnn_rate': data['metrics']['fnn_rate']
        }

    # Process noisy metrics and errors
    for error_filepath in error_files:
        error_data = load_error_results(error_filepath)
        
        system_type = error_data['system_type']
        seed = error_data['seed']
        snr_db = error_data['snr_db']
        noise_type = error_data['noise_type']
        
        gt_key = (system_type, seed)
        if gt_key not in ground_truth_map:
            logger.warning(f"Missing ground truth for {gt_key}, skipping error file {error_filepath}")
            continue

        gt_values = ground_truth_map[gt_key]

        # Process each metric
        for metric_name in ['correlation_dimension', 'lyapunov_exponent', 'fnn_rate']:
            if metric_name in error_data['errors']:
                error_info = error_data['errors'][metric_name]
                
                rows.append({
                    'system_type': system_type,
                    'seed': seed,
                    'snr_db': snr_db,
                    'noise_type': noise_type,
                    'metric_name': metric_name.replace('_', ' ').title().replace(' ', '_'),
                    'ground_truth_value': gt_values[metric_name],
                    'computed_value': error_info['computed_value'],
                    'error_percent': error_info['error_percent']
                })

    if not rows:
        logger.error("No data rows found to aggregate. Check that T017, T030 have run successfully.")
        return pd.DataFrame()

    return pd.DataFrame(rows)

def export_to_csv(df: pd.DataFrame, output_path: str) -> None:
    """Export the DataFrame to a CSV file."""
    if df.empty:
        logger.error("Cannot export empty DataFrame.")
        return

    export_csv(df, output_path)
    logger.info(f"Successfully exported metrics summary to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Aggregate metrics and errors to CSV')
    parser.add_argument('--ground_truth_dir', type=str, default='data/processed',
                        help='Directory containing ground truth metrics JSON files')
    parser.add_argument('--processed_dir', type=str, default='data/processed',
                        help='Directory containing noisy metrics and error JSON files')
    parser.add_argument('--output_file', type=str, default='data/processed/metrics_summary.csv',
                        help='Output CSV file path')
    
    args = parser.parse_args()

    # Ensure output directory exists
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Searching for ground truth files in {args.ground_truth_dir}")
    gt_files = find_ground_truth_metrics_files(args.ground_truth_dir)
    logger.info(f"Found {len(gt_files)} ground truth files")

    logger.info(f"Searching for error files in {args.processed_dir}")
    err_files = find_error_results_files(args.processed_dir)
    logger.info(f"Found {len(err_files)} error result files")

    if not gt_files or not err_files:
        logger.error("Missing required input files. Ensure T017 (Ground Truth) and T030 (Error Calculation) have completed.")
        sys.exit(1)

    logger.info("Aggregating results...")
    df = aggregate_results_to_dataframe(gt_files, [], err_files)

    if df.empty:
        logger.error("Aggregation resulted in an empty DataFrame.")
        sys.exit(1)

    logger.info(f"Exporting to {args.output_file}")
    export_to_csv(df, args.output_file)

    logger.info("T032 completed successfully.")

if __name__ == '__main__':
    main()