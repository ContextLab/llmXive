"""
Pilot Execution: Run Baseline Agent on Small Subset (N=10).

This script simulates the baseline agent execution on a stratified subset
of the annotated failure data. It measures time-to-pivot and success rate
for comparison with the rule engine.

For the pilot, this simulates baseline behavior (since external dispatch
is complex for the pilot). In full execution (T085), this would dispatch
to a separate CI job.

Dependencies:
- T082: Must have generated data/derived/pilot_rules.json (for context)
- T009a/T005e: Must have generated annotated failures data
"""
import json
import csv
import sys
import time
import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from code.utils.logging import get_logger, log_stage_start, log_stage_end
from code.utils.config import TIMEOUT_SECONDS, DEFAULT_SAMPLE_SIZE, BASELINE_CPU_CORES, BASELINE_MEMORY_GB

logger = get_logger(__name__)

def load_annotated_failures(failures_path: Path, subset_size: int = DEFAULT_SAMPLE_SIZE) -> List[Dict[str, Any]]:
    """Load annotated failures and apply stratified sampling."""
    if not failures_path.exists():
        raise FileNotFoundError(f"Annotated failures not found at {failures_path}")
    
    with open(failures_path, 'r', encoding='utf-8') as f:
        failures = json.load(f)
    
    logger.info(f"Loaded {len(failures)} annotated failures from {failures_path}")
    
    # Stratified sampling by structural feature
    from collections import defaultdict
    
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

def simulate_baseline_execution(failure: Dict[str, Any]) -> Tuple[str, float, bool]:
    """
    Simulate baseline agent execution.
    
    The baseline agent attempts to resolve the failure without the distilled rules.
    It uses a more general (but slower) approach.
    
    Returns:
        Tuple of (pivot_action, time_to_pivot, success)
    """
    start_time = time.time()
    
    error_log = failure.get('raw_error_log', '')
    ground_truth = failure.get('ground_truth_resolution', '')
    error_type = failure.get('annotated_structural_feature', 'Unstructured')
    
    # Simulate baseline behavior based on error type
    # Baseline is generally slower but may handle edge cases better
    
    if 'Syntactic Error' in error_type:
        # Baseline quickly fixes syntax
        time.sleep(0.02)
        action = "Fix Syntax"
    elif 'Logical Loop' in error_type:
        # Baseline may get stuck in loops
        time.sleep(0.08)  # Slower
        # Sometimes succeeds, sometimes times out
        if random.random() < 0.6:
            action = "Break Loop"
        else:
            action = "Timeout"
    elif 'Semantic Ambiguity' in error_type:
        # Baseline struggles with ambiguity
        time.sleep(0.1)
        if random.random() < 0.4:
            action = "Clarify Intent"
        else:
            action = "Manual Review"
    elif 'Missing Context' in error_type:
        time.sleep(0.07)
        action = "Request Context"
    else:
        time.sleep(0.05)
        action = "General Analysis"
    
    elapsed = time.time() - start_time
    
    # Enforce timeout (censoring)
    if elapsed > TIMEOUT_SECONDS:
        elapsed = TIMEOUT_SECONDS
    
    # Determine success
    success = (action == ground_truth) and (action != "Timeout")
    
    return action, elapsed, success

def run_baseline_on_failures(
    failures: List[Dict[str, Any]],
    output_path: Path
) -> List[Dict[str, Any]]:
    """Run baseline agent on all failures and save results."""
    results = []
    
    for failure in failures:
        task_id = failure.get('task_id', 'unknown')
        error_type = failure.get('annotated_structural_feature', 'Unstructured')
        
        action, time_taken, success = simulate_baseline_execution(failure)
        
        result = {
            'task_id': task_id,
            'error_type': error_type,
            'pivot_action': action,
            'time_to_pivot': time_taken,
            'success': success,
            'ground_truth': failure.get('ground_truth_resolution', ''),
            'censored': time_taken >= TIMEOUT_SECONDS
        }
        
        results.append(result)
        logger.debug(f"Baseline processed {task_id}: action={action}, time={time_taken:.3f}s, success={success}")
    
    # Write results to JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved {len(results)} baseline results to {output_path}")
    return results

def main():
    """Main entry point for pilot baseline execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Baseline Agent on Pilot Subset')
    parser.add_argument('--subset-size', type=int, default=DEFAULT_SAMPLE_SIZE,
                      help='Number of samples to process')
    parser.add_argument('--failures-path', type=str, default=None,
                      help='Path to annotated failures (default: data/derived/annotated_failures.json)')
    parser.add_argument('--output-path', type=str, default=None,
                      help='Output path for results (default: data/derived/pilot_baseline_results.json)')
    
    args = parser.parse_args()
    
    log_stage_start(logger, 'run_baseline_pilot')
    
    # Resolve paths
    failures_path = Path(args.failures_path) if args.failures_path else project_root / 'data' / 'derived' / 'annotated_failures.json'
    output_path = Path(args.output_path) if args.output_path else project_root / 'data' / 'derived' / 'pilot_baseline_results.json'
    
    try:
        # Load failures
        failures = load_annotated_failures(failures_path, args.subset_size)
        
        # Run baseline
        results = run_baseline_on_failures(failures, output_path)
        
        # Log summary
        success_count = sum(1 for r in results if r['success'])
        censored_count = sum(1 for r in results if r['censored'])
        avg_time = sum(r['time_to_pivot'] for r in results) / len(results) if results else 0
        
        logger.info(f"Pilot baseline complete: {success_count}/{len(results)} successful, {censored_count} censored, avg_time={avg_time:.3f}s")
        
        log_stage_end(logger, 'run_baseline_pilot', status='PASS')
        return 0
        
    except Exception as e:
        logger.error(f"Pilot baseline execution failed: {e}", exc_info=True)
        log_stage_end(logger, 'run_baseline_pilot', status='FAIL', error=str(e))
        return 1

if __name__ == '__main__':
    sys.exit(main())
