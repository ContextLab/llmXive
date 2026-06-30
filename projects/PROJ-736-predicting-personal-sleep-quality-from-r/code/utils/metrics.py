"""
Metrics utilities for sleep quality prediction analysis.

Provides functions to calculate Pearson correlation coefficient (r),
R-squared (R²), and associated p-values for model evaluation.
"""
import numpy as np
from scipy import stats
from typing import Tuple, Union

def pearson_r(y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]) -> float:
    """
    Calculate the Pearson correlation coefficient between true and predicted values.
    
    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        
    Returns:
        Pearson correlation coefficient (r).
        
    Raises:
        ValueError: If input arrays are empty or have different lengths.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    if y_true.size == 0 or y_pred.size == 0:
        raise ValueError("Input arrays cannot be empty.")
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {y_true.shape} vs {y_pred.shape}.")
        
    r, _ = stats.pearsonr(y_true, y_pred)
    return float(r)

def r_squared(y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]) -> float:
    """
    Calculate the R-squared (coefficient of determination) score.
    
    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        
    Returns:
        R-squared value.
        
    Raises:
        ValueError: If input arrays are empty or have different lengths.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    if y_true.size == 0 or y_pred.size == 0:
        raise ValueError("Input arrays cannot be empty.")
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {y_true.shape} vs {y_pred.shape}.")
        
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0 if ss_res == 0 else -1.0
        
    return float(1 - (ss_res / ss_tot))

def pearson_pvalue(y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]) -> float:
    """
    Calculate the p-value for the Pearson correlation coefficient.
    
    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        
    Returns:
        Two-tailed p-value.
        
    Raises:
        ValueError: If input arrays are empty or have different lengths.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    
    if y_true.size == 0 or y_pred.size == 0:
        raise ValueError("Input arrays cannot be empty.")
    if y_true.shape != y_pred.shape:
        raise ValueError(f"Input arrays must have the same shape. Got {y_true.shape} vs {y_pred.shape}.")
        
    _, p_value = stats.pearsonr(y_true, y_pred)
    return float(p_value)

def calculate_metrics(y_true: Union[np.ndarray, list], y_pred: Union[np.ndarray, list]) -> dict:
    """
    Calculate all primary regression metrics at once.
    
    Args:
        y_true: Array of true values.
        y_pred: Array of predicted values.
        
    Returns:
        Dictionary containing 'pearson_r', 'r_squared', and 'p_value'.
        
    Raises:
        ValueError: If input arrays are invalid.
    """
    return {
        "pearson_r": pearson_r(y_true, y_pred),
        "r_squared": r_squared(y_true, y_pred),
        "p_value": pearson_pvalue(y_true, y_pred)
    }
