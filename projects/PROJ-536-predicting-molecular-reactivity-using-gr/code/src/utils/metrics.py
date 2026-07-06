"""
Metric calculators for molecular reactivity prediction.

Provides functions to calculate Mean Absolute Error (MAE),
Root Mean Squared Error (RMSE), and R-squared (R²) for regression tasks.
"""

import math
from typing import List, Union, Optional

import numpy as np

from src.utils.logging import get_logger

logger = get_logger(__name__)


def calculate_mae(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate Mean Absolute Error (MAE).

    Args:
        y_true: List or array of true values.
        y_pred: List or array of predicted values.

    Returns:
        float: The MAE value.

    Raises:
        ValueError: If inputs are empty or have mismatched lengths.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Input arrays must have the same length. "
            f"Got {len(y_true)} and {len(y_pred)}."
        )

    mae = np.mean(np.abs(y_true - y_pred))
    logger.debug(f"Calculated MAE: {mae:.6f}")
    return float(mae)


def calculate_rmse(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate Root Mean Squared Error (RMSE).

    Args:
        y_true: List or array of true values.
        y_pred: List or array of predicted values.

    Returns:
        float: The RMSE value.

    Raises:
        ValueError: If inputs are empty or have mismatched lengths.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Input arrays must have the same length. "
            f"Got {len(y_true)} and {len(y_pred)}."
        )

    mse = np.mean((y_true - y_pred) ** 2)
    rmse = math.sqrt(mse)
    logger.debug(f"Calculated RMSE: {rmse:.6f}")
    return float(rmse)


def calculate_r2(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate R-squared (Coefficient of Determination).

    Args:
        y_true: List or array of true values.
        y_pred: List or array of predicted values.

    Returns:
        float: The R² value.

    Raises:
        ValueError: If inputs are empty, have mismatched lengths,
                    or if variance of y_true is zero.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    if len(y_true) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Input arrays must have the same length. "
            f"Got {len(y_true)} and {len(y_pred)}."
        )

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)

    if ss_tot == 0:
        raise ValueError(
            "Variance of y_true is zero. R² is undefined for constant targets."
        )

    r2 = 1 - (ss_res / ss_tot)
    logger.debug(f"Calculated R²: {r2:.6f}")
    return float(r2)


def calculate_all_metrics(
    y_true: Union[List[float], np.ndarray],
    y_pred: Union[List[float], np.ndarray]
) -> dict:
    """
    Calculate all regression metrics (MAE, RMSE, R²) at once.

    Args:
        y_true: List or array of true values.
        y_pred: List or array of predicted values.

    Returns:
        dict: Dictionary containing 'mae', 'rmse', and 'r2'.

    Raises:
        ValueError: If inputs are invalid for any metric calculation.
    """
    return {
        "mae": calculate_mae(y_true, y_pred),
        "rmse": calculate_rmse(y_true, y_pred),
        "r2": calculate_r2(y_true, y_pred)
    }
