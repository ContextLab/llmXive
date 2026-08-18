"""
Module to calculate p-values from null distributions.
"""

import os
import csv
import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
from config import RESULTS_DIR, ensure_dirs

logger = logging.getLogger(__name__)

def calculate_p_value(
    observed_score: float,
    null_distribution: List[float],
    N_actual: int
) -> float:
    """
    Calculate the p-value for an observed score against a null distribution.
    
    Formula: (r + 1) / (N + 1)
    where r is the rank of the observed score in the null distribution (count of null scores >= observed).
    
    Args:
        observed_score: The metric score from the original (non-permuted) data.
        null_distribution: List of scores from permutations.
        N_actual: Actual number of permutations executed.
    
    Returns:
        P-value.
    """
    if N_actual == 0:
        logger.warning("N_actual is 0, cannot calculate p-value. Returning 1.0.")
        return 1.0
    
    # Count how many null scores are >= observed score
    # Note: For metrics where higher is better (NDCG, AP), we test if observed is significantly higher.
    # So we count null scores that are >= observed.
    r = sum(1 for score in null_distribution if score >= observed_score)
    
    p_value = (r + 1) / (N_actual + 1)
    return p_value

def process_null_distributions(
    results: List[Dict[str, Any]],
    observed_scores: Dict[Tuple[int, str], float]
) -> List[Dict[str, Any]]:
    """
    Process null distribution results to calculate p-values.
    
    Args:
        results: List of null distribution results (from permutation.py).
        observed_scores: Dict mapping (query_id, metric) to observed score.
    
    Returns:
        List of dictionaries with p-values added.
    """
    p_value_results = []
    
    for res in results:
        query_id = res['query_id']
        metric = res['metric']
        null_dist = res['null_distribution']
        N_actual = res['N_actual']
        
        key = (query_id, metric)
        if key not in observed_scores:
            logger.warning(f"Missing observed score for {key}. Skipping.")
            continue
        
        obs_score = observed_scores[key]
        p_val = calculate_p_value(obs_score, null_dist, N_actual)
        
        p_value_results.append({
            'query_id': query_id,
            'metric': metric,
            'observed_score': obs_score,
            'N_actual': N_actual,
            'p_value': p_val
        })
        
        logger.info(f"Query {query_id}, Metric {metric}: Observed={obs_score:.4f}, P-value={p_val:.4f}, N_actual={N_actual}")
    
    return p_value_results

def run_p_value_calculation(
    permutation_results: List[Dict[str, Any]],
    observed_scores: Dict[Tuple[int, str], float],
    output_dir: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Calculate p-values and optionally save them.
    
    Args:
        permutation_results: Results from permutation tests.
        observed_scores: Observed scores for each query/metric.
        output_dir: Directory to save raw p-values.
    
    Returns:
        List of p-value results.
    """
    results = process_null_distributions(permutation_results, observed_scores)
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, "raw_p_values.csv")
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['query_id', 'metric', 'observed_score', 'N_actual', 'p_value'])
            writer.writeheader()
            writer.writerows(results)
        logger.info(f"Saved raw p-values to {filepath}")
    
    return results
