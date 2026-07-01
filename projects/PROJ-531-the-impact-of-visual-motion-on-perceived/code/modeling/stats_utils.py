import numpy as np
import pandas as pd
from typing import List, Union

def bonferroni_correction(p_values: Union[List[float], np.ndarray, pd.Series]) -> np.ndarray:
    """
    Apply Bonferroni correction to a list/array of p-values.
    
    The Bonferroni correction adjusts the significance threshold by dividing 
    the alpha level by the number of tests, or equivalently, multiplying 
    p-values by the number of tests (capped at 1.0).
    
    Parameters
    ----------
    p_values : list, np.ndarray, or pd.Series
        Array-like of raw p-values from statistical tests.
        
    Returns
    -------
    np.ndarray
        Array of corrected p-values (adjusted for multiple comparisons).
    """
    p_array = np.asarray(p_values, dtype=float)
    n_tests = len(p_array)
    
    if n_tests == 0:
        return p_array
        
    # Multiply by number of tests
    corrected = p_array * n_tests
    
    # Cap at 1.0
    corrected = np.minimum(corrected, 1.0)
    
    return corrected

def benjamini_hochberg_correction(p_values: Union[List[float], np.ndarray, pd.Series]) -> np.ndarray:
    """
    Apply Benjamini-Hochberg (BH) correction to control the False Discovery Rate (FDR).
    
    The BH procedure sorts p-values, compares each to a threshold that increases 
    with rank, and determines which hypotheses to reject. The output here returns 
    the adjusted p-values (q-values) such that rejecting at threshold alpha 
    corresponds to controlling FDR at alpha.
    
    Parameters
    ----------
    p_values : list, np.ndarray, or pd.Series
        Array-like of raw p-values from statistical tests.
        
    Returns
    -------
    np.ndarray
        Array of BH-adjusted p-values (q-values).
        
    Notes
    -----
    This implementation follows the standard Benjamini-Hochberg procedure:
    1. Sort p-values: p(1) <= p(2) <= ... <= p(m)
    2. For each i, compute q(i) = min( (m/i) * p(i), 1 )
    3. Ensure monotonicity: q(i) = min(q(i), q(i+1), ..., q(m))
    """
    p_array = np.asarray(p_values, dtype=float)
    n_tests = len(p_array)
    
    if n_tests == 0:
        return p_array
        
    # Create index array to track original positions
    sorted_indices = np.argsort(p_array)
    sorted_p = p_array[sorted_indices]
    
    # Calculate BH adjusted values
    # q_i = (m / i) * p_i  (where i is 1-based rank)
    ranks = np.arange(1, n_tests + 1)
    adjusted = (n_tests / ranks) * sorted_p
    
    # Ensure adjusted p-values do not exceed 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Enforce monotonicity: q_i <= q_{i+1}
    # We traverse backwards to ensure that if a later value is smaller, 
    # we take the minimum of the current and the next.
    # Actually, standard BH ensures q_i <= q_{i+1} by taking min(q_i, q_{i+1}) backwards.
    for i in range(n_tests - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
        
    # Reorder to original positions
    result = np.zeros(n_tests)
    result[sorted_indices] = adjusted
    
    return result
