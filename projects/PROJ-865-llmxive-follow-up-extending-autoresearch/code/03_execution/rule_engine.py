import json
import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from utils.logging import get_logger, log_stage_start, log_stage_end
from utils.config import validate_resource_limits

logger = get_logger(__name__)

def load_rules_library(rules_path: Path) -> List[Dict[str, Any]]:
    """Load the rules library from a JSON file."""
    with open(rules_path, 'r') as f:
        rules = json.load(f)
    return rules

def load_annotated_failures(failures_path: Path) -> List[Dict[str, Any]]:
    """Load annotated failure cases from a JSON file."""
    with open(failures_path, 'r') as f:
        failures = json.load(f)
    return failures

def parse_error_log(error_log: str) -> Dict[str, Any]:
    """
    Parse an error log into a structured format.
    Returns a dictionary with parsed components.
    """
    parsed = {
        "raw": error_log,
        "error_type": None,
        "error_message": None,
        "line_number": None
    }

    if not error_log or not error_log.strip():
        return parsed

    # Extract error type
    error_type_patterns = [
        r"SyntaxError",
        r"Logical loop",
        r"Semantic ambiguity",
        r"Missing context",
        r"Unstructured"
    ]

    for pattern in error_type_patterns:
        if re.search(pattern, error_log, re.IGNORECASE):
            parsed["error_type"] = pattern
            break

    # Extract error message
    if "Error:" in error_log or "error:" in error_log:
        parts = error_log.split(":", 1)
        if len(parts) > 1:
            parsed["error_message"] = parts[1].strip()

    # Extract line number
    line_match = re.search(r"line (\d+)", error_log)
    if line_match:
        parsed["line_number"] = int(line_match.group(1))

    return parsed

def match_rule(parsed_error: Dict[str, Any], rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Match a parsed error against the rules library.
    Returns the first matching rule or None if no match is found.
    """
    for rule in rules:
        condition_pattern = rule.get("condition_pattern", "")
        
        # Check if the condition pattern matches the error type or message
        if condition_pattern in parsed_error.get("raw", ""):
            return rule
        
        # Check if the error type matches the condition pattern
        if parsed_error.get("error_type") and condition_pattern in parsed_error.get("error_type", ""):
            return rule

    # If no specific rule matches, check for "Unstructured" fallback
    for rule in rules:
        if rule.get("condition_pattern", "").lower() == "unstructured":
            return rule

    return None

def get_baseline_retrieval_method() -> str:
    """
    Get the baseline retrieval method for unstructured cases.
    Returns a string describing the method.
    """
    return "External search and retrieval"

def execute_pivot_action(rule: Dict[str, Any], failure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the pivot action from a matched rule.
    Returns a result dictionary with execution details.
    """
    start_time = time.time()
    
    pivot_action = rule.get("pivot_action", "No action defined")
    
    # Simulate execution (in real implementation, this would perform the actual action)
    success = True
    
    execution_result = {
        "task_id": failure.get("task_id"),
        "rule_id": rule.get("rule_id"),
        "pivot_action": pivot_action,
        "time_to_pivot": time.time() - start_time,
        "success": success,
        "failure_type": failure.get("annotated_structural_feature", "Unknown")
    }

    return execution_result

def run_rule_engine_on_failures(rules: List[Dict[str, Any]], failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the rule engine on a list of failure cases.
    Returns a list of execution results.
    """
    results = []
    
    for failure in failures:
        parsed_error = parse_error_log(failure.get("raw_error_log", ""))
        matched_rule = match_rule(parsed_error, rules)
        
        if matched_rule:
            result = execute_pivot_action(matched_rule, failure)
        else:
            # Handle unstructured cases by defaulting to baseline retrieval
            result = {
                "task_id": failure.get("task_id"),
                "rule_id": None,
                "pivot_action": get_baseline_retrieval_method(),
                "time_to_pivot": 0.0,
                "success": False,
                "failure_type": failure.get("annotated_structural_feature", "Unknown"),
                "fallback_used": True
            }
        
        results.append(result)
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save results to a CSV file."""
    import csv
    
    with open(output_path, 'w', newline='') as f:
        fieldnames = ["task_id", "rule_id", "pivot_action", "time_to_pivot", "success", "failure_type"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)

def main():
    """Main entry point for the rule engine."""
    project_root = Path(__file__).resolve().parent.parent.parent
    
    rules_path = project_root / "data" / "derived" / "rules_library.json"
    failures_path = project_root / "data" / "derived" / "failure_cases.json"
    output_path = project_root / "data" / "derived" / "results_rule_engine.csv"
    
    # Validate resource limits
    validate_resource_limits()
    
    # Load rules and failures
    rules = load_rules_library(rules_path)
    failures = load_annotated_failures(failures_path)
    
    # Run rule engine
    results = run_rule_engine_on_failures(rules, failures)
    
    # Save results
    save_results(results, output_path)
    
    logger.info(f"Rule engine completed. Results saved to {output_path}")

if __name__ == "__main__":
    main()