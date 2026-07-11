"""
Custom metric definitions and statistical helpers for yield strength prediction.

This module provides:
- Regression metrics (MAE, RMSE, R²)
- Statistical helpers for cross-validation analysis
- Confidence interval calculation via bootstrapping
"""
from typing import List, Union, Optional
import numpy as np
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_mae(y_true: Union[List[float], np.ndarray], 
                  y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Absolute Error.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        MAE as a float
    """
    return float(mean_absolute_error(y_true, y_pred))


def calculate_rmse(y_true: Union[List[float], np.ndarray], 
                   y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Root Mean Squared Error.
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        RMSE as a float
    """
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def calculate_r2(y_true: Union[List[float], np.ndarray], 
                 y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate R-squared (coefficient of determination).
    
    Args:
        y_true: True values
        y_pred: Predicted values
        
    Returns:
        R² score as a float
    """
    return float(r2_score(y_true, y_pred))


def bootstrap_confidence_interval(
    scores: Union[List[float], np.ndarray],
    confidence: float = 0.95,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> tuple:
    """
    Calculate bootstrap confidence intervals for a set of scores.
    
    Args:
        scores: Array of scores (e.g., R² from CV folds)
        confidence: Confidence level (default 0.95 for 95% CI)
        n_bootstrap: Number of bootstrap samples
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (lower_bound, median, upper_bound)
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    scores = np.array(scores)
    n = len(scores)
    bootstrap_means = []
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(scores, size=n, replace=True)
        bootstrap_means.append(np.mean(sample))
        
    bootstrap_means = np.array(bootstrap_means)
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    median = np.median(bootstrap_means)
    
    return float(lower), float(median), float(upper)


def spearman_correlation(x: Union[List[float], np.ndarray], 
                         y: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Spearman rank correlation coefficient.
    
    Args:
        x: First array
        y: Second array
        
    Returns:
        Spearman correlation coefficient
    """
    x = np.array(x)
    y = np.array(y)
    corr, _ = stats.spearmanr(x, y)
    return float(corr) if not np.isnan(corr) else 0.0


def calculate_variance(scores: Union[List[float], np.ndarray]) -> float:
    """
    Calculate variance of a set of scores.
    
    Args:
        scores: Array of scores
        
    Returns:
        Variance as a float
    """
    return float(np.var(scores, ddof=1))


def calculate_std_dev(scores: Union[List[float], np.ndarray]) -> float:
    """
    Calculate standard deviation of a set of scores.
    
    Args:
        scores: Array of scores
        
    Returns:
        Standard deviation as a float
    """
    return float(np.std(scores, ddof=1))