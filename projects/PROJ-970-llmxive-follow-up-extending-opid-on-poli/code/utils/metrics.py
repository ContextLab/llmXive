import math
import csv
import logging
import hashlib
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SuccessRateResult:
    success_count: int
    total_count: int
    rate: float

def calculate_success_rate(trajectory: List[Dict[str, Any]], ground_truth: List[str]) -> SuccessRateResult:
    """
    Calculate the success rate of a trajectory against a ground truth path.
    
    Args:
        trajectory: List of step dictionaries containing 'node_id' keys.
        ground_truth: List of node IDs representing the correct path.
    
    Returns:
        SuccessRateResult with counts and calculated rate.
    """
    if not trajectory or not ground_truth:
        return SuccessRateResult(success_count=0, total_count=0, rate=0.0)
    
    trajectory_nodes = [step.get('node_id') for step in trajectory if 'node_id' in step]
    total_count = len(ground_truth)
    success_count = 0
    
    # Check if the trajectory matches the ground truth path
    # Allow for some flexibility: trajectory must contain the ground truth sequence
    # For strict matching, we check if the first N nodes of trajectory match ground_truth
    if len(trajectory_nodes) >= total_count:
        if trajectory_nodes[:total_count] == ground_truth:
            success_count = total_count
        elif trajectory_nodes == ground_truth:
            success_count = total_count
    
    # Alternative: check if ground truth is a subsequence
    if success_count == 0 and len(trajectory_nodes) >= total_count:
        idx = 0
        for node in trajectory_nodes:
            if idx < total_count and node == ground_truth[idx]:
                idx += 1
        if idx == total_count:
            success_count = total_count
    
    rate = success_count / total_count if total_count > 0 else 0.0
    return SuccessRateResult(success_count=success_count, total_count=total_count, rate=rate)

def calculate_action_entropy(actions: List[Any], probabilities: Optional[List[float]] = None) -> float:
    """
    Calculate the entropy of a set of actions.
    
    Args:
        actions: List of actions taken.
        probabilities: Optional list of probabilities for each action.
                       If None, assumes uniform distribution over unique actions.
    
    Returns:
        Entropy value in bits.
    """
    if not actions:
        return 0.0
    
    if probabilities is not None:
        if len(probabilities) != len(actions):
            raise ValueError("Probabilities length must match actions length")
        entropy = 0.0
        for p in probabilities:
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy
    
    # Calculate empirical entropy from action counts
    counts: Dict[Any, int] = {}
    for action in actions:
        counts[action] = counts.get(action, 0) + 1
    
    total = len(actions)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy

def calculate_checksum(file_path: str) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal checksum string.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def calculate_raw_entropy(values: List[float]) -> float:
    """
    Calculate the Shannon entropy of a list of probability values.
    
    Args:
        values: List of probability values (should sum to 1).
    
    Returns:
        Entropy value.
    """
    if not values:
        return 0.0
    
    entropy = 0.0
    for v in values:
        if v > 0:
            entropy -= v * math.log2(v)
    return entropy

def calculate_mean_entropy(entropy_values: List[float]) -> float:
    """
    Calculate the mean of a list of entropy values.
    
    Args:
        entropy_values: List of entropy values.
    
    Returns:
        Mean entropy.
    """
    if not entropy_values:
        return 0.0
    return sum(entropy_values) / len(entropy_values)

def calculate_variance(values: List[float]) -> float:
    """
    Calculate the variance of a list of values.
    
    Args:
        values: List of numerical values.
    
    Returns:
        Variance.
    """
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    squared_diffs = [(x - mean) ** 2 for x in values]
    return sum(squared_diffs) / len(values)

def calculate_mean_log_prob_shift(log_prob_shifts: List[float]) -> float:
    """
    Calculate the mean of log-probability shifts.
    
    Args:
        log_prob_shifts: List of log-probability shift values.
    
    Returns:
        Mean shift value.
    """
    if not log_prob_shifts:
        return 0.0
    return sum(log_prob_shifts) / len(log_prob_shifts)

def calculate_distillation_cost_benefit_ratio(
    mean_log_prob_shift: float,
    baseline_success_rate: float,
    improved_success_rate: float
) -> float:
    """
    Calculate the distillation cost-benefit ratio.
    
    Cost = mean log-prob shift (effort to inject skill)
    Benefit = improvement in success rate
    
    Args:
        mean_log_prob_shift: Mean log-probability shift from injection.
        baseline_success_rate: Success rate at threshold=0.0 (baseline).
        improved_success_rate: Success rate at current threshold.
    
    Returns:
        Cost-benefit ratio.
    """
    benefit = improved_success_rate - baseline_success_rate
    if benefit <= 0:
        return float('inf') if mean_log_prob_shift > 0 else 0.0
    return mean_log_prob_shift / benefit

def aggregate_success_rates_by_tier_threshold(
    episode_results: List[Dict[str, Any]]
) -> Dict[Tuple[int, float], Dict[str, Any]]:
    """
    Aggregate episode results by tier and threshold.
    
    Args:
        episode_results: List of episode result dictionaries.
    
    Returns:
        Dictionary mapping (tier, threshold) to aggregated stats.
    """
    aggregated: Dict[Tuple[int, float], Dict[str, Any]] = {}
    
    for result in episode_results:
        tier = result.get('tier', 0)
        threshold = result.get('threshold', 0.0)
        key = (tier, threshold)
        
        if key not in aggregated:
            aggregated[key] = {
                'success_count': 0,
                'total_count': 0,
                'entropy_values': [],
                'log_prob_shifts': []
            }
        
        aggregated[key]['total_count'] += 1
        if result.get('success', False):
            aggregated[key]['success_count'] += 1
        
        if 'entropy' in result:
            aggregated[key]['entropy_values'].append(result['entropy'])
        if 'log_prob_shift' in result:
            aggregated[key]['log_prob_shifts'].append(result['log_prob_shift'])
    
    # Calculate rates
    for key, stats in aggregated.items():
        stats['success_rate'] = (
            stats['success_count'] / stats['total_count']
            if stats['total_count'] > 0 else 0.0
        )
        stats['mean_entropy'] = calculate_mean_entropy(stats['entropy_values'])
        stats['mean_log_prob_shift'] = calculate_mean_log_prob_shift(stats['log_prob_shifts'])
        stats['entropy_variance'] = calculate_variance(stats['entropy_values'])
    
    return aggregated

def write_success_rate_summary(
    aggregated_data: Dict[Tuple[int, float], Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write aggregated success rate summary to a CSV file.
    
    Args:
        aggregated_data: Aggregated data from aggregate_success_rates_by_tier_threshold.
        output_path: Path to output CSV file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'tier', 'threshold', 'success_count', 'total_count',
            'success_rate', 'mean_entropy', 'mean_log_prob_shift', 'entropy_variance'
        ])
        
        for (tier, threshold), stats in sorted(aggregated_data.items()):
            writer.writerow([
                tier,
                threshold,
                stats['success_count'],
                stats['total_count'],
                stats['success_rate'],
                stats['mean_entropy'],
                stats['mean_log_prob_shift'],
                stats['entropy_variance']
            ])
    
    logger.info(f"Success rate summary written to {output_path}")

def log_data_hygiene(file_paths: List[str], output_path: str) -> Dict[str, str]:
    """
    Record file checksums for data hygiene and reproducibility (Const III).
    
    This function computes SHA-256 checksums for a list of files and writes
    them to a CSV log file. This ensures data integrity and reproducibility
    by allowing verification that input files have not been modified.
    
    Args:
        file_paths: List of file paths to checksum.
        output_path: Path to the output CSV log file.
    
    Returns:
        Dictionary mapping file paths to their checksums.
    
    Raises:
        FileNotFoundError: If any specified file does not exist.
        ValueError: If file_paths is empty.
    """
    if not file_paths:
        raise ValueError("file_paths cannot be empty")
    
    checksums: Dict[str, str] = {}
    
    logger.info(f"Computing checksums for {len(file_paths)} files...")
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found for checksum: {file_path}")
        
        checksum = calculate_checksum(file_path)
        checksums[file_path] = checksum
        logger.debug(f"Checksum for {file_path}: {checksum}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write checksums to CSV
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['file_path', 'sha256_checksum'])
        for file_path, checksum in checksums.items():
            writer.writerow([file_path, checksum])
    
    logger.info(f"Data hygiene log written to {output_path}")
    return checksums