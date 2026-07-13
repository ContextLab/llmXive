"""
Metrics utilities for correlation and regression evaluation.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Union

def pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Pearson correlation coefficient.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        Pearson r value
    """
    r, _ = stats.pearsonr(y_true, y_pred)
    return r

def r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared (coefficient of determination).
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        R-squared value
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)

def pearson_pvalue(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate p-value for Pearson correlation.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        P-value
    """
    _, p_value = stats.pearsonr(y_true, y_pred)
    return p_value

def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate all metrics for a prediction.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        Dictionary of metrics
    """
    return {
        'pearson_r': pearson_r(y_true, y_pred),
        'r_squared': r_squared(y_true, y_pred),
        'p_value': pearson_pvalue(y_true, y_pred),
    }
