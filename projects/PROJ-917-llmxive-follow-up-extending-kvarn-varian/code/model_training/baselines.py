"""
Baseline predictors for scaling factor estimation.

This module implements closed-form baselines to compare against the learned
Static Prior (MLP) model. Specifically, it implements the inverse-variance
heuristic derived from the KVarN paper's theoretical analysis.
"""

import numpy as np
from typing import Union, List, Tuple

def predict_closed_form_variance(moments: Union[np.ndarray, List[float], float]) -> np.ndarray:
    """
    Predict scaling factor using the closed-form inverse-variance baseline: s = 1 / variance.

    This implements the theoretical baseline where the scaling factor is inversely
    proportional to the variance of the attention matrix. This serves as a lower-bound
    heuristic for the static prior model.

    Args:
        moments: Input statistical moments.
            - If a single float: interpreted as `variance`.
            - If a 1D array/list of length 2: interpreted as [mean, variance].
            - If a 2D array (N, 2): interpreted as N rows of [mean, variance].

    Returns:
        np.ndarray: Predicted scaling factors (s = 1 / variance).
            - For scalar input: scalar result.
            - For array input: array of shape (N,) or (1,).

    Raises:
        ValueError: If the input shape is invalid or variance is non-positive.
        ZeroDivisionError: If variance is exactly zero (after epsilon floor check).
    """
    moments_arr = np.asarray(moments, dtype=np.float32)

    # Determine variance column based on input shape
    if moments_arr.ndim == 0:
        # Scalar input: assume it is the variance directly
        variance = moments_arr
    elif moments_arr.ndim == 1:
        if len(moments_arr) == 2:
            # [mean, variance]
            variance = moments_arr[1]
        elif len(moments_arr) == 1:
            variance = moments_arr[0]
        else:
            raise ValueError(f"Invalid 1D input length: {len(moments_arr)}. Expected 1 or 2.")
    elif moments_arr.ndim == 2:
        if moments_arr.shape[1] == 2:
            # (N, 2) -> [mean, variance]
            variance = moments_arr[:, 1]
        elif moments_arr.shape[1] == 1:
            variance = moments_arr[:, 0]
        else:
            raise ValueError(f"Invalid 2D input columns: {moments_arr.shape[1]}. Expected 1 or 2.")
    else:
        raise ValueError(f"Invalid input dimensions: {moments_arr.ndim}. Expected 0, 1, or 2.")

    # Apply epsilon floor to prevent division by zero
    # Using a safe epsilon consistent with config defaults (1e-6)
    epsilon_floor = 1e-6
    variance_safe = np.maximum(variance, epsilon_floor)

    # Compute inverse variance
    predictions = 1.0 / variance_safe

    # Ensure output is float32 for consistency with model training
    return predictions.astype(np.float32)

def evaluate_baseline_mse(predictions: np.ndarray, ground_truth: np.ndarray) -> float:
    """
    Calculate Mean Squared Error between baseline predictions and ground truth.

    Args:
        predictions: Predicted scaling factors.
        ground_truth: True scaling factors.

    Returns:
        float: Mean Squared Error.
    """
    predictions = np.asarray(predictions, dtype=np.float32)
    ground_truth = np.asarray(ground_truth, dtype=np.float32)

    if predictions.shape != ground_truth.shape:
        raise ValueError(f"Shape mismatch: predictions {predictions.shape} vs ground_truth {ground_truth.shape}")

    mse = np.mean((predictions - ground_truth) ** 2)
    return float(mse)

def predict_batch_variance(moments_batch: np.ndarray) -> np.ndarray:
    """
    Wrapper for batch prediction using the closed-form baseline.

    Args:
        moments_batch: Array of shape (N, 2) containing [mean, variance] for N samples.

    Returns:
        np.ndarray: Array of shape (N,) containing predicted scaling factors.
    """
    return predict_closed_form_variance(moments_batch)
