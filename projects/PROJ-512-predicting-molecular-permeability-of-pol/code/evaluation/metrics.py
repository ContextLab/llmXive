"""
Evaluation metrics for molecular permeability prediction.

Computes R², MAE, and Pearson correlation coefficient between
predicted and actual log-permeability values.
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Tuple, Union

import numpy as np
from scipy import stats

# Import project utilities
from data.utils import setup_logging, ensure_seed_initialized

# Ensure logging is configured
logger = setup_logging()


def compute_r2(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Compute the coefficient of determination (R²).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        R² score.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

    if len(y_true) == 0:
        raise ValueError("Input arrays are empty.")

    mean_y = np.mean(y_true)
    ss_tot = np.sum((y_true - mean_y) ** 2)
    ss_res = np.sum((y_true - y_pred) ** 2)

    if ss_tot == 0:
        # If all targets are identical, R² is undefined (0/0).
        # Conventionally return 0.0 or 1.0 depending on whether predictions match.
        if ss_res == 0:
            return 1.0
        return 0.0

    return 1.0 - (ss_res / ss_tot)


def compute_mae(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Compute Mean Absolute Error (MAE).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MAE value.
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

    if len(y_true) == 0:
        raise ValueError("Input arrays are empty.")

    return float(np.mean(np.abs(y_true - y_pred)))


def compute_pearson_correlation(
    y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]
) -> Tuple[float, float]:
    """
    Compute Pearson correlation coefficient and p-value.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Tuple of (correlation coefficient, p-value).
    """
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")

    if len(y_true) < 2:
        raise ValueError("Need at least 2 samples to compute Pearson correlation.")

    # scipy.stats.pearsonr returns (r, p-value)
    r, p_value = stats.pearsonr(y_true, y_pred)
    return float(r), float(p_value)


def evaluate_predictions(
    y_true: List[float], y_pred: List[float]
) -> Dict[str, float]:
    """
    Compute all standard evaluation metrics.

    Args:
        y_true: List of ground truth log-permeability values.
        y_pred: List of predicted log-permeability values.

    Returns:
        Dictionary with keys: 'r2', 'mae', 'pearson_r', 'pearson_p'.
    """
    r2 = compute_r2(y_true, y_pred)
    mae = compute_mae(y_true, y_pred)
    pearson_r, pearson_p = compute_pearson_correlation(y_true, y_pred)

    return {
        "r2": r2,
        "mae": mae,
        "pearson_r": pearson_r,
        "pearson_p": pearson_p,
    }


def main() -> None:
    """
    Example usage: Run evaluation on synthetic test data to verify metrics.

    In the full pipeline, this would be called by the evaluation/reporting
    module with real predictions from the model and baseline.
    """
    ensure_seed_initialized()

    logger.info("Running metrics verification with synthetic test data.")

    # Synthetic test data (small, deterministic)
    y_true = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    y_pred = [1.1, 1.9, 3.2, 3.8, 5.1, 5.9, 7.1, 7.8, 9.1, 9.9]

    metrics = evaluate_predictions(y_true, y_pred)

    logger.info(f"Evaluation Metrics: {metrics}")

    # Verify basic properties
    assert -1.0 <= metrics["r2"] <= 1.5, "R² out of expected range"
    assert metrics["mae"] >= 0.0, "MAE cannot be negative"
    assert -1.0 <= metrics["pearson_r"] <= 1.0, "Pearson r out of range [-1, 1]"
    assert 0.0 <= metrics["pearson_p"] <= 1.0, "P-value out of range [0, 1]"

    logger.info("Metrics verification passed.")


if __name__ == "__main__":
    main()