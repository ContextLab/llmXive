"""
Task T014: Validate coverage of distilled rules against the validation split.

This script acts as the gatekeeper for the pipeline. It calculates the coverage
of the `rules_library.json` against a held-out validation set derived from
`data/derived/annotated_failures.json`.

Requirements:
- Coverage must be >= 0.90 (90%).
- If coverage < 90%, the script exits with code 1 to trigger the retry loop (T013d).
- Output: `data/derived/coverage_report.json`.
"""
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import validate_resource_limits

# Configure paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RULES_LIBRARY_PATH = PROJECT_ROOT / "data" / "derived" / "rules_library.json"
ANNOTATED_FAILURES_PATH = PROJECT_ROOT / "data" / "derived" / "annotated_failures.json"
OUTPUT_PATH = PROJECT_ROOT / "data" / "derived" / "coverage_report.json"
COVERAGE_THRESHOLD = 0.90

logger = get_logger(__name__)

def load_rules_library(path: Path) -> List[Dict[str, Any]]:
    """Load the distilled rules library."""
    if not path.exists():
        raise FileNotFoundError(f"Rules library not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Handle both list format and dict with 'rules' key
    if isinstance(data, dict) and "rules" in data:
        return data["rules"]
    return data

def load_annotated_failures(path: Path) -> List[Dict[str, Any]]:
    """Load the annotated failure cases."""
    if not path.exists():
        raise FileNotFoundError(f"Annotated failures not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def split_validation_set(failures: List[Dict[str, Any]], validation_ratio: float = 0.2) -> List[Dict[str, Any]]:
    """
    Split the failures into a validation set.
    For determinism, we use a simple index-based split assuming the input is shuffled or representative.
    """
    n = len(failures)
    split_idx = int(n * (1 - validation_ratio))
    # We take the last 20% as validation for this implementation
    return failures[split_idx:]

def extract_conditions(rule: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract the 'Condition' and 'Action' from a rule.
    Expected structure: {"condition": "...", "action": "...", ...}
    """
    return rule.get("condition"), rule.get("action")

def check_rule_matches(failure: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """
    Check if a specific rule matches a failure case.
    
    Matching Logic:
    1. The rule's 'condition' (a string description) must be found in the failure's
       'failure_description' or 'error_log'.
    2. The rule's 'failure_type' (if present) must match the failure's 'failure_type'.
    
    Returns True if the rule applies to this failure.
    """
    condition_str = rule.get("condition", "")
    rule_type = rule.get("failure_type")
    
    failure_desc = failure.get("failure_description", "").lower()
    error_log = failure.get("error_log", "").lower()
    failure_type = failure.get("failure_type", "")
    
    text_to_check = f"{failure_desc} {error_log}"
    
    # Condition match: simple substring check for heuristic rules
    condition_match = condition_str.lower() in text_to_check
    
    # Type match: if rule specifies a type, it must match
    type_match = (rule_type is None) or (rule_type == failure_type)
    
    return condition_match and type_match

def calculate_coverage(rules: List[Dict[str, Any]], validation_failures: List[Dict[str, Any]]) -> Tuple[float, List[str], List[str]]:
    """
    Calculate the coverage of rules against validation failures.
    
    Returns:
      - coverage_ratio (float): Fraction of failures matched by at least one rule.
      - covered_ids (List[str]): IDs of failures that were covered.
      - uncovered_ids (List[str]): IDs of failures that were NOT covered.
    """
    covered_ids = []
    uncovered_ids = []
    
    for failure in validation_failures:
        failure_id = failure.get("id", "unknown")
        is_covered = False
        
        for rule in rules:
            if check_rule_matches(failure, rule):
                is_covered = True
                break
        
        if is_covered:
            covered_ids.append(failure_id)
        else:
            uncovered_ids.append(failure_id)
    
    total = len(validation_failures)
    if total == 0:
        return 0.0, [], []
        
    coverage_ratio = len(covered_ids) / total
    return coverage_ratio, covered_ids, uncovered_ids

def save_coverage_report(report_data: Dict[str, Any], path: Path) -> None:
    """Save the coverage report to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    logger.info(f"Coverage report saved to {path}")

def main() -> int:
    """Main entry point for the validation task."""
    log_stage_start(logger, "T014_Validate_Coverage")
    
    # Check resource limits
    validate_resource_limits()
    log_resource_usage(logger)
    
    try:
        # 1. Load Data
        logger.info(f"Loading rules library from {RULES_LIBRARY_PATH}")
        rules = load_rules_library(RULES_LIBRARY_PATH)
        logger.info(f"Loaded {len(rules)} rules.")
        
        logger.info(f"Loading annotated failures from {ANNOTATED_FAILURES_PATH}")
        all_failures = load_annotated_failures(ANNOTATED_FAILURES_PATH)
        logger.info(f"Loaded {len(all_failures)} failure cases.")
        
        if not all_failures:
            logger.error("No failure cases found in annotated_failures.json. Cannot calculate coverage.")
            return 1
        
        # 2. Split Validation Set
        validation_failures = split_validation_set(all_failures)
        logger.info(f"Validation set size: {len(validation_failures)}")
        
        # 3. Calculate Coverage
        logger.info("Calculating coverage...")
        coverage_ratio, covered_ids, uncovered_ids = calculate_coverage(rules, validation_failures)
        
        logger.info(f"Coverage Ratio: {coverage_ratio:.4f} ({coverage_ratio*100:.2f}%)")
        logger.info(f"Covered: {len(covered_ids)}, Uncovered: {len(uncovered_ids)}")
        
        # 4. Generate Report
        report = {
            "task_id": "T014",
            "timestamp": str(Path(ANNOTATED_FAILURES_PATH).stat().st_mtime), # Simple timestamp source
            "total_validation_cases": len(validation_failures),
            "coverage_ratio": coverage_ratio,
            "threshold": COVERAGE_THRESHOLD,
            "passed": coverage_ratio >= COVERAGE_THRESHOLD,
            "uncovered_case_ids": uncovered_ids,
            "rule_count": len(rules)
        }
        
        save_coverage_report(report, OUTPUT_PATH)
        
        # 5. Gatekeeper Logic
        if coverage_ratio < COVERAGE_THRESHOLD:
            logger.error(f"COVERAGE FAILED: {coverage_ratio:.4f} < {COVERAGE_THRESHOLD}")
            logger.error(f"Triggering retry loop (T013d). See {OUTPUT_PATH} for details.")
            return 1
        
        logger.info("COVERAGE PASSED: Rules cover >= 90% of validation set.")
        return 0
        
    except Exception as e:
        logger.exception(f"Error during coverage validation: {e}")
        return 1
    finally:
        log_stage_end(logger)

if __name__ == "__main__":
    sys.exit(main())
