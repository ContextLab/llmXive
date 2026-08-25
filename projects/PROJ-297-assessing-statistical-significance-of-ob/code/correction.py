import logging
import numpy as np
from typing import List, Tuple, Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def benjamini_yekutieli(p_values: List[float]) -> List[float]:
    """
    Apply the Benjamini-Yekutieli procedure for FDR control.
    Returns adjusted p-values (q-values).
    """
    if not p_values:
        return []
    
    # Input validation
    p_arr = np.array(p_values)
    if np.any(p_arr < 0) or np.any(p_arr > 1):
        raise ValueError("P-values must be in [0, 1]")
    if np.any(np.isnan(p_arr)):
        raise ValueError("P-values cannot contain NaN")
    
    n = len(p_arr)
    c_n = np.sum(1.0 / np.arange(1, n + 1))
    
    # Sort p-values
    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]
    
    # Calculate q-values
    q = np.zeros(n)
    for i in range(n):
        q[i] = sorted_p[i] * n * c_n / (i + 1)
    
    # Ensure monotonicity (from largest to smallest)
    for i in range(n - 2, -1, -1):
        q[i] = min(q[i], q[i + 1])
    
    # Clip to [0, 1]
    q = np.clip(q, 0, 1)
    
    # Round to 4 decimal places
    q = np.round(q, 4)
    
    # Restore original order
    result = np.zeros(n)
    result[sorted_indices] = q
    
    return result.tolist()

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply the Benjamini-Hochberg procedure for FDR control.
    Returns adjusted p-values (q-values).
    """
    if not p_values:
        return []
    
    p_arr = np.array(p_values)
    n = len(p_arr)
    
    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]
    
    q = np.zeros(n)
    for i in range(n):
        q[i] = sorted_p[i] * n / (i + 1)
    
    for i in range(n - 2, -1, -1):
        q[i] = min(q[i], q[i + 1])
    
    q = np.clip(q, 0, 1)
    q = np.round(q, 4)
    
    result = np.zeros(n)
    result[sorted_indices] = q
    
    return result.tolist()

def apply_correction_to_results(
    results: List[Dict[str, Any]], 
    method: str = 'benjamini_yekutieli'
) -> List[Dict[str, Any]]:
    """
    Apply correction to a list of result dictionaries containing p-values.
    """
    p_values = [r['p_value'] for r in results]
    
    if method == 'benjamini_yekutieli':
        q_values = benjamini_yekutieli(p_values)
    elif method == 'benjamini_hochberg':
        q_values = benjamini_hochberg(p_values)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    for i, r in enumerate(results):
        r['q_value'] = q_values[i]
        r['significant'] = r['q_value'] < 0.05
    
    return results

def main():
    """Main entry point for correction module (for testing)."""
    pass

if __name__ == "__main__":
    pass
