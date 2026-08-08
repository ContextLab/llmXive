import csv
import os
import logging
from typing import Dict, Any, List, Optional
from agents.policy_parser import parse_policy_complexity

logger = logging.getLogger(__name__)

CSV_COLUMNS = [
    'run_id',
    'seed',
    'seed_run_id',
    'condition',
    'env_id',
    'score',
    'pre_shift_score',
    'drop_rate',
    'complexity',
    'branch_count'
]

def calculate_drop_rate(pre_shift_score: float, post_shift_score: float) -> float:
    """
    Calculate the performance drop rate.
    Formula: (pre - post) / pre
    Handles division by zero by returning 0.0 if pre is 0.
    """
    if pre_shift_score == 0.0:
        return 0.0
    return (pre_shift_score - post_shift_score) / pre_shift_score

def write_evolution_result(
    result: Dict[str, Any],
    output_path: str
) -> None:
    """
    Append a single evolution result row to the CSV file.
    If the file does not exist, it is created with headers.
    
    Args:
        result: Dictionary containing run metrics. Expected keys:
            run_id, seed, condition, env_id, score, pre_shift_score, policy_path
        output_path: Full path to the CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Calculate derived metrics
    post_shift_score = result.get('post_shift_score')
    pre_shift_score = result.get('pre_shift_score', 0.0)
    
    # Handle missing post-shift score (e.g., if shift didn't happen or failed)
    if post_shift_score is None:
        drop_rate = 0.0
    else:
        drop_rate = calculate_drop_rate(pre_shift_score, post_shift_score)

    # Parse policy complexity if policy_path is provided
    complexity = 0.0
    branch_count = 0
    policy_path = result.get('policy_path')
    
    if policy_path and os.path.exists(policy_path):
        try:
            metrics = parse_policy_complexity(policy_path)
            complexity = metrics.get('cyclomatic_complexity', 0.0)
            branch_count = metrics.get('branch_count', 0)
        except Exception as e:
            logger.warning(f"Failed to parse policy complexity for {policy_path}: {e}")
            complexity = -1.0
            branch_count = -1
    else:
        logger.warning(f"Policy file not found at {policy_path}, setting complexity to -1")
        complexity = -1.0
        branch_count = -1

    # Construct the row
    row = {
        'run_id': result.get('run_id'),
        'seed': result.get('seed'),
        'seed_run_id': f"{result.get('seed')}-{result.get('run_id')}",
        'condition': result.get('condition'),
        'env_id': result.get('env_id'),
        'score': result.get('score'),
        'pre_shift_score': pre_shift_score,
        'drop_rate': drop_rate,
        'complexity': complexity,
        'branch_count': branch_count
    }

    # Check if file exists to determine if we need to write headers
    file_exists = os.path.isfile(output_path)

    with open(output_path, mode='a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    
    logger.info(f"Wrote result for run {row['seed_run_id']} to {output_path}")

def write_evolution_results_batch(
    results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write a batch of evolution results to the CSV file.
    
    Args:
        results: List of dictionaries containing run metrics.
        output_path: Full path to the CSV file.
    """
    for result in results:
        write_evolution_result(result, output_path)
