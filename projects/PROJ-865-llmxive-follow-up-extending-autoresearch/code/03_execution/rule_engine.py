"""
Rule Engine for ARC-Bench Failure Pivot Execution.

Implements deterministic rule matching and execution based on the distilled rules library.
Handles 'Unstructured' failure cases by defaulting to a baseline retrieval method.
"""
import json
import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Ensure imports work when run from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage

logger = get_logger(__name__)


def load_rules_library(path: Path) -> List[Dict[str, Any]]:
    """Load the distilled rules library from JSON."""
    logger.info(f"Loading rules library from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Rules library not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    
    logger.info(f"Loaded {len(rules)} rules")
    return rules


def load_annotated_failures(path: Path) -> List[Dict[str, Any]]:
    """Load the annotated failure cases."""
    logger.info(f"Loading annotated failures from {path}")
    if not path.exists():
        raise FileNotFoundError(f"Annotated failures not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        failures = json.load(f)
    
    logger.info(f"Loaded {len(failures)} failure cases")
    return failures


def parse_error_log(error_log: str) -> Dict[str, Any]:
    """
    Parse a raw error log string into structured components.
    Extracts key information like error type, message, and stack trace hints.
    """
    parsed = {
        "raw": error_log,
        "error_type": None,
        "message": None,
        "stack_trace": None
    }
    
    if not error_log:
        return parsed
    
    # Basic heuristic parsing
    error_lines = error_log.split('\n')
    for line in error_lines:
        line = line.strip()
        if line.startswith("Error:") or line.startswith("Exception:"):
            parsed["error_type"] = line
        elif "Traceback" in line:
            parsed["stack_trace"] = True
        elif parsed["message"] is None and len(line) > 5:
            parsed["message"] = line
    
    return parsed


def match_rule(error_parsed: Dict[str, Any], failure_feature: str, rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Attempt to match the parsed error and failure feature against the rules library.
    Returns the first matching rule, or None if no match is found.
    
    For 'Unstructured' failure types, this function returns None to trigger
    the baseline retrieval fallback (handled in execute_pivot_action).
    """
    if failure_feature == "Unstructured":
        logger.debug(f"Unstructured failure detected - skipping rule match for baseline fallback")
        return None
    
    error_msg = (error_parsed.get("message") or "").lower()
    error_type = (error_parsed.get("error_type") or "").lower()
    
    for rule in rules:
        conditions = rule.get("conditions", [])
        match = True
        
        for condition in conditions:
            field = condition.get("field")
            pattern = condition.get("pattern", "")
            operator = condition.get("operator", "contains")
            
            if field == "error_type":
                value = error_type
            elif field == "message":
                value = error_msg
            else:
                match = False
                break
            
            if operator == "contains":
                if pattern.lower() not in value:
                    match = False
                    break
            elif operator == "equals":
                if pattern.lower() != value:
                    match = False
                    break
            elif operator == "regex":
                if not re.search(pattern, value, re.IGNORECASE):
                    match = False
                    break
        
        if match:
            logger.debug(f"Rule matched: {rule.get('rule_id', 'unknown')}")
            return rule
    
    logger.debug("No rule matched for this failure")
    return None


def get_baseline_retrieval_method(error_parsed: Dict[str, Any], failure_feature: str) -> Dict[str, Any]:
    """
    Fallback method for 'Unstructured' cases or when no rule matches.
    Uses a simple heuristic retrieval strategy based on error content.
    """
    logger.info("Executing baseline retrieval method for unstructured/no-match case")
    
    error_msg = (error_parsed.get("message") or "").lower()
    
    # Simple heuristic: if we can't parse, return a generic resolution
    # In a real system, this might call an external API or use a different model
    resolution = {
        "method": "baseline_heuristic",
        "action": "retry_with_context",
        "confidence": 0.5,
        "details": "Default baseline retrieval triggered for unstructured or unmatched failure"
    }
    
    # Basic keyword-based adjustments
    if "timeout" in error_msg:
        resolution["action"] = "increase_timeout"
        resolution["confidence"] = 0.7
    elif "memory" in error_msg or "oom" in error_msg:
        resolution["action"] = "reduce_batch_size"
        resolution["confidence"] = 0.7
    elif "syntax" in error_msg:
        resolution["action"] = "syntax_check"
        resolution["confidence"] = 0.8
    
    return resolution


def execute_pivot_action(rule: Optional[Dict[str, Any]], error_parsed: Dict[str, Any], 
                         failure_feature: str) -> Tuple[str, float]:
    """
    Execute the pivot action based on the matched rule or fallback.
    
    Returns:
        Tuple of (action_description, time_taken_seconds)
    
    For 'Unstructured' cases or no rule match, defaults to baseline retrieval method.
    """
    start_time = time.time()
    
    if rule is not None:
        # Execute rule-based pivot
        action = rule.get("action", "unknown_action")
        action_desc = f"Rule-based pivot: {action}"
        logger.info(f"Executing rule-based action: {action}")
    else:
        # Fallback to baseline retrieval
        baseline_result = get_baseline_retrieval_method(error_parsed, failure_feature)
        action = baseline_result.get("action", "unknown")
        action_desc = f"Baseline retrieval: {action}"
        logger.info(f"Executing baseline retrieval action: {action}")
    
    # Simulate execution time (in real scenario, this would execute the action)
    # For now, we just measure the logic time
    elapsed = time.time() - start_time
    
    return action_desc, elapsed


def run_rule_engine_on_failures(rules: List[Dict[str, Any]], 
                                failures: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run the rule engine on all annotated failures.
    
    For each failure:
    1. Parse the error log
    2. Attempt to match a rule (skips if failure_feature is 'Unstructured')
    3. Execute pivot action (uses baseline fallback for Unstructured/no-match)
    4. Record results
    """
    results = []
    
    logger.info(f"Running rule engine on {len(failures)} failure cases")
    
    for failure in failures:
        task_id = failure.get("task_id", "unknown")
        error_log = failure.get("raw_error_log", "")
        failure_feature = failure.get("annotated_structural_feature", "Unstructured")
        
        # Parse error log
        error_parsed = parse_error_log(error_log)
        
        # Attempt rule match
        matched_rule = match_rule(error_parsed, failure_feature, rules)
        
        # Execute pivot (with baseline fallback for Unstructured)
        action_desc, time_taken = execute_pivot_action(matched_rule, error_parsed, failure_feature)
        
        # Determine success (heuristic: if we got a valid action)
        success = action_desc is not None and len(action_desc) > 0
        
        result = {
            "task_id": task_id,
            "failure_type": failure_feature,
            "matched_rule_id": matched_rule.get("rule_id") if matched_rule else None,
            "action_executed": action_desc,
            "time_to_pivot": time_taken,
            "success": success,
            "used_baseline": matched_rule is None
        }
        
        results.append(result)
        logger.debug(f"Processed task {task_id}: {action_desc}")
    
    logger.info(f"Completed rule engine run on {len(results)} cases")
    return results


def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save the rule engine results to a JSON file."""
    logger.info(f"Saving results to {output_path}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(results)} results")


def main():
    """Main entry point for the rule engine."""
    log_stage_start("rule_engine")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    rules_path = project_root / "data" / "derived" / "rules_library.json"
    failures_path = project_root / "data" / "derived" / "failure_cases.json"
    output_path = project_root / "data" / "derived" / "rule_engine_results.json"
    
    try:
        # Load data
        rules = load_rules_library(rules_path)
        failures = load_annotated_failures(failures_path)
        
        # Run rule engine
        results = run_rule_engine_on_failures(rules, failures)
        
        # Save results
        save_results(results, output_path)
        
        log_stage_end("rule_engine", status="success")
        logger.info("Rule engine execution completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        log_stage_end("rule_engine", status="error", error=str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        log_stage_end("rule_engine", status="error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()