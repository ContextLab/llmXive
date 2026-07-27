import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Set, Optional
from utils.logging import get_logger, log_stage_start, log_stage_end

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
DATA_ARTIFACTS = PROJECT_ROOT / "data" / "artifacts"

# Input paths
RULE_ENGINE_RESULTS_PATH = DATA_DERIVED / "results_rule_engine.csv"
BASELINE_RESULTS_PATH = DATA_DERIVED / "baseline_results.json"
MANIFEST_PATH = DATA_DERIVED / "experiment_manifest.csv"

# Output paths
MERGED_RESULTS_PATH = DATA_DERIVED / "results.csv"

logger = get_logger(__name__)


def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the experiment manifest to get the list of expected task IDs."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found at {manifest_path}. Ensure T019a (generate_manifest.py) has completed.")
    
    tasks = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    return tasks


def load_rule_engine_results(results_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load rule engine results from CSV into a dict keyed by task_id."""
    if not results_path.exists():
        raise FileNotFoundError(f"Rule engine results not found at {results_path}.")
    
    results = {}
    with open(results_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row.get('task_id')
            if task_id:
                # Convert numeric strings to appropriate types
                try:
                    row['time_to_pivot'] = float(row['time_to_pivot']) if row['time_to_pivot'] else None
                except ValueError:
                    row['time_to_pivot'] = None
                try:
                    row['success'] = row['success'].lower() == 'true' if row['success'] else False
                except (AttributeError, ValueError):
                    row['success'] = False
                results[task_id] = row
    return results


def load_baseline_results(results_path: Path) -> Dict[str, Dict[str, Any]]:
    """Load baseline results from JSON into a dict keyed by task_id."""
    if not results_path.exists():
        raise FileNotFoundError(f"Baseline results not found at {results_path}.")
    
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and dict formats for baseline results
    if isinstance(data, list):
        results = {item['task_id']: item for item in data}
    elif isinstance(data, dict):
        # If it's a dict where keys are task_ids
        results = data
    else:
        raise ValueError(f"Unexpected baseline results format: {type(data)}")
    
    # Normalize types
    for task_id, row in results.items():
        try:
            row['time_to_pivot'] = float(row['time_to_pivot']) if row.get('time_to_pivot') else None
        except (ValueError, TypeError):
            row['time_to_pivot'] = None
        try:
            row['success'] = str(row['success']).lower() == 'true' if row.get('success') is not None else False
        except (AttributeError, ValueError):
            row['success'] = False
    return results


def merge_results(
    manifest_tasks: List[Dict[str, Any]],
    rule_engine_results: Dict[str, Dict[str, Any]],
    baseline_results: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge rule engine and baseline results based on the manifest.
    
    Logic:
    - Iterate through manifest tasks to ensure strict ID matching.
    - If a task is missing from baseline_results, mark it as 'failed' in the success column.
    - Filter out failed baselines from the 'time_to_pivot' column (set to None) for statistical analysis,
      but retain the 'success' status (False).
    """
    manifest_task_ids = {task['task_id'] for task in manifest_tasks}
    baseline_task_ids = set(baseline_results.keys())
    
    # Validation: Check if all manifest IDs are in baseline results
    missing_in_baseline = manifest_task_ids - baseline_task_ids
    if missing_in_baseline:
        logger.warning(f"Baseline results missing {len(missing_in_baseline)} tasks from manifest: {missing_in_baseline}")
    
    merged = []
    
    for task in manifest_tasks:
        task_id = task['task_id']
        failure_type = task.get('failure_type', 'Unknown')
        
        # Get rule engine data
        re_data = rule_engine_results.get(task_id, {})
        re_time = re_data.get('time_to_pivot')
        re_success = re_data.get('success', False)
        re_method = re_data.get('method', 'rule_engine')
        re_fallback = re_data.get('fallback_chain', 'None')
        
        # Get baseline data
        bl_data = baseline_results.get(task_id)
        
        if bl_data is None:
            # Task missing from baseline (external failure)
            bl_time = None
            bl_success = False
            bl_method = 'baseline'
            # Mark as failed in results
            logger.info(f"Task {task_id} missing from baseline. Marking as failed.")
        else:
            bl_time = bl_data.get('time_to_pivot')
            bl_success = bl_data.get('success', False)
            bl_method = 'baseline'
            
            # Handle Failure Logic:
            # If baseline failed (success is False), set time_to_pivot to None for statistical analysis
            # (to avoid skewing averages with infinite/timeout values), but keep success=False.
            if not bl_success:
                logger.debug(f"Baseline failed for {task_id}. Setting time_to_pivot to None for analysis.")
                bl_time = None

        row = {
            'task_id': task_id,
            'failure_type': failure_type,
            'method': re_method,
            'time_to_pivot': re_time,
            'success': re_success,
            'fallback_chain': re_fallback,
            'baseline_time_to_pivot': bl_time,
            'baseline_success': bl_success
        }
        merged.append(row)
    
    return merged


def write_merged_results(merged_data: List[Dict[str, Any]], output_path: Path):
    """Write the merged results to a CSV file."""
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = [
        'task_id', 'failure_type', 'method', 'time_to_pivot', 'success', 
        'fallback_chain', 'baseline_time_to_pivot', 'baseline_success'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)
    
    logger.info(f"Merged results written to {output_path}")


def main():
    log_stage_start("merge_results")
    
    try:
        # 1. Load Manifest
        logger.info(f"Loading manifest from {MANIFEST_PATH}")
        manifest_tasks = load_manifest(MANIFEST_PATH)
        if not manifest_tasks:
            logger.error("Manifest is empty. Cannot proceed.")
            sys.exit(1)
        logger.info(f"Loaded {len(manifest_tasks)} tasks from manifest.")

        # 2. Load Rule Engine Results
        logger.info(f"Loading rule engine results from {RULE_ENGINE_RESULTS_PATH}")
        rule_engine_results = load_rule_engine_results(RULE_ENGINE_RESULTS_PATH)
        logger.info(f"Loaded {len(rule_engine_results)} rule engine results.")

        # 3. Load Baseline Results
        logger.info(f"Loading baseline results from {BASELINE_RESULTS_PATH}")
        baseline_results = load_baseline_results(BASELINE_RESULTS_PATH)
        logger.info(f"Loaded {len(baseline_results)} baseline results.")

        # 4. Merge
        logger.info("Merging results...")
        merged = merge_results(manifest_tasks, rule_engine_results, baseline_results)

        # 5. Write Output
        logger.info(f"Writing merged results to {MERGED_RESULTS_PATH}")
        write_merged_results(merged, MERGED_RESULTS_PATH)

        # Verification
        if not MERGED_RESULTS_PATH.exists():
            logger.error("Output file was not created.")
            sys.exit(1)
        
        logger.info("Merge completed successfully.")

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during merge: {e}")
        sys.exit(1)
    finally:
        log_stage_end("merge_results")


if __name__ == "__main__":
    main()