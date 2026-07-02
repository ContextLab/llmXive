"""
Statistical testing utilities for model evaluation and comparison.

Provides functions for paired t-tests, Bonferroni correction, and 
Kolmogorov-Smirnov tests.
"""
import numpy as np
from scipy import stats
from typing import Sequence, Tuple, Union, List

def paired_t_test(pred1: Sequence[float], pred2: Sequence[float]) -> Tuple[float, float]:
    """
    Perform a paired t-test to compare two sets of predictions or values.
    
    Args:
        pred1: First sequence of numeric values.
        pred2: Second sequence of numeric values (must be same length as pred1).
        
    Returns:
        Tuple of (t-statistic, p-value).
        
    Raises:
        ValueError: If sequences are not of equal length or are empty.
    """
    arr1 = np.array(pred1)
    arr2 = np.array(pred2)
    
    if len(arr1) != len(arr2):
        raise ValueError("Input sequences must have equal length.")
    if len(arr1) == 0:
        raise ValueError("Input sequences cannot be empty.")
        
    t_stat, p_val = stats.ttest_rel(arr1, arr2)
    return float(t_stat), float(p_val)

def bonferroni_correct(p_values: Sequence[float], n_comparisons: int) -> List[float]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: Sequence of p-values to correct.
        n_comparisons: Total number of comparisons performed (used as the divisor).
        
    Returns:
        List of corrected p-values (capped at 1.0).
    """
    if n_comparisons <= 0:
        raise ValueError("n_comparisons must be positive.")
        
    corrected = [min(p * n_comparisons, 1.0) for p in p_values]
    return corrected

def ks_test(data1: Sequence[float], data2: Sequence[float]) -> Tuple[float, float]:
    """
    Perform a two-sample Kolmogorov-Smirnov test to compare distributions.
    
    Args:
        data1: First sequence of numeric values.
        data2: Second sequence of numeric values.
        
    Returns:
        Tuple of (KS statistic, p-value).
    """
    arr1 = np.array(data1)
    arr2 = np.array(data2)
    
    ks_stat, p_val = stats.ks_2samp(arr1, arr2)
    return float(ks_stat), float(p_val)
