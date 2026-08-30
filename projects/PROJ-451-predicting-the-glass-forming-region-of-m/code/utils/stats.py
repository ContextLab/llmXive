"""
Statistical utilities for hypothesis testing and correction.
"""
from typing import List, Tuple, Dict, Optional
import numpy as np
import scipy.stats as stats

def bonferroni_correct(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply Bonferroni correction to a list of p-values.

    Args:
        p_values: List of raw p-values.
        alpha: Significance level.

    Returns:
        Tuple of (corrected_p_values, is_significant_list)
    """
    n = len(p_values)
    if n == 0:
        return [], []

    # Corrected p-values = min(p * n, 1.0)
    corrected = [min(p * n, 1.0) for p in p_values]
    significant = [p < (alpha / n) for p in p_values]

    return corrected, significant

def bonferroni_threshold(alpha: float, n_tests: int) -> float:
    """
    Calculate the Bonferroni-corrected significance threshold.
    """
    return alpha / n_tests

def apply_bonferroni_to_results(
    results: Dict[str, float],
    alpha: float = 0.05
) -> Dict[str, Dict[str, float]]:
    """
    Apply Bonferroni correction to a dictionary of p-values.
    Returns a dict with 'raw_p', 'corrected_p', 'significant'.
    """
    p_values = list(results.values())
    corrected, sig = bonferroni_correct(p_values, alpha)
    
    output = {}
    keys = list(results.keys())
    for i, key in enumerate(keys):
        output[key] = {
            'raw_p': results[key],
            'corrected_p': corrected[i],
            'significant': sig[i]
        }
    return output
