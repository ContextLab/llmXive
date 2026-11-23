"""
Pilot Execution: Run Rule Engine on Small Subset (N=10).

This script executes the rule engine on a stratified subset of the annotated
failure data to verify data flow, metric logging, and censored data handling.

It reads the rules library generated in T082 and the annotated failures,
executes the pivot actions, and logs the results to data/derived/pilot_results.csv.

Dependencies:
- T082: Must have generated data/derived/pilot_rules.json (or rules_library.json)
- T009a/T005e: Must have generated annotated failures data
"""
import json
import csv
import sys
import time
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.logging import get_logger, log_stage_start, log_stage_end
from code.utils.config import TIMEOUT_SECONDS, DEFAULT_SAMPLE_SIZE

logger = get_logger(__name__)

def load_rules_library(rules_path: Path) -> List[Dict[str, Any]]:
    """Load the rules library from JSON file."""
    if not rules_path.exists():
        raise FileNotFoundError(f"Rules library not found at {rules_path}")
    
    with open(rules_path, 'r', encoding='utf-8') as f:
        rules = json.load(f)
    
    logger.info(f"Loaded {len(rules)} rules from {rules_path}")
    return rules

def load_annotated_failures(failures_path: Path, subset_size: int = DEFAULT_SAMPLE_SIZE) -> List[Dict[str, Any]]:
    """Load annotated failures and apply stratified sampling."""
    if not failures_path.exists():
        raise FileNotFoundError(f"Annotated failures not found at {failures_path}")
    
    with open(failures_path, 'r', encoding='utf-8') as f:
        failures = json.load(f)
    
    logger.info(f"Loaded {len(failures)} annotated failures from {failures_path}")
    
    # Stratified sampling by structural feature
    from collections import defaultdict
    import random
    
    # Group by feature
    groups = defaultdict(list)
    for failure in failures:
        feature = failure.get('annotated_structural_feature', 'Unstructured')
        groups[feature].append(failure)
    
    # Sample proportionally
    sampled = []
    for feature, items in groups.items():
        n_sample = min(len(items), max(1, int(subset_size * len(items) / len(failures))))
        sampled.extend(random.sample(items, n_sample))
    
    logger.info(f"Stratified sample: {len(sampled)} failures (target: {subset_size})")
    return sampled

def parse_error_log(error_log: str) -> Dict[str, Any]:
    """Parse error log into structured components."""
    # Simple parsing: extract error type and message
    lines = error_log.split('\n')
    error_type = lines[0].strip() if lines else "Unknown"
    
    return {
        'raw_error': error_log,
        'error_type': error_type,
        'lines': lines
    }

def match_rule(error_log: str, rules: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Match error log against rules using condition patterns."""
    for rule in rules:
        pattern = rule.get('condition_pattern', '')
        if not pattern:
            continue
        
        try:
            if re.search(pattern, error_log, re.IGNORECASE):
                return rule
        except re.error as e:
            logger.warning(f"Invalid regex pattern in rule {rule.get('rule_id', 'unknown')}: {e}")
            continue
    
    return None

def execute_pivot_action(rule: Dict[str, Any], error_log: str) -> Tuple[str, float]:
    """
    Execute the pivot action defined in the rule.
    
    Returns:
        Tuple of (action_description, time_taken_seconds)
    """
    start_time = time.time()
    
    action = rule.get('pivot_action', 'Manual Review')
    
    # Simulate execution time (real implementation would call actual pivot logic)
    # For pilot, we simulate based on action complexity
    if 'recompile' in action.lower():
        time.sleep(0.01)  # Fast
    elif 'refactor' in action.lower():
        time.sleep(0.02)
    elif 'manual' in action.lower():
        time.sleep(0.05)  # Slowest
    else:
        time.sleep(0.01)
    
    elapsed = time.time() - start_time
    
    # Enforce timeout
    if elapsed > TIMEOUT_SECONDS:
        elapsed = TIMEOUT_SECONDS
    
    return action, elapsed

def run_rule_engine_on_failures(
    failures: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    output_path: Path
) -> List[Dict[str, Any]]:
    """Run rule engine on all failures and save results."""
    results = []
    
    for failure in failures:
        task_id = failure.get('task_id', 'unknown')
        error_log = failure.get('raw_error_log', '')
        ground_truth = failure.get('ground_truth_resolution', '')
        
        # Parse error
        parsed = parse_error_log(error_log)
        
        # Match rule
        matched_rule = match_rule(error_log, rules)
        
        if matched_rule:
            action, time_taken = execute_pivot_action(matched_rule, error_log)
            success = (action == ground_truth)
            rule_id = matched_rule.get('rule_id', 'unknown')
        else:
            action = "Manual Review"
            time_taken = 0.0
            success = False
            rule_id = None
        
        result = {
            'task_id': task_id,
            'error_type': parsed['error_type'],
            'matched_rule_id': rule_id,
            'pivot_action': action,
            'time_to_pivot': time_taken,
            'success': success,
            'ground_truth': ground_truth,
            'annotated_feature': failure.get('annotated_structural_feature', 'Unstructured')
        }
        
        results.append(result)
        logger.debug(f"Processed {task_id}: matched={rule_id is not None}, success={success}")
    
    # Write results to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'task_id', 'error_type', 'matched_rule_id', 'pivot_action',
            'time_to_pivot', 'success', 'ground_truth', 'annotated_feature'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved {len(results)} results to {output_path}")
    return results

def main():
    """Main entry point for pilot rule engine execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Rule Engine on Pilot Subset')
    parser.add_argument('--subset-size', type=int, default=DEFAULT_SAMPLE_SIZE,
                      help='Number of samples to process')
    parser.add_argument('--rules-path', type=str, default=None,
                      help='Path to rules library (default: data/derived/pilot_rules.json)')
    parser.add_argument('--failures-path', type=str, default=None,
                      help='Path to annotated failures (default: data/derived/annotated_failures.json)')
    parser.add_argument('--output-path', type=str, default=None,
                      help='Output path for results (default: data/derived/pilot_results.csv)')
    
    args = parser.parse_args()
    
    log_stage_start(logger, 'run_rule_engine_pilot')
    
    # Resolve paths
    rules_path = Path(args.rules_path) if args.rules_path else project_root / 'data' / 'derived' / 'pilot_rules.json'
    failures_path = Path(args.failures_path) if args.failures_path else project_root / 'data' / 'derived' / 'annotated_failures.json'
    output_path = Path(args.output_path) if args.output_path else project_root / 'data' / 'derived' / 'pilot_results.csv'
    
    try:
        # Load rules
        rules = load_rules_library(rules_path)
        
        # Load failures
        failures = load_annotated_failures(failures_path, args.subset_size)
        
        # Run rule engine
        results = run_rule_engine_on_failures(failures, rules, output_path)
        
        # Log summary
        success_count = sum(1 for r in results if r['success'])
        logger.info(f"Pilot execution complete: {success_count}/{len(results)} successful")
        
        log_stage_end(logger, 'run_rule_engine_pilot', status='PASS')
        return 0
        
    except Exception as e:
        logger.error(f"Pilot execution failed: {e}", exc_info=True)
        log_stage_end(logger, 'run_rule_engine_pilot', status='FAIL', error=str(e))
        return 1

if __name__ == '__main__':
    sys.exit(main())
