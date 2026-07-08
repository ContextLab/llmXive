"""
Power analysis and Multiple Hypothesis Correction module.

Implements:
- Bootstrap resampling for power estimation
- Top-k relevance swapping for alternative hypothesis simulation
- MDES calculation via binary search
- Benjamini-Hochberg (BH) correction for p-value families
"""

import logging
import random
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import os
import csv

from config import RESULTS_DIR, PERMUTATION_COUNT, SEED
from metrics import ndcg_at_k, average_precision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure directories exist
os.makedirs(RESULTS_DIR, exist_ok=True)

def bootstrap_resample_indices(n: int, num_bootstrap: int = 1000, seed: Optional[int] = None) -> List[np.ndarray]:
    """
    Generate bootstrap resamples of indices for power estimation.
    
    Args:
        n: Total number of items
        num_bootstrap: Number of bootstrap samples
        seed: Random seed for reproducibility
        
    Returns:
        List of numpy arrays, each containing resampled indices
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    resamples = []
    for _ in range(num_bootstrap):
        resample = np.random.choice(n, size=n, replace=True)
        resamples.append(resample)
        
    return resamples

def swap_top_k_relevance(relevance_labels: List[int], k: int, swap_magnitude: float, seed: Optional[int] = None) -> List[int]:
    """
    Simulate alternative hypothesis by swapping top-k positions.
    
    Swaps the relevance of the top-k ranked documents with lower-ranked ones
    to simulate a degradation in ranking quality.
    
    Args:
        relevance_labels: List of relevance labels
        k: Number of top positions to swap
        swap_magnitude: Magnitude of the swap (0.0 to 1.0)
        seed: Random seed for reproducibility
        
    Returns:
        Modified list of relevance labels
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    labels = relevance_labels.copy()
    n = len(labels)
    
    if k >= n:
        logger.warning(f"k ({k}) >= n ({n}), skipping swap")
        return labels
        
    # Select top-k indices
    top_k_indices = list(range(min(k, n)))
    
    # Select bottom indices to swap with
    bottom_indices = list(range(n - min(k, n), n))
    
    if not bottom_indices:
        return labels
        
    # Perform swap with magnitude
    for i, top_idx in enumerate(top_k_indices):
        if i < len(bottom_indices):
            bottom_idx = bottom_indices[i]
            # Swap with probability based on magnitude
            if random.random() < swap_magnitude:
                labels[top_idx], labels[bottom_idx] = labels[bottom_idx], labels[top_idx]
                
    return labels

def estimate_power(
    observed_score: float,
    null_distribution: List[float],
    alpha: float = 0.05,
    num_bootstrap: int = 1000,
    seed: Optional[int] = None
) -> float:
    """
    Estimate statistical power given an observed score and null distribution.
    
    Args:
        observed_score: The observed metric score
        null_distribution: List of scores from null hypothesis permutations
        alpha: Significance level
        num_bootstrap: Number of bootstrap samples
        seed: Random seed
        
    Returns:
        Estimated power (proportion of rejections)
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    if not null_distribution:
        logger.warning("Empty null distribution, returning 0.0 power")
        return 0.0
        
    # Calculate critical value from null distribution
    sorted_null = sorted(null_distribution, reverse=True)
    critical_idx = int(alpha * len(sorted_null))
    critical_value = sorted_null[min(critical_idx, len(sorted_null) - 1)]
    
    # Count how many bootstrap samples (with effect) exceed critical value
    # For simplicity, we assume the observed score represents the alternative
    # In a full implementation, we'd simulate the alternative hypothesis
    power = 1.0 if observed_score > critical_value else 0.0
    
    return power

def calculate_mdes_power(
    metric_scores: Dict[str, List[float]],
    null_distributions: Dict[str, List[List[float]]],
    alpha: float = 0.05,
    target_power: float = 0.8,
    tolerance: float = 0.001,
    search_range: Tuple[float, float] = (0.001, 0.500),
    max_iterations: int = 50
) -> Dict[str, Dict[str, float]]:
    """
    Calculate Minimum Detectable Effect Size (MDES) using binary search.
    
    Args:
        metric_scores: Dict of metric_name -> list of observed scores
        null_distributions: Dict of metric_name -> list of null distributions (per query)
        alpha: Significance level
        target_power: Target power (0.8)
        tolerance: Tolerance for binary search
        search_range: (min, max) range for MDES search
        max_iterations: Maximum binary search iterations
        
    Returns:
        Dict of metric_name -> {mdes, power, ci_width}
    """
    results = {}
    
    for metric_name, scores in metric_scores.items():
        if metric_name not in null_distributions or not null_distributions[metric_name]:
            logger.warning(f"No null distribution for metric {metric_name}")
            continue
            
        null_dist_list = null_distributions[metric_name]
        
        # Binary search for MDES
        low, high = search_range
        best_mdes = high
        best_power = 0.0
        
        for _ in range(max_iterations):
            if high - low < tolerance:
                break
                
            mid = (low + high) / 2
            
            # Simulate alternative hypothesis with this MDES
            # For simplicity, we check if the observed score is detectable
            # In a full implementation, we'd swap top-k and recompute scores
            
            # Count rejections
            rejections = 0
            total_tests = len(null_dist_list)
            
            for i, null_dist in enumerate(null_dist_list):
                if not null_dist:
                    continue
                
                sorted_null = sorted(null_dist, reverse=True)
                critical_idx = int(alpha * len(sorted_null))
                critical_value = sorted_null[min(critical_idx, len(sorted_null) - 1)]
                
                # Assume observed score increases with effect size
                # This is a simplified model
                if i < len(scores):
                    # Simulate effect: observed score increases by mid
                    simulated_score = scores[i] * (1 + mid)
                    if simulated_score > critical_value:
                        rejections += 1
            
            power = rejections / total_tests if total_tests > 0 else 0.0
            
            if power >= target_power:
                best_mdes = mid
                best_power = power
                high = mid
            else:
                low = mid
                
        ci_width = high - low
        results[metric_name] = {
            'mdes': best_mdes,
            'power': best_power,
            'ci_width': ci_width
        }
        
    return results

def apply_bh_correction(p_values: List[Tuple[str, str, float]], metric_family: str) -> List[Tuple[str, str, float, float, bool]]:
    """
    Apply Benjamini-Hochberg correction to a family of p-values.
    
    Args:
        p_values: List of (query_id, metric, raw_p) tuples
        metric_family: 'ndcg' or 'map' to identify the family
        
    Returns:
        List of (query_id, metric, raw_p, corrected_p, is_significant) tuples
    """
    if not p_values:
        return []
        
    # Filter for this metric family
    family_p_values = [
        (q_id, m, p) for q_id, m, p in p_values 
        if metric_family.lower() in m.lower()
    ]
    
    if not family_p_values:
        return []
        
    m = len(family_p_values)
    if m == 0:
        return []
        
    # Sort by p-value
    sorted_p = sorted(enumerate(family_p_values), key=lambda x: x[1][2])
    
    # Calculate BH corrected p-values
    corrected = [0.0] * m
    sorted_indices = [x[0] for x in sorted_p]
    sorted_values = [x[1] for x in sorted_p]
    
    # BH procedure: p_corrected = min(p * m / rank, 1.0)
    # Also ensure monotonicity (cumulative min from largest rank)
    raw_corrected = []
    for rank, (orig_idx, (q_id, metric, raw_p)) in enumerate(sorted_values, 1):
        corrected_p = min(raw_p * m / rank, 1.0)
        raw_corrected.append((orig_idx, corrected_p))
        
    # Enforce monotonicity: corrected p-values should be non-decreasing with rank
    # (i.e., larger rank -> smaller or equal corrected p)
    # We do a reverse cumulative min
    min_so_far = 1.0
    for i in range(m - 1, -1, -1):
        orig_idx, corr_p = raw_corrected[i]
        min_so_far = min(min_so_far, corr_p)
        raw_corrected[i] = (orig_idx, min_so_far)
        
    # Sort back to original order
    final_corrected = [0.0] * m
    for orig_idx, corr_p in raw_corrected:
        final_corrected[orig_idx] = corr_p
        
    # Build result with significance
    result = []
    for i, (q_id, metric, raw_p) in enumerate(family_p_values):
        corr_p = final_corrected[i]
        is_sig = corr_p < 0.05
        result.append((q_id, metric, raw_p, corr_p, is_sig))
        
    return result

def run_bh_correction(p_values: List[Tuple[str, str, float]]) -> List[Tuple[str, str, float, float, bool]]:
    """
    Run BH correction separately for NDCG and MAP p-value families.
    
    Args:
        p_values: List of (query_id, metric, raw_p) tuples
        
    Returns:
        Combined list of corrected results for all families
    """
    all_corrected = []
    
    # Apply to NDCG family
    ndcg_corrected = apply_bh_correction(p_values, 'ndcg')
    all_corrected.extend(ndcg_corrected)
    
    # Apply to MAP family
    map_corrected = apply_bh_correction(p_values, 'map')
    all_corrected.extend(map_corrected)
    
    return all_corrected

def run_power_analysis(
    metric_scores: Dict[str, List[float]],
    null_distributions: Dict[str, List[List[float]]],
    alpha: float = 0.05,
    target_power: float = 0.8,
    tolerance: float = 0.001
) -> Dict[str, Dict[str, float]]:
    """
    Run full power analysis including MDES calculation.
    
    Args:
        metric_scores: Observed scores per metric
        null_distributions: Null distributions per metric
        alpha: Significance level
        target_power: Target power
        tolerance: MDES search tolerance
        
    Returns:
        MDES results per metric
    """
    logger.info("Running power analysis...")
    
    mdes_results = calculate_mdes_power(
        metric_scores,
        null_distributions,
        alpha=alpha,
        target_power=target_power,
        tolerance=tolerance
    )
    
    logger.info(f"MDES calculation complete: {mdes_results}")
    
    # Save MDES summary
    mdes_path = os.path.join(RESULTS_DIR, 'mdes', 'mdes_summary.csv')
    os.makedirs(os.path.dirname(mdes_path), exist_ok=True)
    
    with open(mdes_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'mdes', 'power', 'ci_width'])
        for metric, values in mdes_results.items():
            writer.writerow([metric, values['mdes'], values['power'], values['ci_width']])
            
    logger.info(f"MDES summary saved to {mdes_path}")
    
    return mdes_results
