"""
T019: Run the rule engine on the tasks listed in data/derived/experiment_manifest.csv.

This script:
1. Loads the experiment manifest (stratified sample of 100 task IDs).
2. Loads the annotated failure cases to retrieve error logs.
3. Loads the distilled rules library.
4. Executes the rule engine on each task in the manifest.
5. Records Time-to-Pivot, Success, and Failure Type.
6. Writes results to data/derived/results.csv.

Execution must be wrapped by the ResourceWatchdog (T005c).
"""
import json
import csv
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import from project utils
from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import validate_resource_limits
from utils.resource_watchdog import run_with_watchdog

# Import from sibling modules in 03_execution
from rule_engine import (
    load_rules_library,
    load_annotated_failures,
    parse_error_log,
    match_rule,
    execute_pivot_action,
    run_rule_engine_on_failures,
    save_results as save_engine_results
)

# Import from 02_annotation_distillation for schema validation if needed
# (Assuming load_annotated_failures handles the data loading correctly)

# Import from 01_data_ingestion if we need raw traces (likely not needed here)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PROJECT_ROOT / "data" / "derived" / "experiment_manifest.csv"
RESULTS_PATH = PROJECT_ROOT / "data" / "derived" / "results.csv"
RULES_LIBRARY_PATH = PROJECT_ROOT / "data" / "derived" / "rules_library.json"
ANNOTATED_FAILURES_PATH = PROJECT_ROOT / "data" / "derived" / "failure_cases.json"

logger = get_logger(__name__)

def load_manifest(manifest_path: Path) -> List[Dict[str, Any]]:
    """Load the experiment manifest CSV."""
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    tasks = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tasks.append(row)
    
    logger.info(f"Loaded {len(tasks)} tasks from manifest.")
    return tasks

def run_single_experiment(
    task_id: str,
    failure_type: str,
    annotated_failures: Dict[str, Dict[str, Any]],
    rules: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Run the rule engine on a single task.
    
    Returns a dict with:
      - task_id
      - method: "rule_engine"
      - time_to_pivot: float (seconds)
      - success: bool
      - failure_type: str
    """
    # Retrieve the failure case for this task
    if task_id not in annotated_failures:
        logger.warning(f"Task {task_id} not found in annotated failures. Skipping.")
        return {
            "task_id": task_id,
            "method": "rule_engine",
            "time_to_pivot": 0.0,
            "success": False,
            "failure_type": failure_type,
            "error": "Task not found in annotated failures"
        }
    
    failure_case = annotated_failures[task_id]
    error_log = failure_case.get("error_log", "")
    
    # Parse error log
    parsed_error = parse_error_log(error_log)
    
    # Match rule
    matched_rule = match_rule(parsed_error, rules)
    
    # Execute pivot action
    start_time = time.time()
    success = False
    pivot_details = None
    
    if matched_rule:
        pivot_details = execute_pivot_action(matched_rule, parsed_error)
        # Determine success based on pivot result
        # For now, assume success if pivot action was executed without exception
        # In a real scenario, this might check against ground truth or a specific condition
        success = pivot_details.get("success", False)
    
    end_time = time.time()
    time_to_pivot = end_time - start_time
    
    result = {
        "task_id": task_id,
        "method": "rule_engine",
        "time_to_pivot": time_to_pivot,
        "success": success,
        "failure_type": failure_type
    }
    
    if not matched_rule:
        result["reason"] = "No rule matched"
    
    return result

def run_experiments() -> None:
    """Main entry point for running experiments."""
    log_stage_start(logger, "T019: Run Experiments")
    
    # Validate resource limits
    validate_resource_limits()
    
    # Load manifest
    logger.info(f"Loading manifest from {MANIFEST_PATH}")
    manifest = load_manifest(MANIFEST_PATH)
    
    # Load annotated failures
    logger.info(f"Loading annotated failures from {ANNOTATED_FAILURES_PATH}")
    annotated_failures = load_annotated_failures(ANNOTATED_FAILURES_PATH)
    
    # Load rules library
    logger.info(f"Loading rules library from {RULES_LIBRARY_PATH}")
    rules = load_rules_library(RULES_LIBRARY_PATH)
    
    results = []
    
    for task_entry in manifest:
        task_id = task_entry.get("task_id")
        failure_type = task_entry.get("failure_type", "Unknown")
        
        if not task_id:
            logger.warning("Skipping entry without task_id in manifest.")
            continue
        
        logger.info(f"Running experiment for task {task_id} (type: {failure_type})")
        
        try:
            result = run_single_experiment(
                task_id=task_id,
                failure_type=failure_type,
                annotated_failures=annotated_failures,
                rules=rules
            )
            results.append(result)
        except Exception as e:
            logger.error(f"Error running experiment for {task_id}: {e}", exc_info=True)
            # Record a failed attempt
            results.append({
                "task_id": task_id,
                "method": "rule_engine",
                "time_to_pivot": 0.0,
                "success": False,
                "failure_type": failure_type,
                "error": str(e)
            })
    
    # Save results
    logger.info(f"Saving {len(results)} results to {RESULTS_PATH}")
    save_engine_results(results, RESULTS_PATH)
    
    log_stage_end(logger, "T019: Run Experiments")

def main():
    """Entry point wrapped by watchdog."""
    run_with_watchdog(run_experiments)

if __name__ == "__main__":
    main()
