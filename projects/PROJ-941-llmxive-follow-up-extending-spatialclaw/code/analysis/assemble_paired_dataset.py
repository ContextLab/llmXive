"""
Final Paired Dataset Assembly (T047)

Merges 2D agent results (aggregated across runs) and 3D baseline results
into a single canonical CSV file: results/analysis/final_paired_dataset.csv

Schema:
task_id, task_type, 2d_success_rate, 2d_mean_latency, 3d_success, 3d_latency, success_diff, latency_diff
"""
import os
import json
import csv
import logging
import argparse
from typing import Dict, List, Any, Optional, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('results/analysis/assemble_paired_dataset.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_yaml_config_simple(config_path: str) -> Dict[str, Any]:
    """Load a simple YAML config file (key: value format) without external deps."""
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
    except Exception as e:
        logger.warning(f"Could not load config {config_path}: {e}. Using defaults.")
    return config

def load_baseline_results(baseline_dir: str) -> Dict[str, Dict[str, Any]]:
    """
    Load 3D baseline results from results/logs/baseline_run.json or similar.
    Expected schema: {task_id: {success: bool, latency_ms: float, task_type: str}}
    """
    baseline_file = os.path.join(baseline_dir, 'baseline_run.json')
    results = {}

    if not os.path.exists(baseline_file):
        # Try alternative location
        baseline_file = os.path.join(baseline_dir, '3d_baseline_results.json')
        if not os.path.exists(baseline_file):
            raise FileNotFoundError(f"Baseline results file not found: {baseline_dir}/baseline_run.json")

    try:
        with open(baseline_file, 'r') as f:
            data = json.load(f)

        # Handle both list and dict formats
        if isinstance(data, list):
            for item in data:
                task_id = item.get('task_id')
                if task_id:
                    results[task_id] = {
                        'success': item.get('success', False),
                        'latency_ms': item.get('latency_ms', 0.0),
                        'task_type': item.get('task_type', 'unknown')
                    }
        elif isinstance(data, dict):
            # If it's already keyed by task_id
            for task_id, item in data.items():
                results[task_id] = {
                    'success': item.get('success', False),
                    'latency_ms': item.get('latency_ms', 0.0),
                    'task_type': item.get('task_type', 'unknown')
                }
    except Exception as e:
        logger.error(f"Error loading baseline results: {e}")
        raise

    logger.info(f"Loaded {len(results)} baseline results")
    return results

def load_2d_run_results(run_id: int) -> Dict[str, Dict[str, Any]]:
    """
    Load all 2D agent run results from results/runs/run_{run_id}.json files.
    Returns a dict: task_id -> list of run results
    """
    results = {}

    if not os.path.exists(runs_dir):
        raise FileNotFoundError(f"2D runs directory not found: {runs_dir}")

    run_files = sorted([f for f in os.listdir(runs_dir) if f.startswith('run_') and f.endswith('.json')])

    if not run_files:
        raise FileNotFoundError(f"No run files found in {runs_dir}")

    logger.info(f"Found {len(run_files)} run files")

    for run_file in run_files:
        file_path = os.path.join(runs_dir, run_file)
        try:
            with open(file_path, 'r') as f:
                run_data = json.load(f)

            # Handle list of task results
            if isinstance(run_data, list):
                for item in run_data:
                    task_id = item.get('task_id')
                    if task_id:
                        if task_id not in results:
                            results[task_id] = []
                        results[task_id].append({
                            'success_flag': item.get('success_flag', False),
                            'latency_ms': item.get('latency_ms', 0.0),
                            'task_type': item.get('task_type', 'unknown')
                        })
            elif isinstance(run_data, dict):
                # If keyed by task_id
                for task_id, item in run_data.items():
                    if task_id not in results:
                        results[task_id] = []
                    results[task_id].append({
                        'success_flag': item.get('success_flag', False),
                        'latency_ms': item.get('latency_ms', 0.0),
                        'task_type': item.get('task_type', 'unknown')
                    })
        except Exception as e:
            logger.warning(f"Error loading {run_file}: {e}")
            continue

    logger.info(f"Loaded results for {len(results)} unique tasks from 2D runs")
    return results

def aggregate_2d_results(
    run_results: Dict[str, List[Dict[str, Any]]],
    expected_runs: int = 5
) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate 2D results across runs for each task_id.
    Returns: task_id -> {success_rate, mean_latency, task_type}
    """
    # Collect all runs
    all_runs: List[Dict[str, Dict[str, Any]]] = []
    for run_id in range(n_runs):
        run_data = load_2d_run_results(run_id)
        all_runs.append(run_data)
        logger.info(f"Loaded run {run_id}: {len(run_data)} tasks")

    for task_id, runs in run_results.items():
        if not runs:
            continue

        # Calculate success rate (mean of success_flag treated as 0/1)
        success_values = [1.0 if r.get('success_flag', False) else 0.0 for r in runs]
        success_rate = sum(success_values) / len(success_values)

        # Calculate mean latency
        latencies = [r.get('latency_ms', 0.0) for r in runs]
        mean_latency = sum(latencies) / len(latencies)

        # Get task_type (should be consistent across runs)
        task_type = runs[0].get('task_type', 'unknown')

        aggregated[task_id] = {
            'success_rate': success_rate,
            'mean_latency': mean_latency,
            'task_type': task_type,
            'num_runs': len(runs)
        }

    logger.info(f"Aggregated 2D results for {len(aggregated)} tasks")
    return aggregated

def build_paired_dataset(
    baseline_results: Dict[str, Dict[str, Any]],
    aggregated_2d: Dict[str, Dict[str, Any]],
    expected_runs: int = 5
) -> List[Dict[str, Any]]:
    """
    Build the paired dataset by merging 2D and 3D results.
    """
    paired = []
    missing_2d = 0
    missing_3d = 0
    run_count_issues = 0

    # Get all task_ids from both sources
    all_task_ids = set(baseline_results.keys()) | set(aggregated_2d.keys())

    for task_id in sorted(all_task_ids):
        baseline = baseline_results.get(task_id)
        d2 = aggregated_2d.get(task_id)

        if not baseline:
            missing_3d += 1
            logger.warning(f"Missing baseline result for task_id: {task_id}")
            continue

        if not d2:
            missing_2d += 1
            logger.warning(f"Missing 2D result for task_id: {task_id}")
            continue

        # Check run count
        if d2.get('num_runs', 0) != expected_runs:
            run_count_issues += 1
            logger.warning(f"Task {task_id} has {d2.get('num_runs')} runs (expected {expected_runs})")

        # Build row
        row = {
            'task_id': task_id,
            'task_type': d2.get('task_type', baseline.get('task_type', 'unknown')),
            '2d_success_rate': d2['success_rate'],
            '2d_mean_latency': d2['mean_latency'],
            '3d_success': 1.0 if baseline.get('success', False) else 0.0,
            '3d_latency': baseline.get('latency_ms', 0.0),
            'success_diff': d2['success_rate'] - (1.0 if baseline.get('success', False) else 0.0),
            'latency_diff': d2['mean_latency'] - baseline.get('latency_ms', 0.0)
        }
        paired.append(row)

    logger.info(f"Built paired dataset with {len(paired)} rows")
    logger.info(f"Missing 2D: {missing_2d}, Missing 3D: {missing_3d}, Run count issues: {run_count_issues}")

    # Sort by task_id
    paired.sort(key=lambda x: x['task_id'])

    return paired

def write_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """Write the paired dataset to a CSV file."""
    if not data:
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

    logger.info(f"Wrote {len(data)} rows to {output_path}")

def verify_no_nulls(data: List[Dict[str, Any]], critical_columns: List[str]) -> bool:
    """Verify that no critical columns contain null/None values."""
    has_nulls = False
    for i, row in enumerate(data):
        for col in critical_columns:
            if row.get(col) is None:
                logger.error(f"Null value found in row {i}, column '{col}'")
                has_nulls = True

    if has_nulls:
        logger.error("Verification FAILED: Null values found in critical columns")
        return False

    logger.info("Verification PASSED: No null values in critical columns")
    return True

def main():
    """Main entry point for T047."""
    parser = argparse.ArgumentParser(description='Assemble final paired dataset')
    parser.add_argument('--config', type=str, default='data/power_config.yaml',
                      help='Path to power config')
    parser.add_argument('--baseline-dir', type=str, default='results/logs',
                      help='Directory containing baseline results')
    parser.add_argument('--runs-dir', type=str, default='results/runs',
                      help='Directory containing 2D run results')
    parser.add_argument('--output', type=str, default='results/analysis/final_paired_dataset.csv',
                      help='Output CSV path')
    parser.add_argument('--expected-runs', type=int, default=5,
                      help='Expected number of runs per task')

    args = parser.parse_args()

    try:
        # Load config to get expected runs
        config = load_yaml_config_simple(args.config)
        expected_runs = config.get('n_runs', args.expected_runs)

        logger.info(f"Starting paired dataset assembly (expected runs: {expected_runs})")

        # Load results
        baseline_results = load_baseline_results(args.baseline_dir)
        run_results = load_2d_run_results(args.runs_dir)

        # Aggregate 2D results
        aggregated_2d = aggregate_2d_results(run_results, expected_runs)

        # Build paired dataset
        paired_data = build_paired_dataset(baseline_results, aggregated_2d, expected_runs)

        if not paired_data:
            raise ValueError("No paired data could be assembled")

        # Verify no nulls
        critical_cols = ['task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
                       '3d_success', '3d_latency', 'success_diff', 'latency_diff']
        if not verify_no_nulls(paired_data, critical_cols):
            raise ValueError("Null values found in critical columns")

        # Write output
        write_csv(paired_data, args.output)

        logger.info("T047 completed successfully")
        return 0

    except Exception as e:
        logger.error(f"T047 failed: {e}")
        raise

if __name__ == '__main__':
    exit(main())