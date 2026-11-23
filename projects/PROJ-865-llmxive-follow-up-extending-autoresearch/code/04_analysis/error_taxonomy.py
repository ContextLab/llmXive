import json
import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from utils.logging import get_logger, log_stage_start, log_stage_end

logger = get_logger(__name__)

def load_results_csv(path: Path) -> List[Dict[str, Any]]:
    """Load results.csv into a list of dictionaries."""
    if not path.exists():
        logger.error(f"Results file not found: {path}")
        raise FileNotFoundError(f"Results file not found: {path}")
    
    results = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def load_failure_cases(path: Path) -> Dict[str, Dict[str, Any]]:
    """
    Load failure_cases.json and index by task_id.
    This provides the ground_truth_resolution for arbitration.
    """
    if not path.exists():
        logger.error(f"Failure cases file not found: {path}")
        raise FileNotFoundError(f"Failure cases file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Index by task_id for O(1) lookup
    return {entry['task_id']: entry for entry in data}

def categorize_failure(
    result_row: Dict[str, Any],
    failure_case: Dict[str, Any]
) -> Tuple[str, str]:
    """
    Arbitrate the categorization of a failure using ground_truth_resolution.
    
    Logic:
    1. If ground_truth_resolution is null/empty -> "Missing Ground Truth" (excluded from counts).
    2. If rule matched (method != 'Unstructured' or fallback_chain indicates match) BUT 
       the action taken (implied by success=False) did NOT match ground_truth_resolution:
       -> "Distillation Error" (The rule was insufficient/incorrect).
    3. If no rule matched (method == 'Unstructured' or fallback_chain empty) AND success=False:
       -> "Coverage Gap" (The rule set does not cover this failure type).
    
    Returns:
        Tuple (category, reason)
    """
    task_id = result_row.get('task_id')
    method = result_row.get('method', '')
    success_str = result_row.get('success', 'False')
    success = success_str.lower() in ('true', '1', 'yes')
    
    # Check Ground Truth
    ground_truth = failure_case.get('ground_truth_resolution')
    if not ground_truth or ground_truth.strip() == '':
        return "Missing Ground Truth", "Ground truth resolution is null or empty"
    
    # If the pivot was successful, it's not a failure to categorize in this context
    # (Though the taxonomy script usually runs on failures, we check just in case)
    if success:
        return "Success", "Pivot was successful"
    
    # Determine if a rule matched
    # Based on T017: "Unstructured - No Rule Match" sets fallback to "Manual Review"
    # We assume if method is 'Unstructured' or fallback_chain is empty, no rule matched.
    fallback_chain = result_row.get('fallback_chain', '')
    rule_matched = method != 'Unstructured' and fallback_chain != 'Manual Review' and fallback_chain != ''
    
    if not rule_matched:
        return "Coverage Gap", "No rule matched the failure pattern"
    else:
        # Rule matched, but pivot failed. This is a Distillation Error.
        # The rule predicted an action, but the ground truth required something else.
        return "Distillation Error", "Rule matched but action did not resolve the failure"

def build_taxonomy_report(
    results: List[Dict[str, Any]],
    failure_cases_map: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build the full taxonomy report including counts and breakdown.
    """
    coverage_gap_count = 0
    distillation_error_count = 0
    missing_gt_count = 0
    total_failures = 0
    
    breakdown_by_type: Dict[str, Dict[str, int]] = {}
    excluded_task_ids: List[str] = []

    for row in results:
        task_id = row.get('task_id')
        
        # Skip successful pivots for failure taxonomy
        if row.get('success', '').lower() in ('true', '1', 'yes'):
            continue

        failure_case = failure_cases_map.get(task_id)
        if not failure_case:
            logger.warning(f"Task ID {task_id} in results.csv not found in failure_cases.json. Skipping.")
            continue

        category, reason = categorize_failure(row, failure_case)

        if category == "Missing Ground Truth":
            missing_gt_count += 1
            excluded_task_ids.append(task_id)
            continue

        total_failures += 1
        
        failure_type = failure_case.get('annotated_structural_feature', 'Unstructured')
        
        if failure_type not in breakdown_by_type:
            breakdown_by_type[failure_type] = {"coverage_gap": 0, "distillation_error": 0}

        if category == "Coverage Gap":
            coverage_gap_count += 1
            breakdown_by_type[failure_type]["coverage_gap"] += 1
        elif category == "Distillation Error":
            distillation_error_count += 1
            breakdown_by_type[failure_type]["distillation_error"] += 1

    return {
        "coverage_gap_count": coverage_gap_count,
        "distillation_error_count": distillation_error_count,
        "missing_gt_count": missing_gt_count,
        "total_failures": total_failures,
        "breakdown_by_type": breakdown_by_type,
        "excluded_task_ids": excluded_task_ids
    }

def save_taxonomy_results(report: Dict[str, Any], output_path: Path):
    """Save the taxonomy report to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Taxonomy report saved to {output_path}")

def main():
    log_stage_start("Error Taxonomy Analysis")
    
    # Define paths
    project_root = Path(__file__).resolve().parents[2]
    results_csv_path = project_root / "data" / "derived" / "results.csv"
    failure_cases_json_path = project_root / "data" / "derived" / "failure_cases.json"
    output_json_path = project_root / "data" / "derived" / "error_taxonomy_results.json"

    # Pre-Check: Verify inputs exist
    if not results_csv_path.exists():
        logger.error(f"Pre-check failed: {results_csv_path} does not exist.")
        sys.exit(1)
    if not failure_cases_json_path.exists():
        logger.error(f"Pre-check failed: {failure_cases_json_path} does not exist.")
        sys.exit(1)

    try:
        # Load Data
        logger.info("Loading results.csv...")
        results = load_results_csv(results_csv_path)
        
        logger.info("Loading failure_cases.json...")
        failure_cases_map = load_failure_cases(failure_cases_json_path)
        
        # Build Report (Arbitration happens here)
        logger.info("Categorizing failures and arbitrating with ground truth...")
        report = build_taxonomy_report(results, failure_cases_map)
        
        # Save Output
        save_taxonomy_results(report, output_json_path)
        
        log_stage_end("Error Taxonomy Analysis")
        return 0

    except Exception as e:
        logger.error(f"Error during taxonomy analysis: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())