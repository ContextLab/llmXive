"""
Utilities for formatting p-values, specifically handling the p=0.0 case.

Per task T032: When a permutation test or statistical calculation results in 
a p-value of 0.0 (due to finite iterations), report it as "< 0.0001" to 
indicate statistical significance beyond the resolution of the test.
"""
import numpy as np
from typing import Union

def format_p_value(p_value: Union[float, np.floating], threshold: float = 0.0001) -> str:
    """
    Format a p-value for reporting, handling the zero case.
    
    Args:
        p_value: The calculated p-value (float).
        threshold: The threshold below which to report as "< X". Defaults to 0.0001.
        
    Returns:
        A string representation of the p-value. 
        - If p_value is 0.0 or < threshold, returns "< 0.0001".
        - Otherwise, returns the formatted float (4 decimal places).
    """
    if p_value is None:
        return "N/A"
        
    # Handle floating point comparisons
    val = float(p_value)
    
    if val == 0.0 or val < threshold:
        return "< 0.0001"
    else:
        return f"{val:.4f}"

def format_p_value_float(p_value: Union[float, np.floating], threshold: float = 0.0001) -> float:
    """
    Returns the numeric value for calculations, capping at a small positive number 
    if zero, to avoid log(0) errors in downstream stats.
    
    Args:
        p_value: The calculated p-value.
        threshold: The floor value to return if p_value is 0.0.
        
    Returns:
        A float value >= threshold.
    """
    val = float(p_value)
    if val == 0.0:
        return threshold
    return val

def is_significant(p_value: Union[float, np.floating], alpha: float = 0.05) -> bool:
    """
    Check if a p-value indicates statistical significance.
    
    Args:
        p_value: The calculated p-value.
        alpha: The significance threshold (default 0.05).
        
    Returns:
        True if p_value < alpha, False otherwise.
    """
    val = float(p_value)
    return val < alpha
