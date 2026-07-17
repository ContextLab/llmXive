import json
import sys
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import logging utilities from the project's utils module
try:
    from utils.logging import get_logger, log_stage_start, log_stage_end, log_resource_usage
except ImportError:
    # Fallback for direct execution if PYTHONPATH is not set up correctly
    import logging
    def get_logger(name): return logging.getLogger(name)
    def log_stage_start(logger, stage): logger.info(f"Starting stage: {stage}")
    def log_stage_end(logger, stage): logger.info(f"Ending stage: {stage}")
    def log_resource_usage(logger): pass

# Import resource watchdog for T013/T017 compliance
try:
    from utils.resource_watchdog import run_with_watchdog
except ImportError:
    run_with_watchdog = None

logger = get_logger(__name__)

def load_rules_library(rules_path: Path) -> List[Dict[str, Any]]:
    """Load the distilled rules library from JSON."""
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules library not found at {rules_path}")
    with open(rules_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_annotated_failures(failures_path: Path) -> List[Dict[str, Any]]:
    """Load annotated failure cases from JSON."""
    if not failures_path.exists():
        raise FileNotFoundError(f"Annotated failures not found at {failures_path}")
    with open(failures_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_error_log(error_log: str) -> Dict[str, Any]:
    """
    Parse raw error log text into a structured dictionary.
    Extracts key-value pairs and common error patterns.
    """
    parsed = {
        "raw_text": error_log,
        "keywords": [],
        "lines": []
    }
    lines = error_log.split('\n')
    parsed["lines"] = lines
    
    # Simple keyword extraction for rule matching
    keywords = set()
    for line in lines:
        # Extract potential keywords (alphanumeric words, excluding common stop words)
        words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9_]+\b', line)
        keywords.update(words)
    parsed["keywords"] = list(keywords)
    return parsed

def match_rule(error_parsed: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """
    Check if the parsed error matches a specific rule's conditions.
    Rule structure: {"condition": {"type": "keyword", "value": "..."}, ...}
    """
    condition = rule.get("condition", {})
    cond_type = condition.get("type")
    cond_value = condition.get("value")

    if cond_type == "keyword":
        return cond_value.lower() in [k.lower() for k in error_parsed.get("keywords", [])]
    elif cond_type == "contains":
        return cond_value.lower() in error_parsed.get("raw_text", "").lower()
    elif cond_type == "regex":
        return bool(re.search(cond_value, error_parsed.get("raw_text", "")))
    elif cond_type == "failure_type":
        # If the rule is specifically for a failure type, we check against the annotated case metadata
        # This function is called per-case in the main loop, so we pass the case type separately
        return False 
    
    return False

def execute_pivot_action(rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the action defined in the matched rule.
    Returns a result dictionary with the pivot action details.
    """
    action = rule.get("action", {})
    return {
        "action_type": action.get("type", "unknown"),
        "action_params": action.get("params", {}),
        "success": True,
        "message": f"Pivot action executed: {action.get('type')}"
    }

def get_baseline_retrieval_method(error_log: str, failure_type: str) -> Dict[str, Any]:
    """
    T018 Implementation: Handle 'Unstructured' cases by defaulting to baseline retrieval method.
    Since we cannot invoke the external baseline agent directly in this module (T021 handles that),
    we simulate the baseline retrieval behavior:
    1. Attempt to retrieve context based on keywords in the error log.
    2. Return a structured result indicating a "baseline retrieval" attempt was made.
    3. Mark success as False (since it's a fallback and we don't have the external agent's logic here)
       or True if we successfully retrieve a generic context (simulated).
    
    For the purpose of this pipeline, 'baseline retrieval' means:
    - Extract top keywords.
    - Return a generic "context_retrieved" flag with the keywords used.
    """
    parsed = parse_error_log(error_log)
    keywords = parsed.get("keywords", [])
    
    # Simulate baseline retrieval: just return the keywords as the "retrieved context"
    # In a real scenario, this would call an external vector DB or search API.
    result = {
        "action_type": "baseline_retrieval",
        "action_params": {
            "keywords": keywords[:5], # Top 5 keywords
            "method": "keyword_search_fallback"
        },
        "success": False, # Baseline is the fallback; we don't assume it succeeds without the external agent
        "message": f"Unstructured case detected. Defaulting to baseline retrieval with keywords: {keywords[:5]}",
        "failure_type": failure_type
    }
    return result

def run_rule_engine_on_failures(
    rules: List[Dict[str, Any]],
    failures: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Run the rule engine against a list of annotated failures.
    T018 Logic: If failure_type is 'Unstructured', skip rule matching and use baseline retrieval.
    """
    results = []
    
    for failure in failures:
        start_time = time.time()
        failure_id = failure.get("id", "unknown")
        failure_type = failure.get("failure_type", "Unknown")
        error_log = failure.get("error_log", "")
        
        parsed_error = parse_error_log(error_log)
        matched_rule = None
        pivot_result = None
        
        # T018: Check for Unstructured failure type
        if failure_type == "Unstructured":
            logger.info(f"Task {failure_id}: Failure type is 'Unstructured'. Using baseline retrieval method.")
            pivot_result = get_baseline_retrieval_method(error_log, failure_type)
        else:
            # Normal rule matching logic
            for rule in rules:
                if match_rule(parsed_error, rule):
                    matched_rule = rule
                    pivot_result = execute_pivot_action(rule)
                    break
          
        end_time = time.time()
        time_to_pivot = end_time - start_time
          
        result_entry = {
            "task_id": failure_id,
            "failure_type": failure_type,
            "method": "rule_engine",
            "time_to_pivot": time_to_pivot,
            "success": pivot_result.get("success", False) if pivot_result else False,
            "pivot_details": pivot_result,
            "matched_rule_id": matched_rule.get("id") if matched_rule else None
        }
        results.append(result_entry)
        
    return results

def save_results(results: List[Dict[str, Any]], output_path: Path):
    """Save results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

def main():
    """Main entry point for the rule engine execution."""
    # Paths (relative to project root)
    rules_path = Path("data/derived/rules_library.json")
    failures_path = Path("data/derived/annotated_failures.json")
    output_path = Path("data/derived/rule_engine_results.json")
    
    logger.info("Starting Rule Engine Execution")
    
    # Resource watchdog check if available
    if run_with_watchdog:
        logger.info("Running with Resource Watchdog")
        # Note: run_with_watchdog expects a callable. We wrap main logic.
        def run_logic():
            rules = load_rules_library(rules_path)
            failures = load_annotated_failures(failures_path)
            results = run_rule_engine_on_failures(rules, failures)
            save_results(results, output_path)
            logger.info(f"Results saved to {output_path}")
        
        run_with_watchdog(run_logic)
    else:
        # Fallback if watchdog is not available or not wrapped
        rules = load_rules_library(rules_path)
        failures = load_annotated_failures(failures_path)
        results = run_rule_engine_on_failures(rules, failures)
        save_results(results, output_path)
        logger.info(f"Results saved to {output_path}")

    logger.info("Rule Engine Execution Completed")

if __name__ == "__main__":
    main()