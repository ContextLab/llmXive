import logging
import numpy as np
from typing import List, Tuple, Dict, Any

logger = logging.getLogger("correction")

def benjamini_yekutieli(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Yekutieli procedure to a list of p-values.
    Returns q-values.
    """
    if not p_values:
        return []
    
    p_values = np.array(p_values)
    if np.any(p_values < 0) or np.any(p_values > 1):
        raise ValueError("P-values must be in [0, 1].")
    
    n = len(p_values)
    # BY constant
    c_n = np.sum(1.0 / np.arange(1, n + 1))
    
    # Sort p-values
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate q-values
    q_values = np.zeros(n)
    current_q = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = (n / (c_n * rank)) * sorted_p[i]
        current_q = min(current_q, q)
        q_values[sorted_indices[i]] = current_q
    
    # Ensure monotonicity
    for i in range(n - 2, -1, -1):
        q_values[sorted_indices[i]] = min(q_values[sorted_indices[i]], q_values[sorted_indices[i+1]])
    
    # Floor enforcement
    q_values = np.clip(q_values, 1e-10, 1.0 - 1e-10)
    
    return q_values.tolist()

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg procedure.
    """
    if not p_values:
        return []
    
    p_values = np.array(p_values)
    n = len(p_values)
    
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    q_values = np.zeros(n)
    current_q = 1.0
    
    for i in range(n - 1, -1, -1):
        rank = i + 1
        q = (n / rank) * sorted_p[i]
        current_q = min(current_q, q)
        q_values[sorted_indices[i]] = current_q
    
    for i in range(n - 2, -1, -1):
        q_values[sorted_indices[i]] = min(q_values[sorted_indices[i]], q_values[sorted_indices[i+1]])
    
    return q_values.tolist()

def apply_correction_to_results(
    results: Dict[str, Any],
    correction_method: str = 'by'
) -> Dict[str, Any]:
    """Apply correction to a results dictionary."""
    p_values = results.get('p_values', [])
    if not p_values:
        return results
    
    if correction_method == 'by':
        q_values = benjamini_yekutieli(p_values)
    elif correction_method == 'bh':
        q_values = benjamini_hochberg(p_values)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    results['q_values'] = q_values
    return results

def main():
    """Main entry point for correction testing."""
    p_vals = [0.01, 0.04, 0.03, 0.20, 0.50]
    q_vals = benjamini_yekutieli(p_vals)
    logger.info(f"Input p-values: {p_vals}")
    logger.info(f"Output q-values: {q_vals}")

if __name__ == "__main__":
    main()
