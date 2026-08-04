import logging
import random
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import os
import csv

from config import RESULTS_DIR, SEED, PERMUTATION_COUNT
from metrics import ndcg_at_k, average_precision
from p_values import calculate_p_value

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def bootstrap_resample_indices(n: int, rng: Optional[random.Random] = None) -> List[int]:
    """
    Generate bootstrap resample indices of size n.
    """
    if rng is None:
        rng = random.Random(SEED)
    return [rng.randint(0, n - 1) for _ in range(n)]

def swap_top_k_relevance(relevance_labels: List[int], k: int, swap_magnitude: float, rng: Optional[random.Random] = None) -> List[int]:
    """
    Simulate alternative hypothesis by swapping top-k positions.
    
    Args:
        relevance_labels: List of relevance scores.
        k: Number of top positions to consider for swapping.
        swap_magnitude: Magnitude of the shift (0.0 to 1.0).
        rng: Random number generator.
        
    Returns:
        Modified relevance labels with swapped top-k positions.
    """
    if rng is None:
        rng = random.Random(SEED)
    
    new_labels = relevance_labels.copy()
    if len(new_labels) == 0 or k <= 0:
        return new_labels
    
    # Identify top-k positions based on current relevance
    # We want to swap the relevance of a high-relevance doc with a low-relevance one
    # to simulate a degradation or shift in ranking quality.
    
    # Sort indices by relevance (descending)
    sorted_indices = sorted(range(len(new_labels)), key=lambda i: new_labels[i], reverse=True)
    
    # Select top-k indices
    top_k_indices = sorted_indices[:min(k, len(sorted_indices))]
    
    # Select bottom-k indices (lowest relevance)
    bottom_k_indices = sorted_indices[max(0, len(sorted_indices) - k):]
    
    if not top_k_indices or not bottom_k_indices:
        return new_labels
    
    # Apply swap with given magnitude
    # magnitude=1.0 means full swap, magnitude=0.0 means no swap
    if swap_magnitude > 0.0:
        # Pick a random pair to swap
        top_idx = rng.choice(top_k_indices)
        bottom_idx = rng.choice(bottom_k_indices)
        
        # Swap with probability = swap_magnitude
        if rng.random() < swap_magnitude:
            new_labels[top_idx], new_labels[bottom_idx] = new_labels[bottom_idx], new_labels[top_idx]
    
    return new_labels

def estimate_power(
    original_relevance: List[int],
    original_scores: List[float],
    metric_func,
    swap_magnitude: float,
    k: int,
    n_permutations: int,
    alpha: float = 0.05,
    rng: Optional[random.Random] = None
) -> Tuple[float, List[float]]:
    """
    Estimate statistical power for a given swap magnitude.
    
    Power = proportion of rejections under the alternative hypothesis.
    
    Args:
        original_relevance: Original relevance labels.
        original_scores: Original metric scores (for observed value).
        metric_func: Function to calculate metric (e.g., ndcg_at_k).
        swap_magnitude: Magnitude of the top-k swap.
        k: Number of top positions to swap.
        n_permutations: Number of permutations for null distribution.
        alpha: Significance level.
        rng: Random number generator.
        
    Returns:
        Tuple of (power_estimate, null_distribution_scores).
    """
    if rng is None:
        rng = random.Random(SEED)
    
    # 1. Generate null distribution (permutation test under H0)
    null_scores = []
    for _ in range(n_permutations):
        permuted_labels = original_relevance.copy()
        rng.shuffle(permuted_labels)
        # Calculate metric on permuted labels (assuming same document order)
        # For simplicity, we assume the metric function takes labels and returns score
        # In a real scenario, we'd need to re-calculate scores based on new relevance
        # Here we simulate by shuffling labels and re-computing
        score = metric_func(permuted_labels)
        null_scores.append(score)
    
    observed_score = original_scores[0] if isinstance(original_scores, list) else original_scores
    
    # 2. Generate alternative distribution (H1) with swap
    alt_scores = []
    for _ in range(n_permutations):
        swapped_labels = swap_top_k_relevance(original_relevance, k, swap_magnitude, rng)
        score = metric_func(swapped_labels)
        alt_scores.append(score)
    
    # 3. Calculate critical value from null distribution
    # For a one-tailed test (detecting degradation), we look at the lower tail
    # Critical value is the alpha quantile of the null distribution
    null_scores.sort()
    critical_idx = int(alpha * len(null_scores))
    critical_value = null_scores[critical_idx]
    
    # 4. Calculate power: proportion of alternative scores below critical value (for degradation)
    # Or above, depending on the hypothesis direction.
    # Assuming we are testing for degradation (lower scores are worse),
    # power is P(score_alt < critical_value)
    rejections = sum(1 for s in alt_scores if s < critical_value)
    power = rejections / len(alt_scores)
    
    return power, null_scores

def calculate_mdes_power(
    relevance_labels: List[int],
    metric_scores: List[float],
    metric_name: str,
    k: int = 10,
    n_permutations: int = 100,  # Reduced for speed in binary search
    alpha: float = 0.05,
    target_power: float = 0.8,
    tolerance: float = 0.001,
    min_mdes: float = 0.001,
    max_mdes: float = 0.500,
    rng: Optional[random.Random] = None
) -> Dict[str, Any]:
    """
    Calculate Minimum Detectable Effect Size (MDES) using binary search.
    
    Args:
        relevance_labels: Original relevance labels.
        metric_scores: Original metric scores.
        metric_name: Name of the metric ('ndcg' or 'map').
        k: Number of top positions to swap.
        n_permutations: Number of permutations for power estimation.
        alpha: Significance level.
        target_power: Target power (default 0.8).
        tolerance: Convergence tolerance for binary search.
        min_mdes: Minimum search bound.
        max_mdes: Maximum search bound.
        rng: Random number generator.
        
    Returns:
        Dictionary with mdes, power, ci_width, and other details.
    """
    if rng is None:
        rng = random.Random(SEED)
    
    # Select metric function
    if metric_name == 'ndcg':
        metric_func = lambda labels: ndcg_at_k(labels, k=k)
    elif metric_name == 'map':
        # MAP requires a list of scores per query, simplified here
        # For this implementation, we'll use a single score approximation
        metric_func = lambda labels: average_precision(labels)
    else:
        raise ValueError(f"Unsupported metric: {metric_name}")
    
    low = min_mdes
    high = max_mdes
    best_mdes = max_mdes
    best_power = 0.0
    
    # Binary search for MDES
    while high - low > tolerance:
        mid = (low + high) / 2.0
        
        power, _ = estimate_power(
            original_relevance=relevance_labels,
            original_scores=metric_scores,
            metric_func=metric_func,
            swap_magnitude=mid,
            k=k,
            n_permutations=n_permutations,
            alpha=alpha,
            rng=rng
        )
        
        if power >= target_power:
            best_mdes = mid
            best_power = power
            high = mid  # Try smaller effect
        else:
            low = mid   # Need larger effect
    
    # Calculate CI width (simplified: using bootstrap of power estimates)
    # For now, we estimate CI width based on the standard error of the power estimate
    # Power is a proportion, so SE = sqrt(p(1-p)/n)
    se = np.sqrt(best_power * (1 - best_power) / n_permutations)
    ci_width = 2 * 1.96 * se  # 95% CI width
    
    return {
        'metric': metric_name,
        'mdes': best_mdes,
        'power': best_power,
        'ci_width': ci_width,
        'alpha': alpha,
        'target_power': target_power,
        'k': k,
        'n_permutations': n_permutations
    }

def apply_bh_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        
    Returns:
        List of corrected p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_p = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n
    
    for i, (orig_idx, p_val) in enumerate(sorted_p):
        # BH correction: p_corrected = p_raw * n / rank
        # rank is i+1
        corrected_val = p_val * n / (i + 1)
        corrected_val = min(corrected_val, 1.0)  # Cap at 1.0
        # Ensure monotonicity: corrected[i] <= corrected[i+1]
        # We'll handle this in a second pass
        corrected[orig_idx] = corrected_val
    
    # Enforce monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        corrected[i] = min(corrected[i], corrected[i + 1])
    
    return corrected

def run_bh_correction(p_values: List[float]) -> List[float]:
    """Wrapper for BH correction."""
    return apply_bh_correction(p_values)

def run_power_analysis(
    queries_data: List[Dict[str, Any]],
    metric_name: str = 'ndcg',
    k: int = 10,
    n_permutations: int = 1000,
    target_power: float = 0.8,
    alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Run MDES analysis for a list of queries.
    
    Args:
        queries_data: List of query dictionaries with 'query_id', 'relevance', 'scores'.
        metric_name: Metric to use ('ndcg' or 'map').
        k: Top-k positions for swap.
        n_permutations: Permutations for power estimation.
        target_power: Target power.
        alpha: Significance level.
        
    Returns:
        List of MDES results for each query.
    """
    results = []
    rng = random.Random(SEED)
    
    for query in queries_data:
        query_id = query['query_id']
        relevance = query['relevance']
        scores = query['scores']
        
        try:
            mdes_result = calculate_mdes_power(
                relevance_labels=relevance,
                metric_scores=scores,
                metric_name=metric_name,
                k=k,
                n_permutations=n_permutations,
                alpha=alpha,
                target_power=target_power,
                rng=rng
            )
            mdes_result['query_id'] = query_id
            results.append(mdes_result)
            logger.info(f"Query {query_id}: MDES={mdes_result['mdes']:.4f}, Power={mdes_result['power']:.4f}")
        except Exception as e:
            logger.error(f"Error processing query {query_id}: {e}")
            continue
    
    return results

def run_mdes_summary_generation(
    mdes_results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Generate MDES summary CSV file.
    
    Args:
        mdes_results: List of MDES result dictionaries.
        output_path: Path to output CSV.
        
    Returns:
        Path to the generated CSV file.
    """
    if output_path is None:
        output_path = os.path.join(RESULTS_DIR, 'mdes', 'mdes_summary.csv')
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['metric', 'mdes', 'power', 'ci_width', 'query_id'])
        writer.writeheader()
        writer.writerows(mdes_results)
    
    logger.info(f"MDES summary saved to {output_path}")
    return output_path

def run_power_analysis_mode(
    queries_data: List[Dict[str, Any]],
    metric_name: str = 'ndcg',
    k: int = 10,
    n_permutations: int = 1000,
    target_power: float = 0.8,
    alpha: float = 0.05
) -> str:
    """
    Main entry point for power analysis mode.
    
    Args:
        queries_data: List of query data.
        metric_name: Metric name.
        k: Top-k for swap.
        n_permutations: Permutations.
        target_power: Target power.
        alpha: Significance level.
        
    Returns:
        Path to the generated MDES summary CSV.
    """
    logger.info(f"Running power analysis for {metric_name} with k={k}, n_perm={n_permutations}")
    
    # Run MDES calculation for each query
    mdes_results = run_power_analysis(
        queries_data=queries_data,
        metric_name=metric_name,
        k=k,
        n_permutations=n_permutations,
        target_power=target_power,
        alpha=alpha
    )
    
    # Generate summary CSV
    output_path = run_mdes_summary_generation(mdes_results)
    
    return output_path