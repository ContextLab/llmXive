import csv
import hashlib
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from config import get_seed

logger = logging.getLogger(__name__)

class SuccessRateResult:
    def __init__(self, success_count: int, total_count: int, rate: float):
        self.success_count = success_count
        self.total_count = total_count
        self.rate = rate

def calculate_success_rate(trajectory: List[int], ground_truth: List[int]) -> SuccessRateResult:
    """
    Calculate the success rate of a trajectory against a ground truth path.
    
    Args:
        trajectory: List of node IDs visited by the agent
        ground_truth: List of node IDs representing the optimal path
        
    Returns:
        SuccessRateResult object containing counts and rate
    """
    if not ground_truth:
        return SuccessRateResult(0, 1, 0.0)
        
    # Check if trajectory contains the full ground truth path as a subsequence
    success = False
    if len(trajectory) >= len(ground_truth):
        # Simple subsequence check
        it = iter(trajectory)
        success = all(node in it for node in ground_truth)
    
    return SuccessRateResult(1 if success else 0, 1, 1.0 if success else 0.0)

def calculate_action_entropy(actions: List[int]) -> float:
    """
    Calculate the entropy of a sequence of actions.
    
    Args:
        actions: List of action IDs taken by the agent
        
    Returns:
        Entropy value (float)
    """
    if not actions:
        return 0.0
        
    # Count occurrences of each action
    action_counts: Dict[int, int] = {}
    for action in actions:
        action_counts[action] = action_counts.get(action, 0) + 1
    
    total = len(actions)
    entropy = 0.0
    
    for count in action_counts.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log(p)
    
    return entropy

def calculate_checksum(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hex string of the SHA-256 hash
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def calculate_raw_entropy(probabilities: List[float]) -> float:
    """
    Calculate entropy from a list of probabilities.
    
    Args:
        probabilities: List of probability values that sum to 1.0
        
    Returns:
        Entropy value (float)
    """
    if not probabilities:
        return 0.0
        
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log(p)
    
    return entropy

def calculate_mean_entropy(entropy_values: List[float]) -> float:
    """
    Calculate the mean of a list of entropy values.
    
    Args:
        entropy_values: List of entropy values
        
    Returns:
        Mean entropy (float)
    """
    if not entropy_values:
        return 0.0
    return sum(entropy_values) / len(entropy_values)

def calculate_variance(values: List[float]) -> float:
    """
    Calculate the variance of a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Variance (float)
    """
    if len(values) < 2:
        return 0.0
        
    mean = sum(values) / len(values)
    squared_diffs = [(x - mean) ** 2 for x in values]
    return sum(squared_diffs) / len(values)

def calculate_mean_log_prob_shift(shifts: List[float]) -> float:
    """
    Calculate the mean of log-probability shifts.
    
    Args:
        shifts: List of log-probability shift values
        
    Returns:
        Mean shift (float)
    """
    if not shifts:
        return 0.0
    return sum(shifts) / len(shifts)

def calculate_distillation_cost_benefit_ratio(
    mean_log_prob_shift: float,
    success_rate_full: float,
    baseline_success_rate: float
) -> float:
    """
    Calculate the distillation cost-benefit ratio.
    
    Args:
        mean_log_prob_shift: Average log-probability shift
        success_rate_full: Success rate across all episodes
        baseline_success_rate: Success rate at threshold=1.0 (no injection)
        
    Returns:
        Cost-benefit ratio (float)
    """
    delta_success = success_rate_full - baseline_success_rate
    if abs(delta_success) < 1e-9:
        return float('inf') if mean_log_prob_shift != 0 else 0.0
    return mean_log_prob_shift / delta_success

def aggregate_success_rates_by_tier_threshold(
    results: List[Dict[str, Any]]
) -> Dict[Tuple[int, float], SuccessRateResult]:
    """
    Aggregate success rates by tier and threshold.
    
    Args:
        results: List of episode result dictionaries
        
    Returns:
        Dictionary mapping (tier, threshold) to SuccessRateResult
    """
    aggregated: Dict[Tuple[int, float], Dict[str, int]] = {}
    
    for result in results:
        tier = result.get('tier', 0)
        threshold = float(result.get('threshold', 1.0))
        success = 1 if result.get('success', False) else 0
        
        key = (tier, threshold)
        if key not in aggregated:
            aggregated[key] = {'success_count': 0, 'total_count': 0}
        
        aggregated[key]['success_count'] += success
        aggregated[key]['total_count'] += 1
    
    return {
        key: SuccessRateResult(
            data['success_count'],
            data['total_count'],
            data['success_count'] / data['total_count'] if data['total_count'] > 0 else 0.0
        )
        for key, data in aggregated.items()
    }

def write_success_rate_summary(
    aggregated: Dict[Tuple[int, float], SuccessRateResult],
    output_path: str
) -> None:
    """
    Write success rate summary to a CSV file.
    
    Args:
        aggregated: Dictionary of aggregated success rates
        output_path: Path to output CSV file
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tier', 'threshold', 'success_count', 'total_count', 'success_rate'])
        
        for (tier, threshold), result in sorted(aggregated.items()):
            writer.writerow([
                tier,
                f"{threshold:.1f}",
                result.success_count,
                result.total_count,
                f"{result.rate:.6f}"
            ])

def log_data_hygiene(file_paths: List[str], output_path: str) -> None:
    """
    Record file checksums for data hygiene verification (Const III).
    
    This function computes SHA-256 checksums for all provided files and writes
    them to a JSON file for later verification of data integrity.
    
    Args:
        file_paths: List of file paths to checksum
        output_path: Path to the output JSON file for storing checksums
        
    Raises:
        FileNotFoundError: If any of the input files do not exist
        RuntimeError: If checksum calculation fails for any file
    """
    if not file_paths:
        logger.warning("No file paths provided for data hygiene logging")
        checksums = {}
    else:
        checksums = {}
        for file_path in file_paths:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found for checksum: {file_path}")
            
            try:
                checksum = calculate_checksum(file_path)
                checksums[file_path] = checksum
                logger.info(f"Checksum recorded for {file_path}: {checksum}")
            except Exception as e:
                raise RuntimeError(f"Failed to calculate checksum for {file_path}: {e}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Write checksums to JSON file
    import json
    metadata = {
        "seed": get_seed(),
        "files": checksums,
        "checksum_count": len(checksums)
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Data hygiene log written to {output_path} with {len(checksums)} entries")