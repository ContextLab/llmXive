"""
Coverage Measurement Script for ARC-Bench Rule Distillation.

This script calculates the coverage of the distilled rules library against the
validation set of failure cases. It verifies that at least 90% of cases are
covered by the rules.

Output: data/derived/coverage_report.json
Exit Code: 1 if coverage < 90%, 0 otherwise.
"""
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
from utils.config import validate_resource_limits, MAX_MEMORY_GB

logger = get_logger(__name__)

def load_rules_library(rules_path: Path) -> List[Dict[str, Any]]:
    """Load the distilled rules library from JSON."""
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules library not found at {rules_path}")
    with open(rules_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        # Handle both list format and dict with 'rules' key
        if isinstance(data, dict) and 'rules' in data:
            return data['rules']
        return data

def load_annotated_failures(failures_path: Path) -> List[Dict[str, Any]]:
    """Load the annotated failure cases from JSON."""
    if not failures_path.exists():
        raise FileNotFoundError(f"Annotated failures not found at {failures_path}")
    with open(failures_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def split_validation_set(failures: List[Dict[str, Any]], seed: int = 42) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Split failures into train, val, and test sets.
    For this task, we specifically need the validation set.
    We assume the input is the full set and we need to recreate the split
    consistent with T011b.
    """
    import random
    random.seed(seed)
    shuffled = failures.copy()
    random.shuffle(shuffled)
    
    n = len(shuffled)
    train_end = int(n * 0.6)
    val_end = int(n * 0.8)
    
    train = shuffled[:train_end]
    val = shuffled[train_end:val_end]
    test = shuffled[val_end:]
    
    return train, val, test

def extract_conditions(rule: Dict[str, Any]) -> List[str]:
    """Extract condition patterns from a rule."""
    conditions = []
    if 'condition_pattern' in rule:
        conditions.append(rule['condition_pattern'])
    if 'pivot_action' in rule:
        # Sometimes the action itself implies a condition or pattern
        conditions.append(rule['pivot_action'])
    return conditions

def check_rule_matches(error_log: str, conditions: List[str]) -> bool:
    """Check if any condition pattern matches the error log."""
    if not error_log:
        return False
    
    for condition in conditions:
        if not condition:
            continue
        try:
            # Case-insensitive regex match
            if re.search(re.escape(condition), error_log, re.IGNORECASE):
                return True
            # Also try simple substring match for robustness
            if condition.lower() in error_log.lower():
                return True
        except re.error:
            # If regex is invalid, skip this condition
            logger.warning(f"Invalid regex pattern: {condition}")
            continue
    
    return False

def calculate_coverage(rules: List[Dict[str, Any]], failures: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
    """
    Calculate the coverage of rules against failures.
    Returns coverage percentage and list of uncovered task_ids.
    """
    if not failures:
        return 0.0, []
    
    covered_count = 0
    uncovered_tasks = []
    
    for failure in failures:
        task_id = failure.get('task_id', 'unknown')
        error_log = failure.get('raw_error_log', '')
        
        matched = False
        for rule in rules:
            conditions = extract_conditions(rule)
            if check_rule_matches(error_log, conditions):
                matched = True
                break
        
        if matched:
            covered_count += 1
        else:
            uncovered_tasks.append(task_id)
    
    coverage = (covered_count / len(failures)) * 100.0
    return coverage, uncovered_tasks

def save_coverage_report(coverage: float, total_cases: int, covered_cases: int, 
                         uncovered_tasks: List[str], output_path: Path):
    """Save the coverage report to JSON."""
    report = {
        "coverage_percentage": round(coverage, 2),
        "total_cases": total_cases,
        "covered_cases": covered_cases,
        "uncovered_cases": len(uncovered_tasks),
        "uncovered_task_ids": uncovered_tasks,
        "threshold_met": coverage >= 90.0
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Coverage report saved to {output_path}")
    return report

def main():
    """Main entry point for coverage measurement."""
    log_stage_start("Coverage Measurement", logger)
    log_resource_usage(logger)
    
    # Validate resource limits first
    try:
        validate_resource_limits()
    except Exception as e:
        logger.error(f"Resource limit validation failed: {e}")
        sys.exit(1)
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    rules_path = project_root / "data" / "derived" / "rules_library.json"
    failures_path = project_root / "data" / "derived" / "failure_cases.json"
    output_path = project_root / "data" / "derived" / "coverage_report.json"
    
    # Load data
    try:
        logger.info(f"Loading rules library from {rules_path}")
        rules = load_rules_library(rules_path)
        logger.info(f"Loaded {len(rules)} rules")
        
        logger.info(f"Loading annotated failures from {failures_path}")
        all_failures = load_annotated_failures(failures_path)
        logger.info(f"Loaded {len(all_failures)} failure cases")
        
        # Split to get validation set (consistent with T011b)
        # T011b uses seed 42 for splitting
        _, val_set, _ = split_validation_set(all_failures, seed=42)
        logger.info(f"Validation set size: {len(val_set)}")
        
    except FileNotFoundError as e:
        logger.error(f"Required input file missing: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format in input files: {e}")
        sys.exit(1)
    
    # Calculate coverage
    logger.info("Calculating rule coverage...")
    coverage, uncovered_tasks = calculate_coverage(rules, val_set)
    
    logger.info(f"Coverage: {coverage:.2f}% ({len(val_set) - len(uncovered_tasks)}/{len(val_set)} cases covered)")
    
    # Save report
    report = save_coverage_report(coverage, len(val_set), len(val_set) - len(uncovered_tasks), 
                                  uncovered_tasks, output_path)
    
    # Check threshold
    if coverage < 90.0:
        logger.error(f"Coverage threshold NOT met! Required: 90%, Actual: {coverage:.2f}%")
        logger.error(f"Uncovered tasks: {uncovered_tasks}")
        log_stage_end("Coverage Measurement", logger, success=False)
        sys.exit(1)
    
    logger.info(f"Coverage threshold met! ({coverage:.2f}% >= 90%)")
    log_stage_end("Coverage Measurement", logger, success=True)
    sys.exit(0)

if __name__ == "__main__":
    main()
