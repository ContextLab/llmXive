import numpy as np
from scipy import stats
from typing import Tuple, Union, Dict


def pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Pearson correlation coefficient between y_true and y_pred.
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        
    Returns:
        Pearson r correlation coefficient
    """
    if len(y_true) < 2:
        return 0.0
    
    correlation_matrix = np.corrcoef(y_true, y_pred)
    return float(correlation_matrix[0, 1])


def r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R² (coefficient of determination).
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        
    Returns:
        R² score
    """
    if len(y_true) < 2:
        return 0.0
    
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
    
    return float(1.0 - (ss_res / ss_tot))


def pearson_pvalue(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate p-value for Pearson correlation.
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        
    Returns:
        Two-tailed p-value
    """
    if len(y_true) < 2:
        return 1.0
    
    _, p_value = stats.pearsonr(y_true, y_pred)
    return float(p_value)


def calculate_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """
    Calculate all metrics (r, R², p-value) for predictions.
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        
    Returns:
        Dictionary with 'r', 'r2', and 'pvalue' keys
    """
    return {
        'r': pearson_r(y_true, y_pred),
        'r2': r_squared(y_true, y_pred),
        'pvalue': pearson_pvalue(y_true, y_pred)
    }
