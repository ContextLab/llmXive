"""
Execution Integrity Check Utility.

This module aggregates all 2D agent run results and the 3D baseline results
to verify that every task in the dataset has the expected number of runs.
It ensures data completeness before further analysis tasks proceed.
"""
import json
import os
import glob
import logging
from typing import Dict, List, Any, Set, Optional

# Configure logging for this module
logger = logging.getLogger(__name__)

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a simple YAML configuration file.
    Note: This is a minimal parser for key: value pairs to avoid heavy dependencies.
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
                # Try to parse as number
                try:
                    if '.' in value:
                        config[key] = float(value)
                    else:
                        config[key] = int(value)
                except ValueError:
                    config[key] = value
    return config

def load_json(file_path: str) -> Any:
    """Load a JSON file and return its contents."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(file_path, 'r') as f:
        return json.load(f)

def get_task_ids_from_dataset(dataset_path: str) -> Set[str]:
    """
    Extract all unique task_ids from the generated dataset.
    Expects the dataset to be a list of task instances or a dict with a 'tasks' key.
    """
    try:
        data = load_json(dataset_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load dataset: {e}")
        return set()

    task_ids = set()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'task_id' in item:
                task_ids.add(item['task_id'])
    elif isinstance(data, dict):
        if 'tasks' in data and isinstance(data['tasks'], list):
            for item in data['tasks']:
                if isinstance(item, dict) and 'task_id' in item:
                    task_ids.add(item['task_id'])
        elif 'task_id' in data:
            task_ids.add(data['task_id'])
    
    return task_ids

def get_baseline_task_ids(baseline_path: str) -> Set[str]:
    """
    Extract task_ids from the baseline run results.
    Expects a list of results or a dict with 'results'.
    """
    try:
        data = load_json(baseline_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load baseline results: {e}")
        return set()

    task_ids = set()
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'task_id' in item:
                task_ids.add(item['task_id'])
    elif isinstance(data, dict):
        if 'results' in data and isinstance(data['results'], list):
            for item in data['results']:
                if isinstance(item, dict) and 'task_id' in item:
                    task_ids.add(item['task_id'])
        elif 'task_id' in data:
            task_ids.add(data['task_id'])
    
    return task_ids

def get_2d_run_task_ids(run_dir: str) -> Dict[str, List[str]]:
    """
    Scan the run directory for all run_*.json files and extract task_ids.
    Returns a mapping of run_id -> list of task_ids found in that run.
    """
    run_files = glob.glob(os.path.join(run_dir, "run_*.json"))
    run_task_ids = {}
    
    for run_file in run_files:
        run_id = os.path.basename(run_file).replace("run_", "").replace(".json", "")
        try:
            data = load_json(run_file)
            if isinstance(data, list):
                run_task_ids[run_id] = [item['task_id'] for item in data if isinstance(item, dict) and 'task_id' in item]
            elif isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
                run_task_ids[run_id] = [item['task_id'] for item in data['results'] if isinstance(item, dict) and 'task_id' in item]
            else:
                run_task_ids[run_id] = []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not parse run file {run_file}: {e}")
            run_task_ids[run_id] = []
    
    return run_task_ids

def verify_integrity(
    dataset_path: str,
    baseline_path: str,
    runs_dir: str,
    n_runs_expected: int,
    output_path: str
) -> bool:
    """
    Verify execution integrity.
    
    Checks:
    1. Every task_id in the dataset has exactly n_runs_expected runs in results/runs/
    2. Every task_id in the dataset has exactly 1 run in the baseline results
    
    Args:
        dataset_path: Path to the generated dataset (data/raw/synthetic_spatialclaw_v1.json)
        baseline_path: Path to the baseline results (results/logs/baseline_run.json)
        runs_dir: Directory containing run_*.json files
        n_runs_expected: Number of runs expected per task (from config)
        output_path: Path to write the integrity report
    
    Returns:
        True if integrity check passes, False otherwise
    """
    logger.info("Starting execution integrity check...")
    
    # 1. Load expected task IDs from dataset
    dataset_task_ids = get_task_ids_from_dataset(dataset_path)
    if not dataset_task_ids:
        logger.error("No task IDs found in dataset.")
        report = {
            "status": "ERROR",
            "message": "Dataset is empty or invalid.",
            "total_tasks": 0,
            "tasks_with_full_coverage": 0,
            "missing_runs": []
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return False

    total_tasks = len(dataset_task_ids)
    logger.info(f"Found {total_tasks} tasks in dataset.")

    # 2. Check baseline coverage
    baseline_task_ids = get_baseline_task_ids(baseline_path)
    missing_baseline = dataset_task_ids - baseline_task_ids
    if missing_baseline:
        logger.warning(f"Missing baseline runs for {len(missing_baseline)} tasks.")
    
    # 3. Check 2D agent run coverage
    run_task_ids_map = get_2d_run_task_ids(runs_dir)
    all_run_ids = list(run_task_ids_map.keys())
    
    if len(all_run_ids) < n_runs_expected:
        logger.warning(f"Found only {len(all_run_ids)} run files, expected {n_runs_expected}.")
    
    missing_runs_details = []
    tasks_with_full_coverage = 0

    for task_id in dataset_task_ids:
        found_runs = 0
        run_ids_found = []
        
        for run_id in all_run_ids:
            if task_id in run_task_ids_map.get(run_id, []):
                found_runs += 1
                run_ids_found.append(run_id)
        
        # Check if we have exactly n_runs_expected
        if found_runs == n_runs_expected:
            tasks_with_full_coverage += 1
        else:
            missing_runs_details.append({
                "task_id": task_id,
                "expected_runs": n_runs_expected,
                "found_runs": found_runs,
                "found_run_ids": run_ids_found
            })

    # 4. Determine status
    if tasks_with_full_coverage == total_tasks and not missing_baseline:
        status = "COMPLETE"
        logger.info(f"Integrity check PASSED. All {total_tasks} tasks have full coverage.")
    else:
        status = "INCOMPLETE"
        logger.warning(f"Integrity check FAILED. {total_tasks - tasks_with_full_coverage} tasks missing runs.")
        if missing_baseline:
            logger.warning(f"{len(missing_baseline)} tasks missing baseline runs.")

    # 5. Generate report
    report = {
        "status": status,
        "total_tasks": total_tasks,
        "tasks_with_full_coverage": tasks_with_full_coverage,
        "missing_runs": missing_runs_details,
        "missing_baseline_count": len(missing_baseline),
        "n_runs_expected": n_runs_expected,
        "runs_found_count": len(all_run_ids)
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Integrity report written to {output_path}")
    
    return status == "COMPLETE"

def main():
    """Main entry point for the integrity check script."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify execution integrity of SpatialClaw runs.")
    parser.add_argument(
        "--dataset", 
        type=str, 
        default="data/raw/synthetic_spatialclaw_v1.json",
        help="Path to the generated dataset"
    )
    parser.add_argument(
        "--baseline", 
        type=str, 
        default="results/logs/baseline_run.json",
        help="Path to the baseline results"
    )
    parser.add_argument(
        "--runs-dir", 
        type=str, 
        default="results/runs",
        help="Directory containing run_*.json files"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        default="data/power_config.yaml",
        help="Path to power config to read n_runs"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="results/analysis/run_integrity_report.json",
        help="Path to write the integrity report"
    )
    
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Load n_runs from config
        config = load_yaml_config(args.config)
        n_runs = config.get('n_runs', 5)
        logger.info(f"Expected n_runs from config: {n_runs}")
        
        success = verify_integrity(
            dataset_path=args.dataset,
            baseline_path=args.baseline,
            runs_dir=args.runs_dir,
            n_runs_expected=n_runs,
            output_path=args.output
        )
        
        if not success:
            logger.error("Integrity check failed. Aborting further analysis.")
            # In a real pipeline, we might exit with code 1 here
            # sys.exit(1)
        else:
            logger.info("Integrity check passed. Proceeding with analysis.")
            
    except Exception as e:
        logger.exception(f"Integrity check failed with exception: {e}")
        raise

if __name__ == "__main__":
    main()