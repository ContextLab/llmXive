"""
Metric Utilities for Model Evaluation.

Provides MAE, MSE, and R2 score calculations for stiffness prediction tasks.
These metrics are used to evaluate the performance of the CNN model against
the FFT-based numerical homogenization ground truth.
"""

import numpy as np
from typing import Union, List

def mean_absolute_error(y_true: Union[np.ndarray, List[float]], 
                      y_pred: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate Mean Absolute Error (MAE).
    
    MAE measures the average magnitude of the errors in a set of predictions,
    without considering their direction. It is the average over the test sample
    of the absolute differences between prediction and actual observation.
    
    Args:
        y_true: Ground truth values (effective stiffness components).
        y_pred: Predicted values.
        
    Returns:
        float: The mean absolute error.
        
    Example:
        >>> mae = mean_absolute_error([1.0, 2.0, 3.0], [1.1, 2.1, 2.9])
        >>> print(f"{mae:.6f}")
        0.100000
    """
    y_true = np.array(y_true, dtype=np.float64)
    y_pred = np.array(y_pred, dtype=np.float64)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Input shapes must match: y_true {y_true.shape} vs y_pred {y_pred.shape}"
        )
        
    return float(np.mean(np.abs(y_true - y_pred)))

def mean_squared_error(y_true: Union[np.ndarray, List[float]], 
                      y_pred: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate Mean Squared Error (MSE).
    
    MSE measures the average of the squares of the errors—that is, 
    the average squared difference between the estimated values and the actual value.
    It is a risk function corresponding to the expected value of the squared error loss.
    
    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        
    Returns:
        float: The mean squared error.
        
    Example:
        >>> mse = mean_squared_error([1.0, 2.0, 3.0], [1.1, 2.1, 2.9])
        >>> print(f"{mse:.6f}")
        0.010000
    """
    y_true = np.array(y_true, dtype=np.float64)
    y_pred = np.array(y_pred, dtype=np.float64)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Input shapes must match: y_true {y_true.shape} vs y_pred {y_pred.shape}"
        )
        
    return float(np.mean((y_true - y_pred) ** 2))

def r2_score(y_true: Union[np.ndarray, List[float]], 
             y_pred: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate R-squared (coefficient of determination).
    
    R2 represents the proportion of the variance for a dependent variable 
    that's explained by an independent variable or variables in a regression model.
    A value of 1.0 indicates perfect prediction, 0.0 indicates the model performs 
    no better than predicting the mean, and negative values indicate the model 
    performs worse than predicting the mean.
    
    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        
    Returns:
        float: The R-squared score.
        
    Example:
        >>> r2 = r2_score([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        >>> print(f"{r2:.6f}")
        1.000000
    """
    y_true = np.array(y_true, dtype=np.float64)
    y_pred = np.array(y_pred, dtype=np.float64)
    
    if y_true.shape != y_pred.shape:
        raise ValueError(
            f"Input shapes must match: y_true {y_true.shape} vs y_pred {y_pred.shape}"
        )
        
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    if ss_tot == 0.0:
        # If all true values are the same, R2 is undefined. 
        # Return 0.0 if predictions are perfect, else 0.0 (or could raise).
        if ss_res == 0.0:
            return 1.0
        return 0.0
        
    return float(1.0 - (ss_res / ss_tot))