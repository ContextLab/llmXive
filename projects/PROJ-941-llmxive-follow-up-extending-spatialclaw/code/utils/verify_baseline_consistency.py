"""
Verify Baseline Consistency (T060)

Implements a consistency check for the 3D baseline agent by running it twice
on a random subset of tasks with the same seed to ensure determinism.
"""
import os
import sys
import json
import random
import logging
import argparse
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

# Import from existing project modules
from agents.baseline_3d import run_baseline_on_dataset, solve_task
from data.loader import load_dataset, DataLoadError
from utils.logging import setup_logging

# Constants
SUBSET_SIZE = 10
SEED_BASE = 42
OUTPUT_PATH = "results/analysis/baseline_determinism_report.md"

def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def hash_result(result: Dict[str, Any]) -> str:
    """Create a deterministic hash of a result dictionary."""
    # Sort keys to ensure consistent hashing regardless of dict order
    serialized = json.dumps(result, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()

def run_baseline_on_task(task_instance: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """
    Run the baseline agent on a single task instance with a specific seed.
    
    Args:
        task_instance: The task data dictionary
        seed: The random seed to use for this run
        
    Returns:
        Dictionary containing the result of the baseline execution
    """
    # Set seed for reproducibility
    random.seed(seed)
    
    # Extract task details
    task_id = task_instance.get('task_id', 'unknown')
    task_type = task_instance.get('task_type', 'unknown')
    ground_truth = task_instance.get('ground_truth_3d_params', {})
    
    # Run the baseline solver
    try:
        result = solve_task(task_type, ground_truth, seed)
        return {
            'task_id': task_id,
            'task_type': task_type,
            'success': result.get('success', False),
            'latency_ms': result.get('latency_ms', 0.0),
            'result_hash': hash_result(result),
            'details': result
        }
    except Exception as e:
        logging.error(f"Baseline failed on task {task_id}: {e}")
        return {
            'task_id': task_id,
            'task_type': task_type,
            'success': False,
            'latency_ms': 0.0,
            'result_hash': 'error',
            'details': str(e)
        }

def verify_consistency(run1_results: List[Dict[str, Any]], 
                     run2_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compare two runs of the baseline on the same tasks to verify determinism.
    
    Args:
        run1_results: Results from the first run
        run2_results: Results from the second run
        
    Returns:
        Dictionary containing consistency analysis results
    """
    if len(run1_results) != len(run2_results):
        return {
            'consistent': False,
            'reason': 'Different number of results between runs',
            'run1_count': len(run1_results),
            'run2_count': len(run2_results)
        }
    
    inconsistencies = []
    total_variance = 0.0
    total_tasks = len(run1_results)
    
    for i, (res1, res2) in enumerate(zip(run1_results, run2_results)):
        task_id = res1['task_id']
        
        # Check success status
        if res1['success'] != res2['success']:
            inconsistencies.append({
                'task_id': task_id,
                'issue': 'Success status mismatch',
                'run1': res1['success'],
                'run2': res2['success']
            })
        
        # Check result hash (should be identical for deterministic runs)
        if res1['result_hash'] != res2['result_hash']:
            inconsistencies.append({
                'task_id': task_id,
                'issue': 'Result hash mismatch',
                'run1_hash': res1['result_hash'],
                'run2_hash': res2['result_hash']
            })
        
        # Calculate latency variance (allow small floating point differences)
        latency_diff = abs(res1['latency_ms'] - res2['latency_ms'])
        total_variance += latency_diff
        
        # Check if latency difference is negligible (< 1ms tolerance)
        if latency_diff > 1.0:
            inconsistencies.append({
                'task_id': task_id,
                'issue': 'Latency variance exceeds threshold',
                'run1_latency': res1['latency_ms'],
                'run2_latency': res2['latency_ms'],
                'diff_ms': latency_diff
            })
    
    avg_variance = total_variance / total_tasks if total_tasks > 0 else 0.0
    is_consistent = len(inconsistencies) == 0
    
    return {
        'consistent': is_consistent,
        'total_tasks': total_tasks,
        'inconsistency_count': len(inconsistencies),
        'inconsistencies': inconsistencies,
        'average_latency_variance_ms': avg_variance,
        'max_variance_ms': max([abs(r1['latency_ms'] - r2['latency_ms']) 
                               for r1, r2 in zip(run1_results, run2_results)]) if run1_results else 0.0
    }

def generate_report(consistency_results: Dict[str, Any], 
                   run1_results: List[Dict[str, Any]],
                   run2_results: List[Dict[str, Any]],
                   subset_task_ids: List[str]) -> str:
    """
    Generate a markdown report of the baseline determinism verification.
    
    Args:
        consistency_results: The results from verify_consistency
        run1_results: Results from first run
        run2_results: Results from second run
        subset_task_ids: The task IDs that were tested
        
    Returns:
        Markdown formatted report string
    """
    report_lines = [
        "# Baseline Determinism Verification Report",
        "",
        f"**Generated**: {datetime.now().isoformat()}",
        f"**Subset Size**: {len(subset_task_ids)} tasks",
        f"**Random Seed Base**: {SEED_BASE}",
        "",
        "## Summary",
        "",
        f"- **Consistency Status**: {'✅ PASS' if consistency_results['consistent'] else '❌ FAIL'}",
        f"- **Total Tasks Tested**: {consistency_results['total_tasks']}",
        f"- **Inconsistencies Found**: {consistency_results['inconsistency_count']}",
        f"- **Average Latency Variance**: {consistency_results['average_latency_variance_ms']:.4f} ms",
        f"- **Maximum Latency Variance**: {consistency_results['max_variance_ms']:.4f} ms",
        ""
    ]
    
    if consistency_results['consistent']:
        report_lines.extend([
            "### Conclusion",
            "",
            "The 3D baseline agent demonstrates **deterministic behavior** across both runs.",
            "All task results (success status, computed values, and hashes) are identical.",
            "Latency variations are within acceptable floating-point tolerance (< 1ms).",
            "",
            "The baseline can be safely used for paired comparisons without introducing",
            "variance that would confound the 2D vs 3D performance analysis.",
            ""
        ])
    else:
        report_lines.extend([
            "### Issues Detected",
            "",
            "The baseline agent exhibited non-deterministic behavior in the following cases:",
            ""
        ])
        
        for idx, issue in enumerate(consistency_results['inconsistencies'], 1):
            report_lines.append(f"{idx}. **Task {issue['task_id']}**: {issue['issue']}")
            if 'run1' in issue:
                report_lines.append(f"   - Run 1: {issue['run1']}")
            if 'run2' in issue:
                report_lines.append(f"   - Run 2: {issue['run2']}")
            if 'diff_ms' in issue:
                report_lines.append(f"   - Latency difference: {issue['diff_ms']:.4f} ms")
            report_lines.append("")
        
        report_lines.extend([
            "### Conclusion",
            "",
            "⚠️ **WARNING**: The baseline agent is NOT fully deterministic.",
            "This may confound the paired comparison analysis. Investigate the",
            "root cause of non-determinism before proceeding to T047.",
            ""
        ])
    
    report_lines.extend([
        "## Tested Task IDs",
        ""
    ])
    for task_id in subset_task_ids:
        report_lines.append(f"- `{task_id}`")
    
    report_lines.extend([
        "",
        "## Run Details",
        "",
        "### Run 1 Summary",
        ""
    ])
    
    run1_success = sum(1 for r in run1_results if r['success'])
    run1_avg_latency = sum(r['latency_ms'] for r in run1_results) / len(run1_results) if run1_results else 0
    
    report_lines.extend([
        f"- **Success Rate**: {run1_success}/{len(run1_results)} ({100*run1_success/len(run1_results):.1f}%)",
        f"- **Average Latency**: {run1_avg_latency:.2f} ms",
        "",
        "### Run 2 Summary",
        ""
    ])
    
    run2_success = sum(1 for r in run2_results if r['success'])
    run2_avg_latency = sum(r['latency_ms'] for r in run2_results) / len(run2_results) if run2_results else 0
    
    report_lines.extend([
        f"- **Success Rate**: {run2_success}/{len(run2_results)} ({100*run2_success/len(run2_results):.1f}%)",
        f"- **Average Latency**: {run2_avg_latency:.2f} ms",
        ""
    ])
    
    return "\n".join(report_lines)

def main():
    """Main entry point for baseline consistency verification."""
    parser = argparse.ArgumentParser(description="Verify baseline agent determinism")
    parser.add_argument("--dataset", type=str, default="data/raw/synthetic_spatialclaw_v1.json",
                      help="Path to the dataset file")
    parser.add_argument("--subset-size", type=int, default=SUBSET_SIZE,
                      help="Number of tasks to test")
    parser.add_argument("--seed", type=int, default=SEED_BASE,
                      help="Base seed for random selection")
    parser.add_argument("--output", type=str, default=OUTPUT_PATH,
                      help="Output path for the report")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting baseline consistency verification")
    logger.info(f"Dataset: {args.dataset}")
    logger.info(f"Subset size: {args.subset_size}")
    logger.info(f"Seed: {args.seed}")
    
    # Load dataset
    try:
        dataset = load_dataset(args.dataset)
        logger.info(f"Loaded {len(dataset)} tasks from dataset")
    except DataLoadError as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
    
    if len(dataset) < args.subset_size:
        logger.error(f"Dataset has {len(dataset)} tasks, but requested subset size is {args.subset_size}")
        sys.exit(1)
    
    # Select random subset
    random.seed(args.seed)
    subset_indices = random.sample(range(len(dataset)), args.subset_size)
    subset_tasks = [dataset[i] for i in subset_indices]
    subset_task_ids = [t['task_id'] for t in subset_tasks]
    
    logger.info(f"Selected {len(subset_tasks)} tasks for testing")
    
    # Run baseline twice on the same subset with the same seed
    run1_results = []
    run2_results = []
    
    # Run 1
    logger.info("Executing Run 1...")
    for i, task in enumerate(subset_tasks):
        task_seed = args.seed + i
        result = run_baseline_on_task(task, task_seed)
        run1_results.append(result)
        logger.debug(f"Run 1 - Task {i+1}/{len(subset_tasks)}: {result['task_id']} -> success={result['success']}")
    
    # Run 2 (same seed, same tasks)
    logger.info("Executing Run 2...")
    for i, task in enumerate(subset_tasks):
        task_seed = args.seed + i  # Same seed as run 1
        result = run_baseline_on_task(task, task_seed)
        run2_results.append(result)
        logger.debug(f"Run 2 - Task {i+1}/{len(subset_tasks)}: {result['task_id']} -> success={result['success']}")
    
    # Verify consistency
    logger.info("Comparing results...")
    consistency_results = verify_consistency(run1_results, run2_results)
    
    # Generate report
    report = generate_report(consistency_results, run1_results, run2_results, subset_task_ids)
    
    # Write report to file
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Report written to {args.output}")
    
    # Print summary to stdout
    if consistency_results['consistent']:
        print("✅ Baseline determinism check PASSED")
        print(f"   - {consistency_results['total_tasks']} tasks tested")
        print(f"   - Average latency variance: {consistency_results['average_latency_variance_ms']:.4f} ms")
    else:
        print("❌ Baseline determinism check FAILED")
        print(f"   - {consistency_results['inconsistency_count']} inconsistencies found")
        print(f"   - Max latency variance: {consistency_results['max_variance_ms']:.4f} ms")
    
    # Exit with appropriate code
    sys.exit(0 if consistency_results['consistent'] else 1)

if __name__ == "__main__":
    main()
