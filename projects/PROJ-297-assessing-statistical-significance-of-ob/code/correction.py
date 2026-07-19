"""
Multiple testing correction module.
Implements Benjamini-Yekutieli and Benjamini-Hochberg procedures.
"""

import logging
import numpy as np
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

def benjamini_yekutieli(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Benjamini-Yekutieli correction.
    Returns q-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    
    # Stability Check: Detect if number of tests is very small
    # Per T085: If n < 5, the BY procedure may be overly conservative.
    if n < 5:
        logger.warning(
            f"BY Correction Stability Check: Number of tests ({n}) is very small (< 5). "
            "The Benjamini-Yekutieli procedure may be overly conservative in this scenario. "
            "Results should be interpreted with caution."
        )

    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate c(n) for BY
    c_n = sum(1.0 / (i + 1) for i in range(n))
    
    # Calculate critical values
    critical_values = [(i + 1) / (n * c_n) * alpha for i in range(n)]
    
    # Find the largest k such that p(k) <= critical(k)
    k = n - 1
    while k >= 0 and sorted_p[k] > critical_values[k]:
        k -= 1
    
    if k < 0:
        return [1.0] * n
    
    # Calculate q-values
    q_values = np.zeros(n)
    q_values[sorted_indices] = np.minimum.accumulate(
        (n / (np.arange(n, 0, -1))) * sorted_p[::-1] / c_n
    )
    q_values = np.minimum(q_values, 1.0)
    
    return q_values.tolist()

def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """Apply Benjamini-Hochberg correction."""
    n = len(p_values)
    if n == 0:
        return []
    
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    q_values = np.zeros(n)
    for i in range(n):
        q_values[sorted_indices[i]] = sorted_p[i] * n / (i + 1)
    
    q_values = np.minimum.accumulate(q_values[::-1])[::-1]
    q_values = np.minimum(q_values, 1.0)
    
    return q_values.tolist()

def apply_correction_to_results(p_values: List[float], method: str = 'by') -> List[float]:
    """Apply correction to a list of p-values."""
    if method == 'by':
        return benjamini_yekutieli(p_values)
    elif method == 'bh':
        return benjamini_hochberg(p_values)
    else:
        raise ValueError(f"Unknown method: {method}")

def main():
    pass

if __name__ == "__main__":
    main()