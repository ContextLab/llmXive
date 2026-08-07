"""
Final Paired Dataset Assembly for SpatialClaw Restriction Project.

Merges 2D agent results (aggregated across runs) and 3D baseline results
into a single canonical CSV file for statistical analysis.

Output: results/analysis/final_paired_dataset.csv
Schema: task_id, task_type, 2d_success_rate, 2d_mean_latency, 3d_success, 3d_latency, success_diff, latency_diff
"""

import os
import json
import csv
import logging
import argparse
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_yaml_config_simple(config_path: str) -> Dict[str, Any]:
    """
    Load a simple YAML config file.
    Note: This is a minimal parser for the specific format used in power_config.yaml.
    """
    config = {}
    try:
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Try to convert to appropriate type
                    if value.lower() == 'true':
                        config[key] = True
                    elif value.lower() == 'false':
                        config[key] = False
                    else:
                        try:
                            if '.' in value:
                                config[key] = float(value)
                            else:
                                config[key] = int(value)
                        except ValueError:
                            config[key] = value
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_path}")
        raise
    return config


def load_baseline_results(baseline_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load 3D baseline results from JSON file.

    Args:
        baseline_path: Path to results/logs/baseline_run.json

    Returns:
        Dict mapping task_id to result dict
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline results file not found: {baseline_path}")

    with open(baseline_path, 'r') as f:
        data = json.load(f)

    # Handle both list and dict formats
    if isinstance(data, list):
        results = {item['task_id']: item for item in data}
    else:
        results = data

    logger.info(f"Loaded {len(results)} baseline results from {baseline_path}")
    return results


def load_2d_run_results(runs_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all 2D agent run results from individual JSON files.

    Args:
        runs_dir: Directory containing results/runs/run_*.json files

    Returns:
        Dict mapping task_id to list of result dicts across runs
    """
    results = {}
    run_files = sorted(glob.glob(os.path.join(runs_dir, 'run_*.json')))

    if not run_files:
        raise FileNotFoundError(f"No 2D run result files found in {runs_dir}")

    for run_file in run_files:
        with open(run_file, 'r') as f:
            run_data = json.load(f)

        # Handle both list and dict formats
        if isinstance(run_data, list):
            for item in run_data:
                task_id = item['task_id']
                if task_id not in results:
                    results[task_id] = []
                results[task_id].append(item)
        else:
            # Assume dict format with task_id as key
            for task_id, item in run_data.items():
                if task_id not in results:
                    results[task_id] = []
                results[task_id].append(item)

    logger.info(f"Loaded 2D results from {len(run_files)} run files, covering {len(results)} unique tasks")
    return results


def aggregate_2d_results(raw_2d_results: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate 2D results across runs for each task.

    Args:
        raw_2d_results: Dict mapping task_id to list of result dicts

    Returns:
        Dict mapping task_id to aggregated metrics dict
    """
    aggregated = {}

    for task_id, runs in raw_2d_results.items():
        if not runs:
            continue

        # Calculate success rate
        success_count = sum(1 for r in runs if r.get('success', False))
        success_rate = success_count / len(runs)

        # Calculate mean latency
        latencies = [r.get('latency_ms', 0) for r in runs if 'latency_ms' in r]
        mean_latency = sum(latencies) / len(latencies) if latencies else 0.0

        # Get task type from first run (should be consistent across runs)
        task_type = runs[0].get('task_type', 'unknown')

        aggregated[task_id] = {
            'task_id': task_id,
            'task_type': task_type,
            '2d_success_rate': success_rate,
            '2d_mean_latency': mean_latency,
            'n_runs': len(runs)
        }

    logger.info(f"Aggregated 2D results for {len(aggregated)} tasks")
    return aggregated


def build_paired_dataset(
    aggregated_2d: Dict[str, Dict[str, Any]],
    baseline_3d: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Build the final paired dataset by merging 2D and 3D results.

    Args:
        aggregated_2d: Aggregated 2D results
        baseline_3d: 3D baseline results

    Returns:
        List of paired result dicts
    """
    paired = []

    # Find common task IDs
    common_tasks = set(aggregated_2d.keys()) & set(baseline_3d.keys())
    missing_2d = set(baseline_3d.keys()) - set(aggregated_2d.keys())
    missing_3d = set(aggregated_2d.keys()) - set(baseline_3d.keys())

    if missing_2d:
        logger.warning(f"Tasks missing 2D results: {len(missing_2d)}")
    if missing_3d:
        logger.warning(f"Tasks missing 3D results: {len(missing_3d)}")

    for task_id in sorted(common_tasks):
        data_2d = aggregated_2d[task_id]
        data_3d = baseline_3d[task_id]

        # Calculate differences
        success_diff = data_2d['2d_success_rate'] - float(data_3d.get('success', 0))
        latency_diff = data_2d['2d_mean_latency'] - data_3d.get('latency_ms', 0)

        paired_row = {
            'task_id': task_id,
            'task_type': data_2d['task_type'],
            '2d_success_rate': data_2d['2d_success_rate'],
            '2d_mean_latency': data_2d['2d_mean_latency'],
            '3d_success': data_3d.get('success', False),
            '3d_latency': data_3d.get('latency_ms', 0),
            'success_diff': success_diff,
            'latency_diff': latency_diff
        }

        paired.append(paired_row)

    # Sort by task_id
    paired.sort(key=lambda x: x['task_id'])

    # Verify no null values in critical columns
    critical_cols = ['task_id', 'task_type', '2d_success_rate', '2d_mean_latency', '3d_success', '3d_latency']
    for row in paired:
        for col in critical_cols:
            if row[col] is None:
                raise ValueError(f"Null value found in critical column '{col}' for task_id {row['task_id']}")

    logger.info(f"Built paired dataset with {len(paired)} rows")
    return paired


def write_csv(paired_data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write the paired dataset to CSV.

    Args:
        paired_data: List of paired result dicts
        output_path: Path to output CSV file
    """
    if not paired_data:
        raise ValueError("No data to write")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fieldnames = [
        'task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
        '3d_success', '3d_latency', 'success_diff', 'latency_diff'
    ]

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(paired_data)

    logger.info(f"Wrote paired dataset to {output_path}")


def main():
    """Main entry point for assembling the final paired dataset."""
    parser = argparse.ArgumentParser(description='Assemble final paired dataset')
    parser.add_argument('--config', type=str, default='data/power_config.yaml',
                      help='Path to power config file')
    parser.add_argument('--baseline', type=str, default='results/logs/baseline_run.json',
                      help='Path to baseline results')
    parser.add_argument('--runs-dir', type=str, default='results/runs',
                      help='Directory containing 2D run results')
    parser.add_argument('--output', type=str, default='results/analysis/final_paired_dataset.csv',
                      help='Output CSV path')

    args = parser.parse_args()

    try:
        # Load config (optional, mainly for validation)
        if os.path.exists(args.config):
            config = load_yaml_config_simple(args.config)
            logger.info(f"Loaded config: {config.get('n_runs', 'N/A')} runs expected")

        # Load baseline results
        baseline_results = load_baseline_results(args.baseline)

        # Load and aggregate 2D results
        raw_2d = load_2d_run_results(args.runs_dir)
        aggregated_2d = aggregate_2d_results(raw_2d)

        # Build paired dataset
        paired_data = build_paired_dataset(aggregated_2d, baseline_results)

        # Write output
        write_csv(paired_data, args.output)

        logger.info("Final paired dataset assembly completed successfully")

    except Exception as e:
        logger.error(f"Failed to assemble paired dataset: {e}")
        raise


if __name__ == '__main__':
    main()
