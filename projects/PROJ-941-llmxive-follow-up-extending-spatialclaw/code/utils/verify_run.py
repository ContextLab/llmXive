"""
Execution Integrity Check Module (T046).

Verifies that the full experiment run produced the expected number of
results for every task instance.

Requirements:
- Every task_id in the dataset must have exactly n_runs (from config)
  results in results/runs/run_*.json (2D agent).
- Every task_id must have exactly 1 result in results/logs/baseline_run.json.
- Output: results/analysis/run_integrity_report.json with status, counts,
  and list of missing runs.
"""

import json
import os
import glob
import logging
import argparse
from typing import Dict, List, Any, Set, Optional

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("verify_run")


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a simple YAML config file.
    We use a minimal parser here to avoid adding pyyaml dependency if not needed,
    or we can assume standard key: value format.
    """
    config = {}
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Try to convert to int or float if possible
                try:
                    if '.' in value:
                        config[key] = float(value)
                    else:
                        config[key] = int(value)
                except ValueError:
                    config[key] = value
    return config


def load_json(file_path: str) -> Any:
    """Load a JSON file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)


def get_task_ids_from_dataset(dataset_path: str) -> Set[str]:
    """
    Extract all unique task_ids from the generated dataset JSON.
    The dataset is expected to be a list of task instances.
    """
    logger.info(f"Loading dataset from {dataset_path} to extract task IDs...")
    try:
        data = load_json(dataset_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    if not isinstance(data, list):
        raise ValueError(f"Dataset at {dataset_path} must be a JSON list.")

    task_ids = set()
    for item in data:
        if isinstance(item, dict) and 'task_id' in item:
            task_ids.add(item['task_id'])
        elif isinstance(item, dict) and 'id' in item:
             # Fallback if schema uses 'id' instead of 'task_id'
            task_ids.add(item['id'])
    
    logger.info(f"Found {len(task_ids)} unique task IDs in dataset.")
    return task_ids


def get_baseline_task_ids(baseline_results_path: str) -> Dict[str, Dict]:
    """
    Load baseline results and return a mapping of task_id -> result.
    Expected format: A list of results or a dict keyed by task_id.
    We assume the output of T023b is a list of dicts with 'task_id'.
    """
    logger.info(f"Loading baseline results from {baseline_results_path}...")
    try:
        data = load_json(baseline_results_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load baseline results: {e}")
        raise

    baseline_map = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'task_id' in item:
                baseline_map[item['task_id']] = item
            elif isinstance(item, dict) and 'id' in item:
                baseline_map[item['id']] = item
    elif isinstance(data, dict):
        # If it's already a dict keyed by task_id
        baseline_map = data
    else:
        raise ValueError(f"Baseline results at {baseline_results_path} must be a list or dict.")

    logger.info(f"Found {len(baseline_map)} baseline results.")
    return baseline_map


def get_2d_run_task_ids(run_dir: str) -> Dict[str, List[str]]:
    """
    Scan results/runs/ for all run_*.json files.
    Return a mapping of task_id -> list of run_ids (or file paths).
    We assume each file contains a list of results or a single result dict.
    Actually, T017b saves `results/runs/run_{run_id}.json`.
    The structure of these files needs to be inferred.
    Based on T017b description: "save results to results/runs/run_{run_id}.json".
    Let's assume each file is a list of results for all tasks in that run.
    """
    logger.info(f"Scanning 2D run directory: {run_dir}...")
    if not os.path.exists(run_dir):
        logger.warning(f"Run directory {run_dir} does not exist.")
        return {}

    pattern = os.path.join(run_dir, "run_*.json")
    files = glob.glob(pattern)
    
    task_runs_map: Dict[str, List[str]] = {}
    
    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Data is expected to be a list of task results
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'task_id' in item:
                        tid = item['task_id']
                        if tid not in task_runs_map:
                            task_runs_map[tid] = []
                        task_runs_map[tid].append(os.path.basename(file_path))
                    elif isinstance(item, dict) and 'id' in item:
                        tid = item['id']
                        if tid not in task_runs_map:
                            task_runs_map[tid] = []
                        task_runs_map[tid].append(os.path.basename(file_path))
            elif isinstance(data, dict):
                # If the file contains a single result keyed by task_id
                for tid, _ in data.items():
                    if tid not in task_runs_map:
                        task_runs_map[tid] = []
                    task_runs_map[tid].append(os.path.basename(file_path))
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            continue

    logger.info(f"Aggregated 2D runs for {len(task_runs_map)} task IDs.")
    return task_runs_map


def verify_integrity(
    dataset_path: str,
    baseline_path: str,
    runs_dir: str,
    config_path: str,
    output_path: str
) -> bool:
    """
    Main verification logic.
    Returns True if integrity check passes, False otherwise.
    """
    logger.info("Starting execution integrity check...")
    
    # 1. Load config to get n_runs
    try:
        config = load_yaml_config(config_path)
        n_runs = config.get('n_runs', 5)
        logger.info(f"Expected n_runs from config: {n_runs}")
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        # Fallback to default if config is missing/unreadable but we proceed with caution
        n_runs = 5
        logger.warning(f"Using default n_runs={n_runs}")

    # 2. Get task IDs from dataset
    try:
        expected_task_ids = get_task_ids_from_dataset(dataset_path)
    except Exception as e:
        logger.error(f"Cannot proceed: {e}")
        return False

    # 3. Check baseline results
    try:
        baseline_map = get_baseline_task_ids(baseline_path)
    except Exception as e:
        logger.error(f"Cannot proceed: {e}")
        return False

    missing_baseline = expected_task_ids - set(baseline_map.keys())
    if missing_baseline:
        logger.warning(f"Missing baseline results for {len(missing_baseline)} tasks.")
    else:
        logger.info("Baseline results cover all tasks.")

    # 4. Check 2D run results
    task_runs_map = get_2d_run_task_ids(runs_dir)
    missing_2d = expected_task_ids - set(task_runs_map.keys())
    if missing_2d:
        logger.warning(f"Missing 2D run files for {len(missing_2d)} tasks.")
    else:
        logger.info("2D run files exist for all tasks.")

    # 5. Verify run counts
    incomplete_tasks = []
    for tid in expected_task_ids:
        baseline_ok = tid in baseline_map
        runs_ok = tid in task_runs_map and len(task_runs_map[tid]) == n_runs
        
        if not (baseline_ok and runs_ok):
            incomplete_tasks.append({
                "task_id": tid,
                "baseline_present": baseline_ok,
                "runs_found": len(task_runs_map.get(tid, [])),
                "runs_expected": n_runs,
                "status": "INCOMPLETE"
            })
    
    total_tasks = len(expected_task_ids)
    tasks_with_full_coverage = total_tasks - len(incomplete_tasks)
    status = "COMPLETE" if len(incomplete_tasks) == 0 else "INCOMPLETE"

    # 6. Prepare report
    report = {
        "status": status,
        "total_tasks": total_tasks,
        "tasks_with_full_coverage": tasks_with_full_coverage,
        "missing_runs": incomplete_tasks,
        "config": {
            "n_runs_expected": n_runs
        },
        "paths": {
            "dataset": dataset_path,
            "baseline": baseline_path,
            "runs_dir": runs_dir,
            "config": config_path,
            "output": output_path
        }
    }

    # 7. Write report
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Integrity report written to {output_path}")
    logger.info(f"Status: {status}, Coverage: {tasks_with_full_coverage}/{total_tasks}")

    return status == "COMPLETE"


def main():
    parser = argparse.ArgumentParser(description="Verify execution integrity of the SpatialClaw experiment.")
    parser.add_argument("--dataset", type=str, default="data/raw/synthetic_spatialclaw_v1.json",
                      help="Path to the generated dataset JSON.")
    parser.add_argument("--baseline", type=str, default="results/logs/baseline_run.json",
                      help="Path to the baseline results JSON.")
    parser.add_argument("--runs-dir", type=str, default="results/runs",
                      help="Directory containing 2D agent run JSON files.")
    parser.add_argument("--config", type=str, default="data/power_config.yaml",
                      help="Path to power config YAML.")
    parser.add_argument("--output", type=str, default="results/analysis/run_integrity_report.json",
                      help="Path to write the integrity report.")
    
    args = parser.parse_args()
    
    success = verify_integrity(
        dataset_path=args.dataset,
        baseline_path=args.baseline,
        runs_dir=args.runs_dir,
        config_path=args.config,
        output_path=args.output
    )
    
    if not success:
        logger.error("Integrity check FAILED. Further analysis tasks should be aborted.")
        return 1
    else:
        logger.info("Integrity check PASSED.")
        return 0


if __name__ == "__main__":
    exit(main())
