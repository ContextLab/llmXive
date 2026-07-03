"""
Common statistical utility functions.

Implements T006: bootstrap resampling, error metrics.
"""

import numpy as np
from typing import List, Tuple, Optional, Union

def calculate_metrics(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> dict:
    """
    Calculate error metrics: MAE, RMSE, MSE, Mean Signed Error.

    Args:
        y_true: Reference values.
        y_pred: Predicted values.

    Returns:
        Dictionary with metrics.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    errors = y_pred - y_true
    
    mae = np.mean(np.abs(errors))
    rmse = np.sqrt(np.mean(errors**2))
    mse = np.mean(errors**2)
    mse_signed = np.mean(errors) # Mean Signed Error
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "mse": float(mse),
        "mse_signed": float(mse_signed)
    }

def bootstrap_resample(
    data: np.ndarray,
    n_replicates: int = 1000,
    random_state: Optional[int] = None
) -> np.ndarray:
    """
    Generate bootstrap resamples of the data.

    Args:
        data: Input array.
        n_replicates: Number of bootstrap samples.
        random_state: Random seed for reproducibility.

    Returns:
        Array of shape (n_replicates, n_samples) containing resamples.
    """
    rng = np.random.default_rng(random_state)
    n_samples = len(data)
    return rng.choice(data, size=(n_replicates, n_samples), replace=True)

def bootstrap_mean(
    data: np.ndarray,
    n_replicates: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[float, float]:
    """
    Compute bootstrap confidence interval for the mean.

    Args:
        data: Input array.
        n_replicates: Number of bootstrap samples.
        random_state: Random seed.

    Returns:
        Tuple (lower_95, upper_95).
    """
    resamples = bootstrap_resample(data, n_replicates, random_state)
    means = np.mean(resamples, axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))

def bootstrap_mae(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray],
    n_replicates: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[float, float]:
    """
    Compute bootstrap confidence interval for MAE.

    Args:
        y_true: Reference values.
        y_pred: Predicted values.
        n_replicates: Number of bootstrap samples.
        random_state: Random seed.

    Returns:
        Tuple (lower_95, upper_95).
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    errors = np.abs(y_pred - y_true)
    
    resamples = bootstrap_resample(errors, n_replicates, random_state)
    maes = np.mean(resamples, axis=1)
    
    return float(np.percentile(maes, 2.5)), float(np.percentile(maes, 97.5))
