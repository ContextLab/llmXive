"""
Execution Integrity Check for SpatialClaw Benchmark.

This module verifies that the full pipeline execution (T052_exec) produced
the expected number of runs for every task instance.

Requirements:
- Every task_id in the dataset must have exactly `n_runs` (from config, default 5)
  runs in the 2D agent results directory (results/runs/).
- Every task_id must have exactly 1 run in the baseline results file
  (results/logs/baseline_run.json).

Output:
- results/analysis/run_integrity_report.json
"""

import json
import os
import sys
import logging
import argparse
from typing import Dict, List, Any, Optional, Set
from glob import glob

# Add project root to path for imports if running as script
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.logging import setup_logging
from stats.power_analysis import load_power_config

# Constants
CONFIG_PATH = "data/power_config.yaml"
DATASET_PATH = "data/raw/synthetic_spatialclaw_v1.json"
RUNS_DIR = "results/runs"
BASELINE_LOG = "results/logs/baseline_run.json"
OUTPUT_PATH = "results/analysis/run_integrity_report.json"
DEFAULT_N_RUNS = 5

logger = logging.getLogger(__name__)

def load_json_file(path: str) -> Any:
    """Load a JSON file safely."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_task_ids_from_dataset(dataset_path: str) -> Set[str]:
    """Extract unique task_ids from the generated dataset."""
    logger.info(f"Loading dataset from {dataset_path} to identify task IDs...")
    try:
        data = load_json_file(dataset_path)
        # Handle both list and dict with 'tasks' key
        if isinstance(data, list):
            tasks = data
        elif isinstance(data, dict) and 'tasks' in data:
            tasks = data['tasks']
        else:
            # Fallback: assume root is tasks
            tasks = [data] if isinstance(data, dict) else []

        task_ids = set()
        for task in tasks:
            if isinstance(task, dict) and 'task_id' in task:
                task_ids.add(task['task_id'])
            elif isinstance(task, str):
                # If the file is just a list of IDs
                task_ids.add(task)

        if not task_ids:
            raise ValueError("No task_ids found in the dataset file.")

        logger.info(f"Found {len(task_ids)} unique task IDs in dataset.")
        return task_ids
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def get_2d_run_counts(runs_dir: str, task_ids: Set[str]) -> Dict[str, int]:
    """
    Count the number of run files per task_id in results/runs/.
    Expected files: run_{run_id}.json (where run_id is usually an index or UUID)
    We assume the JSON content contains the 'task_id' it belongs to.
    """
    counts = {tid: 0 for tid in task_ids}
    run_files = glob(os.path.join(runs_dir, "run_*.json"))

    if not run_files:
        logger.warning(f"No run files found in {runs_dir}")
        return counts

    logger.info(f"Scanning {len(run_files)} run files in {runs_dir}...")

    for file_path in run_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Handle list of results or single result object
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and 'task_id' in item:
                        tid = item['task_id']
                        if tid in counts:
                            counts[tid] += 1
            elif isinstance(content, dict) and 'task_id' in content:
                tid = content['task_id']
                if tid in counts:
                    counts[tid] += 1
        except json.JSONDecodeError:
            logger.warning(f"Skipping invalid JSON file: {file_path}")
        except Exception as e:
            logger.warning(f"Error processing {file_path}: {e}")

    return counts

def get_baseline_task_ids(baseline_path: str) -> Set[str]:
    """
    Extract task_ids covered by the baseline run.
    Expected format: List of task results or a dict with 'tasks' key.
    """
    if not os.path.exists(baseline_path):
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}")

    logger.info(f"Loading baseline results from {baseline_path}...")
    try:
        data = load_json_file(baseline_path)
        
        if isinstance(data, list):
            tasks = data
        elif isinstance(data, dict) and 'tasks' in data:
            tasks = data['tasks']
        elif isinstance(data, dict) and 'results' in data:
            tasks = data['results']
        else:
            tasks = [data] if isinstance(data, dict) else []

        baseline_ids = set()
        for task in tasks:
            if isinstance(task, dict) and 'task_id' in task:
                baseline_ids.add(task['task_id'])
            elif isinstance(task, str):
                baseline_ids.add(task)

        logger.info(f"Baseline covers {len(baseline_ids)} tasks.")
        return baseline_ids
    except Exception as e:
        logger.error(f"Failed to load baseline: {e}")
        raise

def verify_integrity(
    dataset_path: str,
    runs_dir: str,
    baseline_path: str,
    n_runs_expected: int
) -> Dict[str, Any]:
    """
    Perform the integrity check.
    
    Returns a report dict:
    {
        "total_tasks": int,
        "tasks_with_full_coverage": int,
        "missing_runs": [{"task_id": str, "expected": int, "actual": int}],
        "status": "COMPLETE" | "INCOMPLETE"
    }
    """
    # 1. Get all expected task IDs
    try:
        all_task_ids = get_task_ids_from_dataset(dataset_path)
    except FileNotFoundError as e:
        logger.critical(str(e))
        return {
            "total_tasks": 0,
            "tasks_with_full_coverage": 0,
            "missing_runs": [],
            "status": "INCOMPLETE",
            "error": str(e)
        }

    # 2. Check 2D runs
    try:
        run_counts = get_2d_run_counts(runs_dir, all_task_ids)
    except Exception as e:
        logger.critical(f"Failed to scan 2D runs: {e}")
        return {
            "total_tasks": len(all_task_ids),
            "tasks_with_full_coverage": 0,
            "missing_runs": [],
            "status": "INCOMPLETE",
            "error": f"Failed to scan 2D runs: {e}"
        }

    # 3. Check Baseline runs
    try:
        baseline_ids = get_baseline_task_ids(baseline_path)
    except FileNotFoundError as e:
        logger.critical(str(e))
        return {
            "total_tasks": len(all_task_ids),
            "tasks_with_full_coverage": 0,
            "missing_runs": [],
            "status": "INCOMPLETE",
            "error": str(e)
        }

    # 4. Aggregate findings
    missing_runs = []
    full_coverage_count = 0

    for tid in all_task_ids:
        actual_2d = run_counts.get(tid, 0)
        has_baseline = tid in baseline_ids

        if actual_2d == n_runs_expected and has_baseline:
            full_coverage_count += 1
        else:
            reasons = []
            if actual_2d != n_runs_expected:
                reasons.append(f"2D runs: {actual_2d}/{n_runs_expected}")
            if not has_baseline:
                reasons.append("Baseline: 0/1")
            
            missing_runs.append({
                "task_id": tid,
                "expected": n_runs_expected,
                "actual_2d": actual_2d,
                "baseline_present": has_baseline,
                "reasons": reasons
            })

    status = "COMPLETE" if len(missing_runs) == 0 else "INCOMPLETE"

    logger.info(f"Integrity Check: {full_coverage_count}/{len(all_task_ids)} tasks complete.")
    if missing_runs:
        logger.warning(f"Found {len(missing_runs)} tasks with missing runs.")

    return {
        "total_tasks": len(all_task_ids),
        "tasks_with_full_coverage": full_coverage_count,
        "missing_runs": missing_runs,
        "status": status
    }

def write_report(report: Dict[str, Any], output_path: str) -> None:
    """Write the integrity report to disk."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Integrity report written to {output_path}")

def main(args: Optional[argparse.Namespace] = None) -> int:
    """Main entry point."""
    if args is None:
        parser = argparse.ArgumentParser(description="Verify execution integrity.")
        parser.add_argument("--config", default=CONFIG_PATH, help="Path to power config")
        parser.add_argument("--dataset", default=DATASET_PATH, help="Path to dataset")
        parser.add_argument("--runs-dir", default=RUNS_DIR, help="Directory containing run_*.json")
        parser.add_argument("--baseline", default=BASELINE_LOG, help="Path to baseline log")
        parser.add_argument("--output", default=OUTPUT_PATH, help="Output report path")
        parser.add_argument("--log-file", default="results/logs/verify_run.log", help="Log file path")
        args = parser.parse_args()

    setup_logging(log_file=args.log_file)

    try:
        # Load expected n_runs from config
        try:
            config = load_power_config(args.config)
            n_runs = config.get("n_runs", DEFAULT_N_RUNS)
            logger.info(f"Using n_runs={n_runs} from config.")
        except Exception as e:
            logger.warning(f"Could not load config {args.config}: {e}. Using default {DEFAULT_N_RUNS}.")
            n_runs = DEFAULT_N_RUNS

        # Run verification
        report = verify_integrity(
            dataset_path=args.dataset,
            runs_dir=args.runs_dir,
            baseline_path=args.baseline,
            n_runs_expected=n_runs
        )

        # Write report
        write_report(report, args.output)

        # If incomplete, log a clear error message for the pipeline to catch
        if report["status"] == "INCOMPLETE":
            logger.error("INTEGRITY CHECK FAILED: Missing runs detected. Aborting further analysis.")
            return 1
        
        logger.info("INTEGRITY CHECK PASSED: All tasks have full coverage.")
        return 0

    except Exception as e:
        logger.exception(f"Unexpected error during integrity check: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())