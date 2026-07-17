"""
error_taxonomy.py

Categorizes failed pivots based on rule matching and ground-truth resolution.
Ensures ground-truth is used to arbitrate categorization of failures.

Inputs:
  - data/derived/results.csv (from run_experiments.py)
  - data/derived/failure_cases.json (from annotate_failures.py/parse_reasoning_traces.py)

Outputs:
  - data/derived/error_taxonomy_results.json
"""

import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from utils.logging import get_logger, log_stage_start, log_stage_end

# Initialize logger
logger = get_logger(__name__)

# Constants
RESULTS_CSV_PATH = "data/derived/results.csv"
FAILURE_CASES_PATH = "data/derived/failure_cases.json"
OUTPUT_PATH = "data/derived/error_taxonomy_results.json"

FAILURE_TYPES = ["Syntactic", "Logical", "Semantic", "Missing Context", "Unstructured"]

def load_results_csv(path: str) -> List[Dict[str, Any]]:
    """Load the results CSV file."""
    results = []
    with open(path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def load_failure_cases(path: str) -> Dict[str, Any]:
    """Load the failure cases JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Ensure we have a dict keyed by task_id if it's a list, or handle structure
    if isinstance(data, list):
        # Assuming list of dicts with 'task_id' field
        return {item['task_id']: item for item in data if 'task_id' in item}
    return data

def categorize_failure(
    result: Dict[str, Any],
    failure_cases: Dict[str, Any],
    rules_library: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Categorize a single failure using ground-truth resolution.

    Logic:
    1. Check if a rule matched (from result['rule_matched'] or similar).
    2. If no rule matched -> "Coverage Gap".
    3. If rule matched:
       - Compare the executed action (or predicted pivot) against the ground-truth resolution.
       - If action != ground_truth -> "Distillation Error".
       - If action == ground_truth -> "Success" (should not appear in failed pivots, but handled).
    4. If the result indicates success but is in the failure set (edge case), mark as "Anomaly".

    The ground-truth resolution is retrieved from the failure_cases dict using the task_id.
    """
    task_id = result.get('task_id')
    if not task_id:
        logger.warning(f"Missing task_id in result: {result}")
        return {"task_id": task_id, "category": "Unknown", "reason": "Missing task_id"}

    # Get ground truth
    failure_case = failure_cases.get(task_id)
    if not failure_case:
        logger.warning(f"Missing ground-truth failure case for task_id: {task_id}")
        # Fallback if data is missing, though task implies it should exist
        return {"task_id": task_id, "category": "Missing Ground Truth", "reason": f"No ground truth found for {task_id}"}

    ground_truth_resolution = failure_case.get('ground_truth_resolution')
    if not ground_truth_resolution:
        logger.warning(f"Missing ground_truth_resolution for task_id: {task_id}")
        return {"task_id": task_id, "category": "Missing Ground Truth Data", "reason": "No ground_truth_resolution field"}

    # Check if rule matched
    # Assuming 'rule_matched' is a boolean or string 'True'/'False' in the CSV
    rule_matched = result.get('rule_matched')
    if rule_matched is None:
        # Fallback: check if there's a rule_id or similar
        rule_matched = bool(result.get('rule_id'))

    if not rule_matched:
        return {
            "task_id": task_id,
            "category": "Coverage Gap",
            "reason": "No rule matched the failure pattern",
            "failure_type": result.get('failure_type'),
            "ground_truth": ground_truth_resolution
        }

    # Rule matched, check if the action was correct
    # The result might contain 'executed_action' or 'pivot_action'
    executed_action = result.get('executed_action') or result.get('pivot_action')
    
    if executed_action is None:
        # If we can't determine the action, it's ambiguous
        return {
            "task_id": task_id,
            "category": "Distillation Error",
            "reason": "Rule matched but executed action is missing or invalid",
            "failure_type": result.get('failure_type'),
            "ground_truth": ground_truth_resolution
        }

    # Compare actions
    # Normalize comparison (string match, case-insensitive if applicable)
    is_correct = str(executed_action).strip().lower() == str(ground_truth_resolution).strip().lower()

    if not is_correct:
        return {
            "task_id": task_id,
            "category": "Distillation Error",
            "reason": f"Rule matched but action mismatch. Executed: {executed_action}, Ground Truth: {ground_truth_resolution}",
            "failure_type": result.get('failure_type'),
            "ground_truth": ground_truth_resolution,
            "executed_action": executed_action
        }
    else:
        # This shouldn't happen in a "failed pivot" list unless the definition of failure is time-based
        return {
            "task_id": task_id,
            "category": "Success (Anomaly in Failure Set)",
            "reason": "Action matched ground truth, but task is in failure set (possibly timeout)",
            "failure_type": result.get('failure_type'),
            "ground_truth": ground_truth_resolution
        }

def build_taxonomy_report(
    results: List[Dict[str, Any]],
    failure_cases: Dict[str, Any],
    rules_library: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Build the full taxonomy report by categorizing all results.
    """
    taxonomy_entries = []
    summary = {
        "Coverage Gap": 0,
        "Distillation Error": 0,
        "Missing Ground Truth": 0,
        "Missing Ground Truth Data": 0,
        "Success (Anomaly in Failure Set)": 0,
        "Unknown": 0
    }
    
    # Breakdown by failure type
    breakdown_by_type = {ft: {"Coverage Gap": 0, "Distillation Error": 0, "Other": 0} for ft in FAILURE_TYPES}

    for result in results:
        entry = categorize_failure(result, failure_cases, rules_library)
        taxonomy_entries.append(entry)
        
        category = entry.get('category', 'Unknown')
        summary[category] = summary.get(category, 0) + 1
        
        failure_type = entry.get('failure_type', 'Unknown')
        if failure_type in breakdown_by_type:
            if category in ["Coverage Gap", "Distillation Error"]:
                breakdown_by_type[failure_type][category] += 1
            else:
                breakdown_by_type[failure_type]["Other"] += 1

    report = {
        "total_cases": len(results),
        "summary": summary,
        "breakdown_by_failure_type": breakdown_by_type,
        "entries": taxonomy_entries
    }
    return report

def save_taxonomy_results(report: Dict[str, Any], path: str) -> None:
    """Save the taxonomy report to a JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    logger.info(f"Taxonomy results saved to {path}")

def main():
    log_stage_start("Error Taxonomy Analysis")
    
    # Load data
    logger.info(f"Loading results from {RESULTS_CSV_PATH}")
    results = load_results_csv(RESULTS_CSV_PATH)
    
    logger.info(f"Loading failure cases from {FAILURE_CASES_PATH}")
    failure_cases = load_failure_cases(FAILURE_CASES_PATH)
    
    # Note: rules_library is not strictly needed for the logic if we trust result['rule_matched'],
    # but we could load it if we needed to re-evaluate matching.
    # rules_library = load_rules_library("data/derived/rules_library.json") 

    # Build report
    logger.info(f"Categorizing {len(results)} failures using ground-truth resolution")
    report = build_taxonomy_report(results, failure_cases)
    
    # Save
    save_taxonomy_results(report, OUTPUT_PATH)
    
    log_stage_end("Error Taxonomy Analysis")
    return report

if __name__ == "__main__":
    main()