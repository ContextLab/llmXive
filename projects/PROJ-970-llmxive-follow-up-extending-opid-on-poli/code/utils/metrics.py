import csv
import hashlib
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class SuccessRateResult:
    def __init__(self, success: bool, steps: int, path_length: int):
        self.success = success
        self.steps = steps
        self.path_length = path_length

def calculate_success_rate(trajectory: List[Any], ground_truth: List[Any]) -> SuccessRateResult:
    if not trajectory or not ground_truth:
        return SuccessRateResult(False, 0, 0)
    
    success = trajectory == ground_truth
    steps = len(trajectory)
    path_length = len(ground_truth)
    
    return SuccessRateResult(success, steps, path_length)

def calculate_action_entropy(actions: List[float]) -> float:
    if not actions:
        return 0.0
    
    total = sum(actions)
    if total == 0:
        return 0.0
    
    probs = [a / total for a in actions]
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * math.log(p)
    
    return entropy

def calculate_checksum(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def calculate_raw_entropy(values: List[float]) -> float:
    if not values:
        return 0.0
    
    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    if variance <= 0:
        return 0.0
    
    return 0.5 * math.log(2 * math.pi * math.e * variance)

def calculate_mean_entropy(entropy_values: List[float]) -> float:
    if not entropy_values:
        return 0.0
    return sum(entropy_values) / len(entropy_values)

def calculate_variance(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    
    mean_val = sum(values) / len(values)
    variance = sum((x - mean_val) ** 2 for x in values) / len(values)
    return variance

def calculate_mean_log_prob_shift(shifts: List[float]) -> float:
    if not shifts:
        return 0.0
    return sum(shifts) / len(shifts)

def calculate_distillation_cost_benefit_ratio(
    mean_log_prob_shift: float,
    success_rate_held_out: float,
    baseline_success_rate: float
) -> float:
    denominator = success_rate_held_out - baseline_success_rate
    if denominator == 0:
        return float('inf') if mean_log_prob_shift != 0 else 0.0
    return mean_log_prob_shift / denominator

def aggregate_success_rates_by_tier_threshold(
    results: List[Dict[str, Any]]
) -> Dict[Tuple[int, float], List[bool]]:
    aggregated: Dict[Tuple[int, float], List[bool]] = {}
    for r in results:
        tier = r.get('tier')
        threshold = r.get('threshold')
        success = r.get('success', False)
        key = (tier, threshold)
        if key not in aggregated:
            aggregated[key] = []
        aggregated[key].append(success)
    return aggregated

def write_success_rate_summary(
    aggregated: Dict[Tuple[int, float], List[bool]],
    output_path: str
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['tier', 'threshold', 'total_episodes', 'successes', 'success_rate'])
        for (tier, threshold), successes in sorted(aggregated.items()):
            total = len(successes)
            succ_count = sum(successes)
            rate = succ_count / total if total > 0 else 0.0
            writer.writerow([tier, threshold, total, succ_count, rate])

def log_data_hygiene(file_paths: List[str], output_path: str) -> Dict[str, str]:
    """
    Record file checksums for data hygiene verification (Const III).
    
    Args:
        file_paths: List of file paths to checksum
        output_path: Path to write the checksum report (JSON)
    
    Returns:
        Dictionary mapping file paths to their SHA-256 checksums
    """
    checksums: Dict[str, str] = {}
    
    for file_path in file_paths:
        if not os.path.exists(file_path):
            logger.warning(f"File not found for checksum: {file_path}")
            checksums[file_path] = "FILE_NOT_FOUND"
            continue
        
        try:
            checksum = calculate_checksum(file_path)
            checksums[file_path] = checksum
            logger.info(f"Checksum recorded for {file_path}: {checksum}")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {file_path}: {e}")
            checksums[file_path] = f"ERROR: {str(e)}"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    import json
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    logger.info(f"Data hygiene checksums written to {output_path}")
    return checksums