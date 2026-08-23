"""
Assemble the final paired dataset by merging 2D agent results and 3D baseline results.

This module aggregates 2D agent runs (multiple runs per task) and merges them with
the single 3D baseline run per task to create a canonical paired dataset for
statistical analysis.

Output: results/analysis/final_paired_dataset.csv
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths (relative to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
ANALYSIS_DIR = os.path.join(RESULTS_DIR, 'analysis')
RUNS_DIR = os.path.join(RESULTS_DIR, 'runs')
BASELINE_LOGS_DIR = os.path.join(RESULTS_DIR, 'logs')

# Output file
OUTPUT_FILE = os.path.join(ANALYSIS_DIR, 'final_paired_dataset.csv')

# Input patterns
RUN_2D_PATTERN = 'run_{run_id}.json'
BASELINE_FILE = 'baseline_run.json'


def load_yaml_config_simple(config_path: str) -> Dict[str, Any]:
    """Load a simple YAML config file (minimal parser for power_config.yaml)."""
    config = {}
    if not os.path.exists(config_path):
        logger.warning(f"Config file not found: {config_path}")
        return config

    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Try to parse as number
                try:
                    if '.' in value:
                        config[key] = float(value)
                    else:
                        config[key] = int(value)
                except ValueError:
                    config[key] = value
    return config


def load_baseline_results(baseline_file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load 3D baseline results from the baseline_run.json file.

    Expected schema:
    {
        "task_id": {
            "task_type": str,
            "success": bool,
            "latency_ms": float,
            ...
        },
        ...
    }

    Returns: dict mapping task_id -> {task_type, success, latency_ms}
    """
    if not os.path.exists(baseline_file_path):
        raise FileNotFoundError(f"Baseline results file not found: {baseline_file_path}")

    with open(baseline_file_path, 'r') as f:
        data = json.load(f)

    baseline_dict = {}
    for task_id, result in data.items():
        baseline_dict[task_id] = {
            'task_type': result.get('task_type'),
            'success': result.get('success'),
            'latency_ms': result.get('latency_ms')
        }

    return baseline_dict


def load_2d_run_results(run_id: int) -> Dict[str, Dict[str, Any]]:
    """
    Load 2D agent results for a specific run.

    Expected file: results/runs/run_{run_id}.json
    Expected schema:
    {
        "task_id": {
            "task_type": str,
            "success_flag": bool,
            "latency_ms": float,
            ...
        },
        ...
    }

    Returns: dict mapping task_id -> {task_type, success_flag, latency_ms}
    """
    run_file = os.path.join(RUNS_DIR, f'run_{run_id}.json')
    if not os.path.exists(run_file):
        logger.warning(f"Run file not found: {run_file}")
        return {}

    with open(run_file, 'r') as f:
        data = json.load(f)

    run_dict = {}
    for task_id, result in data.items():
        run_dict[task_id] = {
            'task_type': result.get('task_type'),
            'success_flag': result.get('success_flag'),
            'latency_ms': result.get('latency_ms')
        }

    return run_dict


def aggregate_2d_results(n_runs: int) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate 2D agent results across all runs.

    For each task_id, calculate:
    - 2d_success_rate: mean of success_flag (treated as 0/1)
    - 2d_mean_latency: mean of latency_ms

    Returns: dict mapping task_id -> {2d_success_rate, 2d_mean_latency, task_type}
    """
    # Collect all runs
    all_runs: List[Dict[str, Dict[str, Any]]] = []
    for run_id in range(n_runs):
        run_data = load_2d_run_results(run_id)
        all_runs.append(run_data)
        logger.info(f"Loaded run {run_id}: {len(run_data)} tasks")

    if not all_runs:
        raise ValueError("No 2D run results found")

    # Aggregate by task_id
    aggregated: Dict[str, Dict[str, Any]] = {}

    for task_id in all_runs[0].keys():
        success_flags = []
        latencies = []
        task_type = None

        for run_data in all_runs:
            if task_id in run_data:
                result = run_data[task_id]
                success_flags.append(1 if result.get('success_flag', False) else 0)
                latencies.append(result.get('latency_ms', 0.0))
                if task_type is None:
                    task_type = result.get('task_type')

        if success_flags:
          aggregated[task_id] = {
              '2d_success_rate': sum(success_flags) / len(success_flags),
              '2d_mean_latency': sum(latencies) / len(latencies),
              'task_type': task_type
          }
        else:
            logger.warning(f"No valid data for task_id: {task_id}")

    return aggregated


def build_paired_dataset(
    aggregated_2d: Dict[str, Dict[str, Any]],
    baseline_3d: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge 2D aggregated results with 3D baseline results.

    Schema:
    [
        {
            'task_id': str,
            'task_type': str,
            '2d_success_rate': float,
            '2d_mean_latency': float,
            '3d_success': bool,
            '3d_latency': float,
            'success_diff': float,
            'latency_diff': float
        },
        ...
    ]
    """
    paired = []

    # Use 2D tasks as the base (should match baseline tasks)
    for task_id, agg_2d in aggregated_2d.items():
        if task_id not in baseline_3d:
            logger.warning(f"Task {task_id} in 2D results but not in baseline")
            continue

        base_3d = baseline_3d[task_id]

        # Calculate differences
        # success_diff: 2d_success_rate - 3d_success (3d_success is 0 or 1)
        success_diff = agg_2d['2d_success_rate'] - (1 if base_3d['success'] else 0)
        # latency_diff: 2d_mean_latency - 3d_latency
        latency_diff = agg_2d['2d_mean_latency'] - base_3d['latency_ms']

        paired.append({
            'task_id': task_id,
            'task_type': agg_2d['task_type'],
            '2d_success_rate': agg_2d['2d_success_rate'],
            '2d_mean_latency': agg_2d['2d_mean_latency'],
            '3d_success': base_3d['success'],
            '3d_latency': base_3d['latency_ms'],
            'success_diff': success_diff,
            'latency_diff': latency_diff
        })

    # Sort by task_id
    paired.sort(key=lambda x: x['task_id'])

    return paired


def verify_no_nulls(paired_data: List[Dict[str, Any]]) -> bool:
    """
    Verify that no critical columns have null/None values.

    Critical columns: task_id, task_type, 2d_success_rate, 2d_mean_latency,
                     3d_success, 3d_latency, success_diff, latency_diff
    """
    critical_cols = [
        'task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
        '3d_success', '3d_latency', 'success_diff', 'latency_diff'
    ]

    for row in paired_data:
        for col in critical_cols:
            if row.get(col) is None:
                logger.error(f"Null value found in {col} for task_id {row.get('task_id')}")
                return False

    return True


def write_csv(paired_data: List[Dict[str, Any]], output_path: str) -> None:
    """Write the paired dataset to a CSV file."""
    if not paired_data:
        logger.warning("No data to write")
        return

    fieldnames = [
        'task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
        '3d_success', '3d_latency', 'success_diff', 'latency_diff'
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(paired_data)

    logger.info(f"Wrote {len(paired_data)} rows to {output_path}")


def main():
    """Main entry point for assembling the paired dataset."""
    parser = argparse.ArgumentParser(description='Assemble final paired dataset')
    parser.add_argument('--config', type=str, default='data/power_config.yaml',
                      help='Path to power config file')
    parser.add_argument('--baseline', type=str, default=None,
                      help='Path to baseline results file (default: auto-detect)')
    parser.add_argument('--n-runs', type=int, default=None,
                      help='Number of 2D runs (default: read from config)')
    args = parser.parse_args()

    # Load config
    config_path = os.path.join(PROJECT_ROOT, args.config)
    config = load_yaml_config_simple(config_path)
    n_runs = args.n_runs if args.n_runs else config.get('n_runs', 5)
    logger.info(f"Using n_runs={n_runs}")

    # Load baseline results
    baseline_path = args.baseline
    if baseline_path is None:
        baseline_path = os.path.join(BASELINE_LOGS_DIR, BASELINE_FILE)

    logger.info(f"Loading baseline from: {baseline_path}")
    baseline_3d = load_baseline_results(baseline_path)
    logger.info(f"Loaded {len(baseline_3d)} baseline tasks")

    # Aggregate 2D results
    logger.info("Aggregating 2D results...")
    aggregated_2d = aggregate_2d_results(n_runs)
    logger.info(f"Aggregated {len(aggregated_2d)} tasks from 2D runs")

    # Build paired dataset
    logger.info("Building paired dataset...")
    paired_data = build_paired_dataset(aggregated_2d, baseline_3d)
    logger.info(f"Built paired dataset with {len(paired_data)} tasks")

    # Verify no nulls
    logger.info("Verifying data integrity...")
    if not verify_no_nulls(paired_data):
        logger.error("Data verification failed: null values found")
        # Still write what we have but exit with error code
        # In a real scenario, we might want to abort here
        write_csv(paired_data, OUTPUT_FILE)
        return 1

    # Write output
    write_csv(paired_data, OUTPUT_FILE)

    logger.info("Paired dataset assembly complete")
    return 0


if __name__ == '__main__':
    exit(main())