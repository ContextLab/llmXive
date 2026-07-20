"""
Metric calculators for molecular reactivity prediction.

Provides implementations for Mean Absolute Error (MAE),
Root Mean Squared Error (RMSE), and R-squared (R²).
"""
import math
from typing import List, Union, Optional, Dict, Any

import numpy as np

from src.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_mae(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate Mean Absolute Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: The MAE value.

    Raises:
        ValueError: If inputs are empty or have mismatched lengths.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Input lengths must match: {len(y_true)} vs {len(y_pred)}.")

    y_true_arr = np.array(y_true, dtype=float)
    y_pred_arr = np.array(y_pred, dtype=float)

    return float(np.mean(np.abs(y_true_arr - y_pred_arr)))


def calculate_rmse(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate Root Mean Squared Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: The RMSE value.

    Raises:
        ValueError: If inputs are empty or have mismatched lengths.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Input lengths must match: {len(y_true)} vs {len(y_pred)}.")

    y_true_arr = np.array(y_true, dtype=float)
    y_pred_arr = np.array(y_pred, dtype=float)

    return float(np.sqrt(np.mean((y_true_arr - y_pred_arr) ** 2)))


def calculate_r2(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate R-squared (Coefficient of Determination).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: The R² value.

    Raises:
        ValueError: If inputs are empty, have mismatched lengths, or y_true has zero variance.
    """
    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Input lengths must match: {len(y_true)} vs {len(y_pred)}.")

    y_true_arr = np.array(y_true, dtype=float)
    y_pred_arr = np.array(y_pred, dtype=float)

    ss_res = np.sum((y_true_arr - y_pred_arr) ** 2)
    ss_tot = np.sum((y_true_arr - np.mean(y_true_arr)) ** 2)

    if ss_tot == 0.0:
        if ss_res == 0.0:
            return 1.0
        raise ValueError("y_true has zero variance and predictions are not perfect (R² undefined).")

    return float(1.0 - (ss_res / ss_tot))


def calculate_all_metrics(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> Dict[str, float]:
    """
    Calculate all regression metrics (MAE, RMSE, R²) at once.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        dict: A dictionary containing 'mae', 'rmse', and 'r2'.

    Raises:
        ValueError: Propagated from individual metric calculations if inputs are invalid.
    """
    logger.info("Calculating all metrics for regression evaluation.")
    try:
        mae = calculate_mae(y_true, y_pred)
        rmse = calculate_rmse(y_true, y_pred)
        r2 = calculate_r2(y_true, y_pred)
        logger.info(f"Metrics calculated: MAE={mae:.4f}, RMSE={rmse:.4f}, R2={r2:.4f}")
        return {
            "mae": mae,
            "rmse": rmse,
            "r2": r2
        }
    except ValueError as e:
        logger.error(f"Failed to calculate metrics: {e}")
        raise
