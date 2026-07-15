"""
Multiple testing correction module.

Implements the Benjamini-Yekutieli (BY) procedure for controlling the False Discovery Rate (FDR)
under arbitrary dependence structures, as required by FR-004.

This module provides a robust implementation of the BY procedure which is more conservative
than the standard Benjamini-Hochberg (BH) procedure but guarantees FDR control when test
statistics are positively dependent or arbitrary dependent.
"""

import numpy as np
from typing import List, Tuple, Dict, Any


def benjamini_yekutieli(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply the Benjamini-Yekutieli procedure to a list of p-values.
    
    The BY procedure controls the False Discovery Rate (FDR) under arbitrary dependence
    structures between test statistics. It is more conservative than the BH procedure
    but provides stronger guarantees when dependencies are unknown or complex.
    
    The procedure works as follows:
    1. Sort p-values in ascending order: p_(1) <= p_(2) <= ... <= p_(m)
    2. Compute critical values: q_(i) = (i / (m * c(m))) * alpha
       where c(m) = sum(1/j for j in 1..m) = H_m (the m-th harmonic number)
    3. Find the largest k such that p_(k) <= q_(k)
    4. Reject all hypotheses corresponding to p_(1), ..., p_(k)
    
    Parameters
    ----------
    p_values : List[float]
        List of raw p-values from hypothesis tests.
    alpha : float, optional
        Significance level (default is 0.05).
    
    Returns
    -------
    Tuple[List[float], List[bool]]
        A tuple containing:
        - q_values: List of adjusted q-values (BY-adjusted p-values)
        - is_significant: List of boolean flags indicating significance at level alpha
    
    Raises
    ------
    ValueError
        If p_values is empty or contains invalid values.
    """
    if not p_values:
        raise ValueError("p_values list cannot be empty")
    
    if any(p < 0 or p > 1 for p in p_values):
        raise ValueError("All p-values must be between 0 and 1")
    
    m = len(p_values)
    
    # Compute the harmonic number c(m) = sum(1/j for j in 1..m)
    # This is the correction factor for arbitrary dependence
    c_m = sum(1.0 / j for j in range(1, m + 1))
    
    # Sort p-values while keeping track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])
    
    # Compute critical values for each sorted p-value
    # q_(i) = (i / (m * c(m))) * alpha
    # Note: i is 1-indexed in the formula, so we use (rank + 1)
    ranks = np.arange(1, m + 1)
    critical_values = (ranks / (m * c_m)) * alpha
    
    # Find the largest k such that p_(k) <= q_(k)
    # We need to find the threshold index
    threshold_idx = -1
    for i in range(m - 1, -1, -1):
        if sorted_p_values[i] <= critical_values[i]:
            threshold_idx = i
            break
    
    # Create significance flags
    is_significant = [False] * m
    if threshold_idx >= 0:
        for i in range(threshold_idx + 1):
            original_idx = sorted_indices[i]
            is_significant[original_idx] = True
    
    # Compute q-values (adjusted p-values)
    # q_(i) = min(p_(j) * m * c(m) / j for j >= i)
    # This ensures monotonicity: q_(1) <= q_(2) <= ... <= q_(m)
    q_values = np.zeros(m)
    min_q = 1.0
    
    # Process from largest to smallest to ensure monotonicity
    for i in range(m - 1, -1, -1):
        rank = i + 1  # 1-indexed rank
        adjusted_p = sorted_p_values[i] * m * c_m / rank
        # Ensure q-values don't exceed 1.0
        adjusted_p = min(adjusted_p, 1.0)
        # Ensure monotonicity
        min_q = min(min_q, adjusted_p)
        q_values[sorted_indices[i]] = min_q
    
    return q_values.tolist(), is_significant


def apply_correction_to_results(
    results: Dict[str, Any],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Apply BY correction to a dictionary of statistical test results.
    
    This function is designed to work with the output structure from the stats_engine,
    specifically the results containing p-values for various statistics across datasets.
    
    Parameters
    ----------
    results : Dict[str, Any]
        Dictionary containing test results with p-values. Expected structure:
        {
            'dataset_id': {
                'statistic_name': {
                    'observed': float,
                    'p_value': float,
                    ...
                },
                ...
            },
            ...
        }
    alpha : float, optional
        Significance level (default is 0.05).
    
    Returns
    -------
    Dict[str, Any]
        Updated results dictionary with q-values and significance flags added:
        {
            'dataset_id': {
                'statistic_name': {
                    'observed': float,
                    'p_value': float,
                    'q_value': float,
                    'is_significant': bool,
                    ...
                },
                ...
            },
            ...
        }
    """
    # Collect all p-values with their metadata
    p_value_entries = []
    metadata = []
    
    for dataset_id, stats_dict in results.items():
        for stat_name, stat_data in stats_dict.items():
            if 'p_value' in stat_data:
                p_value_entries.append(stat_data['p_value'])
                metadata.append({
                    'dataset_id': dataset_id,
                    'statistic': stat_name
                })
    
    if not p_value_entries:
        # No p-values to correct, return original results
        return results
    
    # Apply BY correction
    q_values, is_significant = benjamini_yekutieli(p_value_entries, alpha)
    
    # Update results with corrected values
    for i, entry in enumerate(metadata):
        dataset_id = entry['dataset_id']
        stat_name = entry['statistic']
        
        results[dataset_id][stat_name]['q_value'] = q_values[i]
        results[dataset_id][stat_name]['is_significant'] = is_significant[i]
    
    return results