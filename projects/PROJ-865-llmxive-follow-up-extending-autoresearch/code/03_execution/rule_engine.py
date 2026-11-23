"""
Rule Engine for ARC-Bench Failure Analysis.

Executes distilled rules on failure cases and provides fallback strategies for
unstructured or unmatched cases.
"""

import json
import sys
import time
import re
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import logging from utils
try:
    from utils.logging import get_logger, log_stage_start, log_stage_end
except ImportError:
    # Fallback for direct execution context if utils is not in path
    import logging
    def get_logger(name): return logging.getLogger(name)
    def log_stage_start(*args, **kwargs): pass
    def log_stage_end(*args, **kwargs): pass

logger = get_logger(__name__)

# Configuration paths
RULES_LIBRARY_PATH = Path("data/derived/rules_library.json")
FAILURE_CASES_PATH = Path("data/derived/failure_cases.json")
RESULTS_OUTPUT_PATH = Path("data/derived/results_rule_engine.csv")

# Constants
MAX_KEYWORDS = 50
TOP_K_RESULTS = 3


def load_rules_library(rules_path: Path = RULES_LIBRARY_PATH) -> List[Dict[str, Any]]:
    """Load the distilled rules library from JSON."""
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules library not found at {rules_path}")
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    
    logger.info(f"Loaded {len(rules)} rules from {rules_path}")
    return rules


def load_annotated_failures(cases_path: Path = FAILURE_CASES_PATH) -> List[Dict[str, Any]]:
    """Load annotated failure cases from JSON."""
    if not cases_path.exists():
        raise FileNotFoundError(f"Failure cases not found at {cases_path}")
    
    with open(cases_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    logger.info(f"Loaded {len(cases)} failure cases from {cases_path}")
    return cases


def parse_error_log(error_log: str) -> Dict[str, Any]:
    """
    Parse an error log string into structured components.
    
    Returns a dict with:
      - 'raw': original string
      - 'prefix': first 50 characters (for keyword extraction)
      - 'keywords': list of extracted keywords
      - 'type': inferred error type if possible
    """
    if not error_log:
        return {
            'raw': '',
            'prefix': '',
            'keywords': [],
            'type': 'Unknown'
        }
    
    # Extract first 50 characters for keyword fallback
    prefix = error_log[:MAX_KEYWORDS]
    
    # Simple keyword extraction: split on non-alphanumeric, filter short words
    words = re.findall(r'\b\w+\b', prefix.lower())
    keywords = [w for w in words if len(w) > 2]  # Filter very short words
    
    # Simple type inference based on common patterns
    error_lower = error_log.lower()
    if 'syntax' in error_lower or 'indentation' in error_lower:
        error_type = 'Syntactic Error'
    elif 'loop' in error_lower and ('infinite' in error_lower or 'recursive' in error_lower):
        error_type = 'Logical Loop'
    elif 'ambiguity' in error_lower or 'unclear' in error_lower:
        error_type = 'Semantic Ambiguity'
    elif 'context' in error_lower or 'missing' in error_lower:
        error_type = 'Missing Context'
    else:
        error_type = 'Unstructured'
    
    return {
        'raw': error_log,
        'prefix': prefix,
        'keywords': list(set(keywords)),  # Unique keywords
        'type': error_type
    }


def match_rule(parsed_log: Dict[str, Any], rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Attempt to match a parsed error log against the rules library.
    
    Returns the matching rule if found, None otherwise.
    """
    for rule in rules:
        condition_pattern = rule.get('condition_pattern', '')
        
        # Try to match the condition pattern against the raw error log
        try:
            if re.search(condition_pattern, parsed_log['raw'], re.IGNORECASE):
                logger.debug(f"Rule '{rule.get('rule_id')}' matched")
                return rule
        except re.error as e:
            logger.warning(f"Invalid regex pattern in rule {rule.get('rule_id')}: {e}")
            continue
    
    return None


def get_baseline_retrieval_method(parsed_log: Dict[str, Any]) -> str:
    """
    Determine the baseline retrieval method based on parsed log.
    
    This simulates the baseline agent's probabilistic retrieval.
    """
    if parsed_log['type'] == 'Unstructured':
        return 'probabilistic_fallback'
    elif parsed_log['type'] == 'Syntactic Error':
        return 'syntax_parser'
    elif parsed_log['type'] == 'Logical Loop':
        return 'control_flow_analyzer'
    else:
        return 'semantic_search'


def execute_pivot_action(rule: Dict[str, Any], parsed_log: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the pivot action defined in a matched rule.
    
    Returns a result dict with:
      - 'success': boolean indicating if pivot succeeded
      - 'method': the method used
      - 'time_to_pivot': time taken in seconds
      - 'action': the action taken
    """
    start_time = time.time()
    
    pivot_action = rule.get('pivot_action', 'unknown_action')
    
    # Simulate pivot execution (in real implementation, this would call the actual action)
    # For now, we assume success unless the action is explicitly marked as failing
    success = pivot_action != 'fail_pivot'
    
    time_taken = time.time() - start_time
    
    return {
        'success': success,
        'method': rule.get('rule_id', 'unknown'),
        'time_to_pivot': time_taken,
        'action': pivot_action,
        'fallback_chain': 'Primary'
    }


def keyword_based_fallback(parsed_log: Dict[str, Any], rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Secondary fallback: keyword-based retrieval for unstructured cases.
    
    Uses the first 50 characters of the error log to extract keywords
    and matches against rule condition patterns.
    
    Returns the best matching rule if found, None otherwise.
    """
    if not parsed_log['keywords']:
        return None
    
    # Score rules based on keyword matches
    scored_rules = []
    for rule in rules:
        condition_pattern = rule.get('condition_pattern', '')
        keyword_matches = 0
        
        # Count how many keywords appear in the condition pattern
        for keyword in parsed_log['keywords']:
            if keyword in condition_pattern.lower():
                keyword_matches += 1
        
        if keyword_matches > 0:
            scored_rules.append((keyword_matches, rule))
    
    if not scored_rules:
        return None
    
    # Sort by number of matches (descending) and return top result
    scored_rules.sort(key=lambda x: x[0], reverse=True)
    best_match = scored_rules[0][1]
    
    logger.debug(f"Keyword fallback matched rule '{best_match.get('rule_id')}' with {scored_rules[0][0]} keyword matches")
    return best_match


def run_rule_engine_on_failures(
    cases: List[Dict[str, Any]], 
    rules: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Run the rule engine on a list of failure cases.
    
    For each case:
    1. Parse the error log
    2. Attempt primary rule matching
    3. If no match and case is 'Unstructured', attempt keyword-based fallback
    4. Execute pivot action if a rule is found
    5. Record results including fallback chain
    
    Returns a list of result dicts.
    """
    results = []
    
    for case in cases:
        task_id = case.get('task_id', 'unknown')
        error_log = case.get('raw_error_log', '')
        failure_type = case.get('annotated_structural_feature', 'Unstructured')
        
        logger.info(f"Processing task {task_id} ({failure_type})")
        
        # Parse the error log
        parsed_log = parse_error_log(error_log)
        
        # Primary rule matching
        matched_rule = match_rule(parsed_log, rules)
        
        if matched_rule:
            # Primary match successful
            result = execute_pivot_action(matched_rule, parsed_log)
            result['task_id'] = task_id
            result['failure_type'] = failure_type
            result['fallback_chain'] = 'Primary'
            results.append(result)
            logger.info(f"Task {task_id}: Primary match successful")
        else:
            # No primary match - check if fallback is appropriate
            if failure_type == 'Unstructured':
                # Attempt keyword-based fallback
                fallback_rule = keyword_based_fallback(parsed_log, rules)
                
                if fallback_rule:
                    # Fallback successful
                    result = execute_pivot_action(fallback_rule, parsed_log)
                    result['task_id'] = task_id
                    result['failure_type'] = failure_type
                    result['fallback_chain'] = 'Primary->Secondary'
                    results.append(result)
                    logger.info(f"Task {task_id}: Fallback successful (Primary->Secondary)")
                else:
                    # Both primary and fallback failed
                    result = {
                        'task_id': task_id,
                        'failure_type': failure_type,
                        'success': False,
                        'method': 'none',
                        'time_to_pivot': 0.0,
                        'action': 'no_match',
                        'fallback_chain': 'None'
                    }
                    results.append(result)
                    logger.warning(f"Task {task_id}: No match found (Primary and Fallback failed)")
            else:
                # Not an unstructured case, no fallback attempted
                result = {
                    'task_id': task_id,
                    'failure_type': failure_type,
                    'success': False,
                    'method': 'none',
                    'time_to_pivot': 0.0,
                    'action': 'no_match',
                    'fallback_chain': 'None'
                }
                results.append(result)
                logger.warning(f"Task {task_id}: No match found (No fallback for {failure_type})")
    
    return results


def save_results(results: List[Dict[str, Any]], output_path: Path = RESULTS_OUTPUT_PATH) -> None:
    """
    Save rule engine results to a CSV file.
    
    Includes the new 'fallback_chain' column as required by T052.
    """
    if not results:
        logger.warning("No results to save")
        return
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define CSV columns
    fieldnames = [
        'task_id', 
        'failure_type', 
        'success', 
        'method', 
        'time_to_pivot', 
        'action', 
        'fallback_chain'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            # Ensure all fields are present
            row = {field: result.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Saved {len(results)} results to {output_path}")


def main():
    """Main entry point for the rule engine."""
    log_stage_start("Rule Engine Execution")
    
    try:
        # Load rules and failure cases
        rules = load_rules_library()
        cases = load_annotated_failures()
        
        # Run the rule engine
        results = run_rule_engine_on_failures(cases, rules)
        
        # Save results
        save_results(results)
        
        # Log summary
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        primary_only = sum(1 for r in results if r['fallback_chain'] == 'Primary')
        fallback_used = sum(1 for r in results if r['fallback_chain'] == 'Primary->Secondary')
        no_match = sum(1 for r in results if r['fallback_chain'] == 'None')
        
        logger.info(f"Rule Engine Summary:")
        logger.info(f"  Total cases: {total_count}")
        logger.info(f"  Successful pivots: {success_count} ({100*success_count/total_count:.1f}%)")
        logger.info(f"  Primary matches only: {primary_only}")
        logger.info(f"  Fallback used (Primary->Secondary): {fallback_used}")
        logger.info(f"  No match (fallback failed): {no_match}")
        
        log_stage_end("Rule Engine Execution", success=True)
        return 0
        
    except Exception as e:
        logger.error(f"Rule Engine failed: {e}", exc_info=True)
        log_stage_end("Rule Engine Execution", success=False)
        return 1


if __name__ == "__main__":
    sys.exit(main())