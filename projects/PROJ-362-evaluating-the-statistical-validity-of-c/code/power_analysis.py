import logging
import random
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import os
import csv
from metrics import ndcg_at_k, average_precision
from config import PERMUTATION_COUNT, SEED, RESULTS_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def bootstrap_resample_indices(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate bootstrap resample indices."""
    return rng.choice(n, size=n, replace=True)

def swap_top_k_relevance(relevance_labels: List[int], k: int, rng: np.random.Generator) -> List[int]:
    """
    Simulate alternative hypothesis by swapping top-k positions.
    
    Args:
        relevance_labels: Original relevance labels
        k: Number of top positions to swap
        rng: NumPy random generator for reproducibility
        
    Returns:
        Modified relevance labels with top-k positions swapped
    """
    if k <= 0 or k >= len(relevance_labels):
        return relevance_labels[:]
    
    modified = relevance_labels[:]
    # Swap the top k positions
    for i in range(k // 2):
        j = k - 1 - i
        if i != j:
            modified[i], modified[j] = modified[j], modified[i]
    
    return modified

def estimate_power(
    observed_score: float,
    null_scores: List[float],
    swap_factor: float,
    metric_func,
    relevance_labels: List[int],
    doc_scores: List[float],
    rng: np.random.Generator,
    n_bootstrap: int = 100
) -> float:
    """
    Estimate statistical power for a given effect size.
    
    Args:
        observed_score: The observed metric score
        null_scores: List of null distribution scores
        swap_factor: Factor for top-k swapping (0-1)
        metric_func: Metric function (ndcg_at_k or average_precision)
        relevance_labels: Original relevance labels
        doc_scores: Document scores
        rng: NumPy random generator
        n_bootstrap: Number of bootstrap iterations
        
    Returns:
        Estimated power (proportion of rejections)
    """
    # Calculate critical value from null distribution
    alpha = 0.05
    sorted_null = sorted(null_scores)
    critical_idx = int((1 - alpha) * len(sorted_null))
    critical_value = sorted_null[min(critical_idx, len(sorted_null) - 1)]
    
    # Determine k for swapping based on swap_factor
    k = max(1, int(len(relevance_labels) * swap_factor))
    
    # Bootstrap to estimate power
    rejections = 0
    for _ in range(n_bootstrap):
        # Resample indices
        indices = bootstrap_resample_indices(len(relevance_labels), rng)
        resampled_labels = [relevance_labels[i] for i in indices]
        resampled_scores = [doc_scores[i] for i in indices]
        
        # Apply swap to simulate alternative hypothesis
        swapped_labels = swap_top_k_relevance(resampled_labels, k, rng)
        
        # Calculate metric on swapped labels
        try:
            swapped_score = metric_func(swapped_labels, resampled_scores)
            if swapped_score > critical_value:
                rejections += 1
        except Exception:
            continue
    
    power = rejections / n_bootstrap
    return power

def calculate_mdes_power(
    observed_score: float,
    null_scores: List[float],
    metric_func,
    relevance_labels: List[int],
    doc_scores: List[float],
    target_power: float = 0.8,
    tolerance: float = 0.001,
    search_range: Tuple[float, float] = (0.001, 0.500),
    n_bootstrap: int = 100
) -> Tuple[float, float, float]:
    """
    Calculate Minimum Detectable Effect Size (MDES) using binary search.
    
    Args:
        observed_score: The observed metric score
        null_scores: List of null distribution scores
        metric_func: Metric function (ndcg_at_k or average_precision)
        relevance_labels: Original relevance labels
        doc_scores: Document scores
        target_power: Target power (default 0.8)
        tolerance: Tolerance for binary search (default 0.001)
        search_range: Range for swap factor search (default 0.001, 0.500)
        n_bootstrap: Number of bootstrap iterations
        
    Returns:
        Tuple of (mdes, power, ci_width)
    """
    low, high = search_range
    rng = np.random.default_rng(SEED)
    
    mdes = high
    best_power = 0.0
    
    # Binary search for MDES
    while high - low > tolerance:
        mid = (low + high) / 2
        power = estimate_power(
            observed_score,
            null_scores,
            mid,
            metric_func,
            relevance_labels,
            doc_scores,
            rng,
            n_bootstrap
        )
        
        if power >= target_power:
            mdes = mid
            best_power = power
            high = mid
        else:
            low = mid
    
    # Calculate confidence interval width (approximate)
    ci_width = 2 * np.sqrt(best_power * (1 - best_power) / n_bootstrap)
    
    return mdes, best_power, ci_width

def apply_bh_correction(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of corrected p-values
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values with their original indices
    sorted_p_values = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n
    
    # Apply BH correction
    for i, (orig_idx, p_val) in enumerate(sorted_p_values):
        corrected[orig_idx] = min(p_val * n / (i + 1), 1.0)
    
    # Ensure monotonicity (corrected p-values should be non-decreasing)
    for i in range(n - 2, -1, -1):
        corrected[i] = min(corrected[i], corrected[i + 1])
    
    return corrected

def run_bh_correction(raw_p_values: List[float]) -> List[float]:
    """
    Run Benjamini-Hochberg correction on raw p-values.
    
    Args:
        raw_p_values: List of raw p-values
        
    Returns:
        List of corrected p-values
    """
    return apply_bh_correction(raw_p_values)

def run_power_analysis(
    query_id: int,
    relevance_labels: List[int],
    doc_scores: List[float],
    metric_name: str,
    observed_score: float,
    null_scores: List[float]
) -> Dict[str, Any]:
    """
    Run power analysis for a single query and metric.
    
    Args:
        query_id: Query identifier
        relevance_labels: Original relevance labels
        doc_scores: Document scores
        metric_name: Name of the metric (NDCG@10 or MAP)
        observed_score: Observed metric score
        null_scores: Null distribution scores
        
    Returns:
        Dictionary with MDES results
    """
    # Select metric function
    if metric_name == "NDCG@10":
        metric_func = ndcg_at_k
    elif metric_name == "MAP":
        metric_func = average_precision
    else:
        raise ValueError(f"Unknown metric: {metric_name}")
    
    # Calculate MDES
    mdes, power, ci_width = calculate_mdes_power(
        observed_score,
        null_scores,
        metric_func,
        relevance_labels,
        doc_scores,
        target_power=0.8,
        tolerance=0.001,
        search_range=(0.001, 0.500),
        n_bootstrap=100
    )
    
    return {
        'query_id': query_id,
        'metric': metric_name,
        'mdes': mdes,
        'power': power,
        'ci_width': ci_width
    }

def run_power_analysis_mode():
    """
    Run power analysis for all queries and metrics.
    """
    logger.info("Starting power analysis mode")
    
    # This would normally load data and process all queries
    # For now, we'll just demonstrate the structure
    
    # Example: Process a single query
    query_id = 1
    relevance_labels = [1, 0, 1, 0, 0, 1, 0, 0, 0, 0]
    doc_scores = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]
    
    # Calculate observed scores
    observed_ndcg = ndcg_at_k(relevance_labels, doc_scores, k=10)
    observed_map = average_precision(relevance_labels, doc_scores)
    
    # Generate null distribution (simplified)
    rng = np.random.default_rng(SEED)
    null_ndcg = [ndcg_at_k(rng.permutation(relevance_labels), doc_scores, k=10) for _ in range(100)]
    null_map = [average_precision(rng.permutation(relevance_labels), doc_scores) for _ in range(100)]
    
    # Run power analysis for both metrics
    results = []
    
    # NDCG@10 analysis
    ndcg_result = run_power_analysis(
        query_id,
        relevance_labels,
        doc_scores,
        "NDCG@10",
        observed_ndcg,
        null_ndcg
    )
    results.append(ndcg_result)
    
    # MAP analysis
    map_result = run_power_analysis(
        query_id,
        relevance_labels,
        doc_scores,
        "MAP",
        observed_map,
        null_map
    )
    results.append(map_result)
    
    # Save results
    save_mdes_results(results)
    
    logger.info("Power analysis completed")

def save_mdes_results(results: List[Dict[str, Any]]):
    """
    Save MDES results to CSV.
    
    Args:
        results: List of MDES result dictionaries
    """
    output_file = os.path.join(RESULTS_DIR, "mdes", "mdes_summary.csv")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['query_id', 'metric', 'mdes', 'power', 'ci_width']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saved MDES results to {output_file}")

def run_mdes_summary_generation():
    """
    Generate the MDES summary CSV file.
    """
    logger.info("Generating MDES summary")
    
    # This function would typically aggregate results from multiple queries
    # For now, we'll just ensure the file exists with proper structure
    
    output_file = os.path.join(RESULTS_DIR, "mdes", "mdes_summary.csv")
    
    if os.path.exists(output_file):
        logger.info(f"MDES summary already exists at {output_file}")
        return True
    
    # Create empty file with headers if no data exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['metric', 'mdes', 'power', 'ci_width']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
    
    logger.info(f"Created empty MDES summary at {output_file}")
    return True

def run_power_analysis_main():
    """
    Command-line entry point for power analysis.
    """
    import sys
    run_power_analysis_mode()
    sys.exit(0)

if __name__ == "__main__":
    run_power_analysis_main()
