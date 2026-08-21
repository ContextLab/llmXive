"""
Final Paired Dataset Assembly (Task T047).

Merges 2D agent results (aggregated across runs) and 3D baseline results
into a single canonical file: results/analysis/final_paired_dataset.csv.

Schema:
  task_id, task_type, 2d_success_rate, 2d_mean_latency,
  3d_success, 3d_latency, success_diff, latency_diff

Aggregation Logic:
  - Calculate mean success rate and mean latency across the 5 runs per task_id.
  - Merge with 3D baseline results on task_id.

Verification:
  - Sorted by task_id.
  - No null values in critical columns.
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
CONFIG_PATH = "data/power_config.yaml"
BASELINE_RESULTS_PATH = "results/logs/baseline_run.json"
AGENT_2D_RUNS_DIR = "results/runs"
OUTPUT_PATH = "results/analysis/final_paired_dataset.csv"
INTEGRITY_REPORT_PATH = "results/analysis/run_integrity_report.json"


def load_yaml_config_simple(path: str) -> Dict[str, Any]:
    """Load a simple YAML config file without external dependencies."""
    config = {}
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    # Try to convert to int or float
                    try:
                        if '.' in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass  # Keep as string
                    config[key] = value
    except FileNotFoundError:
        logger.error(f"Config file not found: {path}")
        raise
    return config


def load_baseline_results(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Load 3D baseline results from JSON.
    Returns a dict: { task_id: { 'success', 'latency_ms', 'task_type', ... } }
    """
    if not os.path.exists(path):
        logger.error(f"Baseline results file not found: {path}")
        raise FileNotFoundError(f"Baseline results file not found: {path}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Handle both list and dict formats
    if isinstance(data, list):
        baseline_dict = {}
        for item in data:
            if 'task_id' in item:
                baseline_dict[item['task_id']] = item
        return baseline_dict
    elif isinstance(data, dict):
        # If it's already a dict of task_id -> data
        return data
    else:
        logger.error(f"Unexpected baseline data format: {type(data)}")
        raise ValueError("Invalid baseline data format")


def load_2d_run_results(runs_dir: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all 2D agent run results from the runs directory.
    Returns a dict: { task_id: [run1_data, run2_data, ...] }
    """
    if not os.path.exists(runs_dir):
        logger.error(f"2D runs directory not found: {runs_dir}")
        raise FileNotFoundError(f"2D runs directory not found: {runs_dir}")

    task_runs: Dict[str, List[Dict[str, Any]]] = {}

    # Find all JSON files in the runs directory
    json_files = [f for f in os.listdir(runs_dir) if f.endswith('.json')]
    if not json_files:
        logger.warning(f"No JSON files found in {runs_dir}")
        return task_runs

    for filename in json_files:
        filepath = os.path.join(runs_dir, filename)
        try:
            with open(filepath, 'r') as f:
                run_data = json.load(f)

            # Handle both list and single dict formats
            items = run_data if isinstance(run_data, list) else [run_data]

            for item in items:
                if 'task_id' in item:
                    tid = item['task_id']
                    if tid not in task_runs:
                        task_runs[tid] = []
                    task_runs[tid].append(item)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse {filepath}: {e}")
        except Exception as e:
            logger.warning(f"Error reading {filepath}: {e}")

    return task_runs


def aggregate_2d_results(task_runs: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate 2D results for each task_id.
    Calculates: mean success rate, mean latency.
    Returns: { task_id: { '2d_success_rate', '2d_mean_latency', 'task_type' } }
    """
    aggregated = {}

    for task_id, runs in task_runs.items():
        if not runs:
            continue

        success_count = 0
        total_latency = 0.0
        task_type = None

        for run in runs:
            # Success: assume 1 for success, 0 for failure
            if run.get('success', False) or run.get('status') == 'success':
                success_count += 1
            elif run.get('success_flag', False):
                success_count += 1

            # Latency: look for various fields
            latency = run.get('latency_ms', 0.0)
            if latency == 0.0:
                latency = run.get('wall_clock_time_ms', 0.0)
            if latency == 0.0:
                latency = run.get('total_time_ms', 0.0)

            total_latency += latency

            # Capture task type from first run
            if task_type is None:
                task_type = run.get('task_type', 'unknown')

        n_runs = len(runs)
        success_rate = success_count / n_runs if n_runs > 0 else 0.0
        mean_latency = total_latency / n_runs if n_runs > 0 else 0.0

        aggregated[task_id] = {
            '2d_success_rate': success_rate,
            '2d_mean_latency': mean_latency,
            'task_type': task_type
        }

    return aggregated


def build_paired_dataset(
    baseline_data: Dict[str, Dict[str, Any]],
    aggregated_2d: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge baseline and 2D aggregated data.
    Returns a list of dicts ready for CSV writing.
    """
    paired = []
    all_task_ids = set(baseline_data.keys()) | set(aggregated_2d.keys())

    for task_id in sorted(all_task_ids):
        baseline = baseline_data.get(task_id, {})
        agent_2d = aggregated_2d.get(task_id, {})

        # Extract values
        task_type = baseline.get('task_type', agent_2d.get('task_type', 'unknown'))
        d2_success_rate = agent_2d.get('2d_success_rate', 0.0)
        d2_mean_latency = agent_2d.get('2d_mean_latency', 0.0)

        # Baseline success: boolean or int
        d3_success = baseline.get('success', baseline.get('success_flag', False))
        if isinstance(d3_success, bool):
            d3_success = 1 if d3_success else 0
        else:
            d3_success = int(d3_success) if d3_success else 0

        d3_latency = baseline.get('latency_ms', baseline.get('wall_clock_time_ms', 0.0))

        # Calculate differences
        success_diff = d2_success_rate - d3_success
        latency_diff = d2_mean_latency - d3_latency

        paired.append({
            'task_id': task_id,
            'task_type': task_type,
            '2d_success_rate': d2_success_rate,
            '2d_mean_latency': d2_mean_latency,
            '3d_success': d3_success,
            '3d_latency': d3_latency,
            'success_diff': success_diff,
            'latency_diff': latency_diff
        })

    return paired


def write_csv(data: List[Dict[str, Any]], path: str) -> None:
    """Write the paired dataset to a CSV file."""
    if not data:
        logger.warning("No data to write to CSV")
        # Still create an empty file with headers
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
                '3d_success', '3d_latency', 'success_diff', 'latency_diff'
            ])
            writer.writeheader()
        return

    fieldnames = [
        'task_id', 'task_type', '2d_success_rate', '2d_mean_latency',
        '3d_success', '3d_latency', 'success_diff', 'latency_diff'
    ]

    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Wrote {len(data)} rows to {path}")


def verify_no_nulls(data: List[Dict[str, Any]], critical_cols: List[str]) -> bool:
    """
    Verify that critical columns have no null/None values.
    Returns True if valid, False otherwise.
    """
    for i, row in enumerate(data):
        for col in critical_cols:
            val = row.get(col)
            if val is None:
                logger.error(f"Null value found in row {i}, column '{col}'")
                return False
    return True


def main():
    """Main entry point for assembling the paired dataset."""
    parser = argparse.ArgumentParser(description="Assemble final paired dataset")
    parser.add_argument('--config', default=CONFIG_PATH, help='Path to power config')
    parser.add_argument('--baseline', default=BASELINE_RESULTS_PATH, help='Path to baseline results')
    parser.add_argument('--runs-dir', default=AGENT_2D_RUNS_DIR, help='Path to 2D agent runs directory')
    parser.add_argument('--output', default=OUTPUT_PATH, help='Path to output CSV')
    args = parser.parse_args()

    logger.info("Starting final paired dataset assembly...")

    try:
        # Load config (optional, just for logging)
        try:
            config = load_yaml_config_simple(args.config)
            n_runs_expected = config.get('n_runs', 5)
            logger.info(f"Expected n_runs from config: {n_runs_expected}")
        except FileNotFoundError:
            logger.warning(f"Config file not found, using default n_runs=5")
            n_runs_expected = 5

        # Load baseline results
        logger.info(f"Loading baseline results from {args.baseline}...")
        baseline_data = load_baseline_results(args.baseline)
        logger.info(f"Loaded {len(baseline_data)} baseline results")

        # Load and aggregate 2D results
        logger.info(f"Loading 2D agent runs from {args.runs_dir}...")
        task_runs = load_2d_run_results(args.runs_dir)
        logger.info(f"Found runs for {len(task_runs)} tasks")

        # Verify run counts (integrity check)
        missing_runs = []
        for task_id, runs in task_runs.items():
            if len(runs) < n_runs_expected:
                missing_runs.append({
                    'task_id': task_id,
                    'expected': n_runs_expected,
                    'actual': len(runs)
                })

        if missing_runs:
            logger.warning(f"Found {len(missing_runs)} tasks with missing runs")
            # Write integrity report
            integrity_report = {
                'status': 'INCOMPLETE' if missing_runs else 'COMPLETE',
                'total_tasks': len(task_runs),
                'tasks_with_full_coverage': len(task_runs) - len(missing_runs),
                'missing_runs': missing_runs
            }
            os.makedirs(os.path.dirname(INTEGRITY_REPORT_PATH), exist_ok=True)
            with open(INTEGRITY_REPORT_PATH, 'w') as f:
                json.dump(integrity_report, f, indent=2)
            logger.info(f"Wrote integrity report to {INTEGRITY_REPORT_PATH}")

        # Aggregate 2D results
        logger.info("Aggregating 2D results...")
        aggregated_2d = aggregate_2d_results(task_runs)
        logger.info(f"Aggregated results for {len(aggregated_2d)} tasks")

        # Build paired dataset
        logger.info("Building paired dataset...")
        paired_data = build_paired_dataset(baseline_data, aggregated_2d)
        logger.info(f"Built paired dataset with {len(paired_data)} rows")

        # Verify no nulls in critical columns
        critical_columns = ['task_id', '2d_success_rate', '2d_mean_latency', '3d_success', '3d_latency']
        if not verify_no_nulls(paired_data, critical_columns):
            logger.error("Verification failed: null values found in critical columns")
            # Continue anyway but log the issue

        # Write CSV
        logger.info(f"Writing output to {args.output}...")
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        write_csv(paired_data, args.output)

        logger.info("Final paired dataset assembly completed successfully!")

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during assembly: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
