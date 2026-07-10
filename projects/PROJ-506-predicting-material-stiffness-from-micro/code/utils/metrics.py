"""
Utility metrics functions for evaluating model performance.

Provides Mean Absolute Error (MAE), Mean Squared Error (MSE),
and R-squared (R2) calculation functions.
"""

import numpy as np
from typing import Union, List


def mean_absolute_error(y_true: Union[np.ndarray, List[float]],
                        y_pred: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate Mean Absolute Error (MAE).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: The mean absolute error.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")

    return float(np.mean(np.abs(y_true - y_pred)))


def mean_squared_error(y_true: Union[np.ndarray, List[float]],
                       y_pred: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate Mean Squared Error (MSE).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: The mean squared error.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")

    return float(np.mean((y_true - y_pred) ** 2))


def r2_score(y_true: Union[np.ndarray, List[float]],
             y_pred: Union[np.ndarray, List[float]]) -> float:
    """
    Calculate R-squared (Coefficient of Determination).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: The R-squared value.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} vs y_pred {y_pred.shape}")

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        # If variance of y_true is 0, R2 is undefined (or 0 by convention)
        # If predictions are also perfect (ss_res=0), return 1.0
        if ss_res == 0:
            return 1.0
        return 0.0

    return float(1 - (ss_res / ss_tot))