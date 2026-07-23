import logging
import numpy as np
from typing import List, Tuple, Dict, Any

def benjamini_yekutieli(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply the Benjamini-Yekutieli (BY) procedure for FDR control under dependence.
    
    Args:
        p_values: List of p-values.
        alpha: Significance level.
    
    Returns:
        Tuple of (q_values, significant_flags)
    """
    if not p_values:
        return [], []
    
    n = len(p_values)
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate BY critical values
    # c(m) = sum(1/i for i in 1..m)
    c_m = sum(1.0 / i for i in range(1, n + 1))
    
    # BY threshold: (i / m) * (alpha / c(m))
    thresholds = [(i + 1) / n * (alpha / c_m) for i in range(n)]
    
    # Find the largest k such that p_(k) <= threshold_(k)
    k = -1
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= thresholds[i]:
            k = i
            break
    
    if k == -1:
        # No significant findings
        return [1.0] * n, [False] * n
    
    # Calculate q-values
    # q_i = min(1, min_{j>=i} (p_j * m / (j * c(m))))
    # Simplified: q-values are monotonic
    q_values = np.zeros(n)
    q_values[k] = sorted_p[k] * n * c_m / (k + 1)
    for i in range(k - 1, -1, -1):
        q_values[i] = min(1.0, min(q_values[i+1], sorted_p[i] * n * c_m / (i + 1)))
    
    # Map back to original order
    original_q = [0.0] * n
    for idx, q in zip(sorted_indices, q_values):
        original_q[idx] = q
    
    # Significant if q <= alpha
    significant = [q <= alpha for q in original_q]
    
    return original_q, significant

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[float], List[bool]]:
    """
    Apply the Benjamini-Hochberg (BH) procedure for FDR control under independence.
    
    Args:
        p_values: List of p-values.
        alpha: Significance level.
    
    Returns:
        Tuple of (q_values, significant_flags)
    """
    if not p_values:
        return [], []
    
    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # BH thresholds: (i / m) * alpha
    thresholds = [(i + 1) / n * alpha for i in range(n)]
    
    k = -1
    for i in range(n - 1, -1, -1):
        if sorted_p[i] <= thresholds[i]:
            k = i
            break
    
    if k == -1:
        return [1.0] * n, [False] * n
    
    q_values = np.zeros(n)
    q_values[k] = sorted_p[k] * n / (k + 1)
    for i in range(k - 1, -1, -1):
        q_values[i] = min(1.0, min(q_values[i+1], sorted_p[i] * n / (i + 1)))
    
    original_q = [0.0] * n
    for idx, q in zip(sorted_indices, q_values):
        original_q[idx] = q
    
    significant = [q <= alpha for q in original_q]
    
    return original_q, significant

def apply_correction_to_results(p_values: List[float], method: str = 'by', alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply correction method to a list of p-values.
    
    Args:
        p_values: List of p-values.
        method: 'by' or 'bh'.
        alpha: Significance level.
    
    Returns:
        Dictionary with q_values and significant flags.
    """
    if method == 'by':
        q_values, significant = benjamini_yekutieli(p_values, alpha)
    elif method == 'bh':
        q_values, significant = benjamini_hochberg(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {method}")
    
    return {
        'q_values': q_values,
        'significant': significant
    }

def main():
    # Example usage
    p_vals = [0.01, 0.04, 0.03, 0.005, 0.02]
    q_vals, sig = benjamini_yekutieli(p_vals)
    print(f"P-values: {p_vals}")
    print(f"Q-values: {q_vals}")
    print(f"Significant: {sig}")
