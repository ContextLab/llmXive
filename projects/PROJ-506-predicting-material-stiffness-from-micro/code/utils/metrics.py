"""
Metric Utilities for Model Evaluation.

Provides MAE, MSE, and R2 score calculations.
"""

import numpy as np
from typing import Union, List

def mean_absolute_error(y_true: Union[np.ndarray, List[float]], 
                      y_pred: Union[np.ndarray, List[float]]) -> float:
    """Calculate Mean Absolute Error."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean(np.abs(y_true - y_pred))

def mean_squared_error(y_true: Union[np.ndarray, List[float]], 
                      y_pred: Union[np.ndarray, List[float]]) -> float:
    """Calculate Mean Squared Error."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return np.mean((y_true - y_pred) ** 2)

def r2_score(y_true: Union[np.ndarray, List[float]], 
             y_pred: Union[np.ndarray, List[float]]) -> float:
    """Calculate R-squared (coefficient of determination)."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0:
        return 0.0
        
    return 1.0 - (ss_res / ss_tot)
