"""
metrics.py - Statistical evaluation and comparison metrics for molecular reactivity models.

Implements:
- MSE (Mean Squared Error)
- MAE (Mean Absolute Error)
- Pearson R (Correlation Coefficient)
- Paired t-test (Primary statistical comparison per FR-006)
- Wilcoxon signed-rank test (Sensitivity analysis)
"""

import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_mse(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Squared Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: MSE value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    if len(y_true) == 0:
        raise ValueError("Input arrays are empty.")

    return float(np.mean((y_true - y_pred) ** 2))


def calculate_mae(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Absolute Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: MAE value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    if len(y_true) == 0:
        raise ValueError("Input arrays are empty.")

    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_pearson_r(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Pearson Correlation Coefficient.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        float: Pearson R value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if len(y_true) != len(y_pred):
        raise ValueError(f"Length mismatch: y_true ({len(y_true)}) != y_pred ({len(y_pred)})")
    if len(y_true) < 2:
        raise ValueError("Need at least 2 samples to calculate correlation.")

    corr, _ = stats.pearsonr(y_true, y_pred)
    if np.isnan(corr):
        # Handle constant arrays case
        logger.warning("Pearson correlation is NaN (likely constant values). Returning 0.0.")
        return 0.0
    return float(corr)


def paired_t_test(y_pred_model_a: Union[List[float], np.ndarray],
                  y_pred_model_b: Union[List[float], np.ndarray],
                  y_true: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Perform a paired t-test on the errors of two models.
    This is the PRIMARY statistical test per FR-006 to compare GNN vs RF.

    The test compares the residuals (errors) of Model A vs Model B.
    Null Hypothesis: The mean difference in errors is zero.

    Args:
        y_pred_model_a: Predictions from Model A.
        y_pred_model_b: Predictions from Model B.
        y_true: Ground truth values.

    Returns:
        Dict containing 't_statistic' and 'p_value'.
    """
    y_true = np.asarray(y_true)
    y_pred_a = np.asarray(y_pred_model_a)
    y_pred_b = np.asarray(y_pred_model_b)

    if not (len(y_true) == len(y_pred_a) == len(y_pred_b)):
        raise ValueError("Input arrays must all have the same length.")
    if len(y_true) < 2:
        raise ValueError("Need at least 2 samples to perform a t-test.")

    # Calculate residuals (errors)
    errors_a = y_true - y_pred_a
    errors_b = y_true - y_pred_b

    # Paired t-test on the errors
    t_stat, p_val = stats.ttest_rel(errors_a, errors_b)

    logger.info(f"Paired T-Test Results: t={t_stat:.4f}, p={p_val:.4e}")

    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val)
    }


def wilcoxon_signed_rank_test(y_pred_model_a: Union[List[float], np.ndarray],
                              y_pred_model_b: Union[List[float], np.ndarray],
                              y_true: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Perform a Wilcoxon signed-rank test on the errors of two models.
    This is the SENSITIVITY analysis test.

    Non-parametric alternative to the paired t-test.
    Null Hypothesis: The distribution of differences in errors is symmetric around zero.

    Args:
        y_pred_model_a: Predictions from Model A.
        y_pred_model_b: Predictions from Model B.
        y_true: Ground truth values.

    Returns:
        Dict containing 'statistic' and 'p_value'.
    """
    y_true = np.asarray(y_true)
    y_pred_a = np.asarray(y_pred_model_a)
    y_pred_b = np.asarray(y_pred_model_b)

    if not (len(y_true) == len(y_pred_a) == len(y_pred_b)):
        raise ValueError("Input arrays must all have the same length.")
    if len(y_true) < 2:
        raise ValueError("Need at least 2 samples to perform Wilcoxon test.")

    # Calculate residuals (errors)
    errors_a = y_true - y_pred_a
    errors_b = y_true - y_pred_b

    # Wilcoxon signed-rank test
    # Note: stats.wilcoxon returns (statistic, pvalue)
    try:
        stat, p_val = stats.wilcoxon(errors_a, errors_b)
    except ValueError as e:
        # Handle cases where differences are all zero or other edge cases
        logger.warning(f"Wilcoxon test failed: {e}. Returning NaN.")
        return {
            "statistic": float('nan'),
            "p_value": float('nan')
        }

    logger.info(f"Wilcoxon Signed-Rank Test Results: statistic={stat:.4f}, p={p_val:.4e}")

    return {
        "statistic": float(stat),
        "p_value": float(p_val)
    }


def evaluate_model(y_true: Union[List[float], np.ndarray],
                   y_pred: Union[List[float], np.ndarray],
                   model_name: str = "Model") -> Dict[str, float]:
    """
    Calculate a standard set of metrics for a single model.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        model_name: Name of the model for logging.

    Returns:
        Dict containing MSE, MAE, and Pearson R.
    """
    mse = calculate_mse(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    pearson_r = calculate_pearson_r(y_true, y_pred)

    logger.info(f"Evaluation for {model_name}: MSE={mse:.4f}, MAE={mae:.4f}, Pearson R={pearson_r:.4f}")

    return {
        "model_name": model_name,
        "mse": mse,
        "mae": mae,
        "pearson_r": pearson_r
    }


def compare_models(y_true: Union[List[float], np.ndarray],
                   y_pred_model_a: Union[List[float], np.ndarray],
                   y_pred_model_b: Union[List[float], np.ndarray],
                   name_a: str = "Model A",
                   name_b: str = "Model B") -> Dict[str, Any]:
    """
    Perform a full statistical comparison between two models.
    Includes individual metrics and paired statistical tests.

    Args:
        y_true: Ground truth values.
        y_pred_model_a: Predictions from Model A.
        y_pred_model_b: Predictions from Model B.
        name_a: Name of Model A.
        name_b: Name of Model B.

    Returns:
        Dict containing individual metrics and test results.
    """
    metrics_a = evaluate_model(y_true, y_pred_model_a, name_a)
    metrics_b = evaluate_model(y_true, y_pred_model_b, name_b)

    t_test_result = paired_t_test(y_pred_model_a, y_pred_model_b, y_true)
    wilcoxon_result = wilcoxon_signed_rank_test(y_pred_model_a, y_pred_model_b, y_true)

    return {
        "model_a_metrics": metrics_a,
        "model_b_metrics": metrics_b,
        "paired_t_test": t_test_result,
        "wilcoxon_test": wilcoxon_result
    }