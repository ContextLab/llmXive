"""
Metrics calculation utilities for OPID routing complexity analysis.

Provides functions for calculating success rates, entropy measures,
log-probability shifts, and distillation cost-benefit ratios.
"""
import math
import csv
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SuccessRateResult:
    """Container for success rate calculation results."""
    total_episodes: int
    successful_episodes: int
    success_rate: float
    tier: str
    threshold: float


def calculate_success_rate(
    episode_results: List[Dict[str, Any]],
    tier: Optional[str] = None,
    threshold: Optional[float] = None
) -> SuccessRateResult:
    """
    Calculate the success rate as the percentage of episodes that traversed
    the ground-truth path.
    
    Args:
        episode_results: List of episode result dictionaries. Each dictionary
            must contain a 'succeeded' key (bool) indicating whether the
            episode successfully traversed the ground-truth path.
            Optional: 'tier' and 'threshold' keys for filtering.
        tier: Optional tier filter (e.g., 'Tier1', 'Tier2', 'Tier3').
            If provided, only episodes from this tier are included.
        threshold: Optional threshold filter (float). If provided, only
            episodes with this threshold value are included.
    
    Returns:
        SuccessRateResult containing:
            - total_episodes: Number of episodes in the filtered set
            - successful_episodes: Number of successful episodes
            - success_rate: Ratio of successful to total episodes (0.0 to 1.0)
            - tier: The tier used (or 'All' if not filtered)
            - threshold: The threshold used (or 'All' if not filtered)
    
    Raises:
        ValueError: If episode_results is empty or lacks required 'succeeded' key
        TypeError: If 'succeeded' values are not boolean
    """
    if not episode_results:
        raise ValueError("episode_results cannot be empty")
    
    # Filter by tier and threshold if specified
    filtered_results = episode_results
    
    if tier is not None:
        filtered_results = [
            r for r in filtered_results
            if r.get('tier') == tier
        ]
    
    if threshold is not None:
        filtered_results = [
            r for r in filtered_results
            if abs(r.get('threshold', -1) - threshold) < 1e-6
        ]
    
    if not filtered_results:
        raise ValueError(
            f"No episodes found matching tier={tier}, threshold={threshold}"
        )
    
    # Validate and count successes
    successful_count = 0
    for i, result in enumerate(filtered_results):
        if 'succeeded' not in result:
            raise ValueError(
                f"Episode result at index {i} missing required 'succeeded' key"
            )
        
        if not isinstance(result['succeeded'], bool):
            raise TypeError(
                f"Episode result 'succeeded' must be boolean, got {type(result['succeeded'])}"
            )
        
        if result['succeeded']:
            successful_count += 1
    
    total_count = len(filtered_results)
    success_rate = successful_count / total_count if total_count > 0 else 0.0
    
    return SuccessRateResult(
        total_episodes=total_count,
        successful_episodes=successful_count,
        success_rate=success_rate,
        tier=tier if tier is not None else "All",
        threshold=threshold if threshold is not None else 0.0
    )


def calculate_raw_entropy(probabilities: List[float]) -> float:
    """
    Calculate raw Shannon entropy from a probability distribution.
    
    Args:
        probabilities: List of probabilities that sum to 1.0
    
    Returns:
        Shannon entropy value (non-negative float)
    """
    if not probabilities:
        return 0.0
    
    # Filter out zero probabilities to avoid log(0)
    valid_probs = [p for p in probabilities if p > 0]
    
    if not valid_probs:
        return 0.0
    
    entropy = 0.0
    for p in valid_probs:
        if p > 0:
            entropy -= p * math.log2(p)
    
    return entropy


def calculate_mean_entropy(entropy_values: List[float]) -> float:
    """
    Calculate the mean of a list of entropy values.
    
    Args:
        entropy_values: List of entropy values (floats)
    
    Returns:
        Mean entropy value
    """
    if not entropy_values:
        return 0.0
    
    return sum(entropy_values) / len(entropy_values)


def calculate_variance(values: List[float]) -> float:
    """
    Calculate the population variance of a list of values.
    
    Args:
        values: List of numeric values
    
    Returns:
        Population variance (float)
    """
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    
    return variance


def calculate_mean_log_prob_shift(
    episode_results: List[Dict[str, Any]]
) -> float:
    """
    Calculate the mean log-probability shift across episodes.
    
    This measures how much the policy's log-probability changed due to
    skill injection signals.
    
    Args:
        episode_results: List of episode result dictionaries. Each must
            contain a 'log_prob_shift' key (float) representing the
            log-probability shift for that episode.
    
    Returns:
        Mean log-probability shift across all episodes (float)
    
    Raises:
        ValueError: If episode_results is empty or lacks required keys
    """
    if not episode_results:
        raise ValueError("episode_results cannot be empty")
    
    shift_values = []
    for i, result in enumerate(episode_results):
        if 'log_prob_shift' not in result:
            raise ValueError(
                f"Episode result at index {i} missing required 'log_prob_shift' key"
            )
        shift_values.append(float(result['log_prob_shift']))
    
    return sum(shift_values) / len(shift_values) if shift_values else 0.0


def calculate_distillation_cost_benefit_ratio(
    mean_log_prob_shift: float,
    success_rate_improvement: float
) -> Dict[str, float]:
    """
    Calculate the distillation cost-benefit ratio.
    
    This ratio measures the efficiency of skill injection: how much
    log-probability shift (cost) is required per unit of success rate
    improvement (benefit).
    
    Args:
        mean_log_prob_shift: Mean log-probability shift across episodes
        success_rate_improvement: Improvement in success rate (baseline to current)
    
    Returns:
        Dictionary containing:
            - cost_benefit_ratio: Ratio of mean_log_prob_shift to success_rate_improvement
            - mean_log_prob_shift: The input mean log-probability shift
            - success_rate_improvement: The input success rate improvement
    
    Raises:
        ValueError: If success_rate_improvement is zero or negative
    """
    if success_rate_improvement <= 0:
        raise ValueError(
            f"success_rate_improvement must be positive, got {success_rate_improvement}"
        )
    
    if mean_log_prob_shift == 0:
        # No cost, infinite benefit efficiency
        ratio = float('inf')
    else:
        ratio = abs(mean_log_prob_shift) / success_rate_improvement
    
    return {
        'cost_benefit_ratio': ratio,
        'mean_log_prob_shift': mean_log_prob_shift,
        'success_rate_improvement': success_rate_improvement
    }


def aggregate_success_rates_by_tier_threshold(
    episode_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Aggregate success rates grouped by (tier, threshold) combinations.
    
    Args:
        episode_results: List of episode result dictionaries containing
            'tier', 'threshold', and 'succeeded' keys
    
    Returns:
        List of dictionaries with aggregated success rates:
            - tier: Tier identifier
            - threshold: Threshold value
            - total_episodes: Total episodes in this group
            - successful_episodes: Successful episodes in this group
            - success_rate: Calculated success rate
    """
    if not episode_results:
        return []
    
    # Group by (tier, threshold)
    groups: Dict[Tuple[str, float], List[Dict[str, Any]]] = {}
    
    for result in episode_results:
        tier = result.get('tier', 'Unknown')
        threshold = result.get('threshold', 0.0)
        key = (tier, threshold)
        
        if key not in groups:
            groups[key] = []
        groups[key].append(result)
    
    # Calculate success rates for each group
    aggregated = []
    for (tier, threshold), group_results in sorted(groups.items()):
        success_result = calculate_success_rate(group_results)
        aggregated.append({
            'tier': success_result.tier,
            'threshold': success_result.threshold,
            'total_episodes': success_result.total_episodes,
            'successful_episodes': success_result.successful_episodes,
            'success_rate': success_result.success_rate
        })
    
    return aggregated


def write_success_rate_summary(
    aggregated_results: List[Dict[str, Any]],
    output_path: str
) -> None:
    """
    Write aggregated success rate results to a CSV file.
    
    Args:
        aggregated_results: List of aggregated success rate dictionaries
        output_path: Path to output CSV file
    """
    if not aggregated_results:
        logger.warning("No aggregated results to write")
        return
    
    fieldnames = [
        'tier', 'threshold', 'total_episodes',
        'successful_episodes', 'success_rate'
    ]
    
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aggregated_results)
    
    logger.info(f"Success rate summary written to {output_path}")