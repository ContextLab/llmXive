"""
Evaluation metric utilities for the molecular dipole moment prediction project.

Provides simple implementations of Mean Absolute Error (MAE) and Root Mean Squared
Error (RMSE) that operate on NumPy arrays or array‑like sequences, as well as a
convenience ``evaluate`` function returning both metrics in a dictionary.
"""

from __future__ import annotations

import numpy as np
from typing import Sequence, Dict

__all__ = ["mae", "rmse", "evaluate"]


def _to_numpy(arr: Sequence[float] | np.ndarray) -> np.ndarray:
    """
    Convert an input sequence to a 1‑D NumPy array of type float64.

    Parameters
    ----------
    arr : Sequence[float] | np.ndarray
        Input data.

    Returns
    -------
    np.ndarray
        1‑D float64 array.
    """
    np_arr = np.asarray(arr, dtype=np.float64)
    if np_arr.ndim != 1:
        raise ValueError("Input must be a one‑dimensional array or sequence.")
    return np_arr


def mae(y_true: Sequence[float] | np.ndarray,
        y_pred: Sequence[float] | np.ndarray) -> float:
    """
    Compute Mean Absolute Error (MAE) between true and predicted values.

    Parameters
    ----------
    y_true : array‑like of shape (n_samples,)
        Ground‑truth target values.
    y_pred : array‑like of shape (n_samples,)
        Predicted target values.

    Returns
    -------
    float
        The MAE value.
    """
    y_true_np = _to_numpy(y_true)
    y_pred_np = _to_numpy(y_pred)

    if y_true_np.shape != y_pred_np.shape:
        raise ValueError("y_true and y_pred must have the same shape.")

    absolute_errors = np.abs(y_true_np - y_pred_np)
    return float(np.mean(absolute_errors))


def rmse(y_true: Sequence[float] | np.ndarray,
         y_pred: Sequence[float] | np.ndarray) -> float:
    """
    Compute Root Mean Squared Error (RMSE) between true and predicted values.

    Parameters
    ----------
    y_true : array‑like of shape (n_samples,)
        Ground‑truth target values.
    y_pred : array‑like of shape (n_samples,)
        Predicted target values.

    Returns
    -------
    float
        The RMSE value.
    """
    y_true_np = _to_numpy(y_true)
    y_pred_np = _to_numpy(y_pred)

    if y_true_np.shape != y_pred_np.shape:
        raise ValueError("y_true and y_pred must have the same shape.")

    squared_errors = (y_true_np - y_pred_np) ** 2
    mse = np.mean(squared_errors)
    return float(np.sqrt(mse))


def evaluate(y_true: Sequence[float] | np.ndarray,
             y_pred: Sequence[float] | np.ndarray) -> Dict[str, float]:
    """
    Compute both MAE and RMSE for a set of predictions.

    This convenience wrapper is useful in training / evaluation scripts where
    both metrics are required simultaneously.

    Parameters
    ----------
    y_true : array‑like of shape (n_samples,)
        Ground‑truth target values.
    y_pred : array‑like of shape (n_samples,)
        Predicted target values.

    Returns
    -------
    dict
        Dictionary with keys ``"mae"`` and ``"rmse"`` mapping to the respective
        metric values.
    """
    return {"mae": mae(y_true, y_pred), "rmse": rmse(y_true, y_pred)}