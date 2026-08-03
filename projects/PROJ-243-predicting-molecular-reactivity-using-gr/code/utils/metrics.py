"""
Metrics and Statistical Evaluation Utilities.

This module provides the single source of truth for all statistical tests
and performance metrics used in the molecular reactivity pipeline.

Primary Test: Wilcoxon signed-rank test (non-parametric, handles heteroscedasticity)
Sensitivity Test: Paired t-test (parametric)
"""

import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Union, Optional
import logging

# Configure logging for this module
logger = logging.getLogger(__name__)


def calculate_mse(y_true: Union[List[float], np.ndarray],
                  y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Squared Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MSE value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} != y_pred {y_pred.shape}")

    return float(np.mean((y_true - y_pred) ** 2))


def calculate_mae(y_true: Union[List[float], np.ndarray],
                  y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Absolute Error.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MAE value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} != y_pred {y_pred.shape}")

    return float(np.mean(np.abs(y_true - y_pred)))


def calculate_pearson_r(y_true: Union[List[float], np.ndarray],
                        y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Pearson correlation coefficient.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Pearson r value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} != y_pred {y_pred.shape}")

    if len(y_true) < 2:
        raise ValueError("Pearson correlation requires at least 2 samples.")

    r, _ = stats.pearsonr(y_true, y_pred)
    return float(r)


def wilcoxon_signed_rank_test(y_true: Union[List[float], np.ndarray],
                              y_pred: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Perform Wilcoxon signed-rank test (PRIMARY statistical test).

    This non-parametric test is robust to heteroscedasticity and non-normality
    of residuals, making it suitable for molecular property predictions.

    Args:
        y_true: Ground truth values (e.g., experimental rates).
        y_pred: Predicted values.

    Returns:
        Dictionary containing 'statistic' and 'pvalue'.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} != y_pred {y_pred.shape}")

    if len(y_true) < 2:
        raise ValueError("Wilcoxon test requires at least 2 samples.")

    # The test checks if the median difference is zero.
    # We test the residuals (y_true - y_pred) against 0.
    residuals = y_true - y_pred
    statistic, pvalue = stats.wilcoxon(residuals)

    logger.info(f"Wilcoxon test: statistic={statistic:.4f}, p-value={pvalue:.4e}")

    return {
        "statistic": float(statistic),
        "pvalue": float(pvalue)
    }


def paired_t_test(y_true: Union[List[float], np.ndarray],
                  y_pred: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Perform Paired t-test (SENSITIVITY statistical test).

    This parametric test assumes normality of differences. It is used as a
    sensitivity check against the primary Wilcoxon test.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Dictionary containing 'statistic' and 'pvalue'.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if y_true.shape != y_pred.shape:
        raise ValueError(f"Shape mismatch: y_true {y_true.shape} != y_pred {y_pred.shape}")

    if len(y_true) < 2:
        raise ValueError("Paired t-test requires at least 2 samples.")

    # We test the residuals (y_true - y_pred) against 0.
    residuals = y_true - y_pred
    statistic, pvalue = stats.ttest_rel(residuals, np.zeros_like(residuals))

    logger.info(f"Paired t-test: statistic={statistic:.4f}, p-value={pvalue:.4e}")

    return {
        "statistic": float(statistic),
        "pvalue": float(pvalue)
    }


def evaluate_model(y_true: Union[List[float], np.ndarray],
                   y_pred: Union[List[float], np.ndarray],
                   alpha: float = 0.05) -> Dict[str, Any]:
    """
    Evaluate a model's performance using all defined metrics and tests.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.
        alpha: Significance level for hypothesis tests.

    Returns:
        Dictionary containing MSE, MAE, Pearson R, and statistical test results.
    """
    mse = calculate_mse(y_true, y_pred)
    mae = calculate_mae(y_true, y_pred)
    pearson_r = calculate_pearson_r(y_true, y_pred)

    wilcoxon_result = wilcoxon_signed_rank_test(y_true, y_pred)
    ttest_result = paired_t_test(y_true, y_pred)

    # Apply Bonferroni correction if multiple comparisons were made (context dependent)
    # Here we just report the raw p-values and the adjusted alpha if needed by caller
    # The caller (T024c) handles the specific Bonferroni logic for the final report
    # based on the number of models being compared.

    return {
        "mse": mse,
        "mae": mae,
        "pearson_r": pearson_r,
        "statistical_tests": {
            "primary_test": "wilcoxon",
            "sensitivity_test": "t-test",
            "wilcoxon": wilcoxon_result,
            "ttest": ttest_result,
            "alpha": alpha
        }
    }


def compare_models(y_true: Union[List[float], np.ndarray],
                   predictions: Dict[str, List[float]],
                   alpha: float = 0.05) -> Dict[str, Any]:
    """
    Compare multiple models against ground truth.

    Args:
        y_true: Ground truth values.
        predictions: Dictionary mapping model names to their prediction arrays.
        alpha: Significance level.

    Returns:
        Dictionary containing metrics for each model and pairwise comparisons if needed.
        Currently returns per-model metrics and tests.
    """
    results = {}

    for model_name, y_pred in predictions.items():
        results[model_name] = evaluate_model(y_true, y_pred, alpha)

    logger.info(f"Evaluated {len(predictions)} models.")

    return results