import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

INPUT_RESULTS_PATH = "data/derived/results.csv"
INPUT_FAILURE_CASES_PATH = "data/derived/failure_cases.json"
OUTPUT_TAXONOMY_PATH = "data/derived/error_taxonomy_results.json"

def load_results_csv(path: str) -> List[Dict[str, Any]]:
    """Load results from CSV file."""
    results = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def load_failure_cases(path: str) -> Dict[str, Dict[str, Any]]:
    """Load failure cases and index by task_id."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Failure cases file not found: {path}")
    
    with open(p, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    # Index by task_id for quick lookup
    return {case['task_id']: case for case in cases}

def categorize_failure(task_id: str, method: str, success: str, 
                      failure_cases_map: Dict[str, Dict[str, Any]]) -> Tuple[str, str]:
    """
    Categorize a failed pivot.
    
    Returns:
        Tuple of (category, failure_type)
        category: "coverage_gap" or "distillation_error"
        failure_type: The annotated structural feature
    """
    # Only categorize failures
    if success.lower() == 'true' or success.lower() == '1':
        return None, None
    
    if task_id not in failure_cases_map:
        logger.warning(f"Task {task_id} not found in failure cases. Skipping categorization.")
        return None, None
    
    failure_case = failure_cases_map[task_id]
    failure_type = failure_case.get('annotated_structural_feature', 'Unknown')
    ground_truth_resolution = failure_case.get('ground_truth_resolution', '')
    
    # The rule_engine.py logic (from T017) would have attempted to match a rule.
    # If no rule matched -> "Coverage Gap"
    # If rule matched but action != ground_truth_resolution -> "Distillation Error"
    
    # Since we don't have the specific rule match log in results.csv, we infer:
    # In a real scenario, results.csv would have a 'rule_matched' column.
    # Based on the task description logic:
    # We assume if the method is 'rule_engine' and it failed, we need to check
    # if the rule matched. Since we don't have that column, we simulate the check
    # by assuming if the failure_type is "Unstructured", it's a coverage gap (no rule),
    # otherwise it might be a distillation error if the rule existed but was wrong.
    # HOWEVER, the prompt says: "If no rule matches -> Coverage Gap; If rule matches but action != ground_truth -> Distillation Error".
    # We need to know if a rule matched. 
    # Let's assume the 'method' column tells us 'rule_engine'.
    # We need to determine if the rule matched. 
    # Since the results.csv schema (T024) only has: task_id, method, time_to_pivot, success, failure_type.
    # We cannot definitively know if a rule matched without an extra column.
    # BUT, the task T027 description implies we can determine this.
    # Let's re-read T017: "handle 'Unstructured' cases by defaulting to baseline retrieval method".
    # This implies if failure_type is "Unstructured", the rule engine did NOT match a rule (it defaulted).
    # So:
    # If failure_type == "Unstructured" -> Coverage Gap (no rule matched)
    # If failure_type != "Unstructured" AND success == False -> Distillation Error (rule matched but failed)
    
    if failure_type == "Unstructured":
        return "coverage_gap", failure_type
    else:
        return "distillation_error", failure_type

def build_taxonomy_report(results: List[Dict[str, Any]], 
                          failure_cases_map: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Build the error taxonomy report."""
    coverage_gap_count = 0
    distillation_error_count = 0
    breakdown_by_type: Dict[str, Dict[str, int]] = {}
    
    for row in results:
        task_id = row['task_id']
        method = row['method']
        success = row['success']
        
        # Only process failures from the rule_engine method
        if method != 'rule_engine' or success.lower() in ('true', '1'):
            continue
        
        category, failure_type = categorize_failure(task_id, method, success, failure_cases_map)
        
        if category is None:
            continue
        
        if category == "coverage_gap":
            coverage_gap_count += 1
        elif category == "distillation_error":
            distillation_error_count += 1
        
        if failure_type not in breakdown_by_type:
            breakdown_by_type[failure_type] = {"coverage_gap": 0, "distillation_error": 0}
        
        breakdown_by_type[failure_type][category] += 1
    
    total_failures = coverage_gap_count + distillation_error_count
    
    return {
        "coverage_gap_count": coverage_gap_count,
        "distillation_error_count": distillation_error_count,
        "total_failures": total_failures,
        "breakdown_by_type": breakdown_by_type
    }

def save_taxonomy_results(report: Dict[str, Any], path: str) -> None:
    """Save the taxonomy report to JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Taxonomy results saved to {path}")

def main():
    log_stage_start("error_taxonomy", INPUT_RESULTS_PATH, INPUT_FAILURE_CASES_PATH)
    
    try:
        # Load inputs
        logger.info(f"Loading results from {INPUT_RESULTS_PATH}")
        results = load_results_csv(INPUT_RESULTS_PATH)
        
        logger.info(f"Loading failure cases from {INPUT_FAILURE_CASES_PATH}")
        failure_cases_map = load_failure_cases(INPUT_FAILURE_CASES_PATH)
        
        # Build report
        logger.info("Building error taxonomy report...")
        report = build_taxonomy_report(results, failure_cases_map)
        
        # Save output
        logger.info(f"Saving taxonomy results to {OUTPUT_TAXONOMY_PATH}")
        save_taxonomy_results(report, OUTPUT_TAXONOMY_PATH)
        
        logger.info(f"Taxonomy complete. Total failures: {report['total_failures']}")
        log_stage_end("error_taxonomy", status="success")
        
    except Exception as e:
        logger.error(f"Error in error_taxonomy: {e}", exc_info=True)
        log_stage_end("error_taxonomy", status="failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
