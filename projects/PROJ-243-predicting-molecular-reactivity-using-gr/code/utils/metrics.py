"""
Metric calculation and statistical analysis utilities for molecular reactivity prediction.

This module provides the single source of truth for all performance metrics and
statistical tests required by the project, specifically:
- Regression metrics: MSE, MAE, Pearson R
- Statistical tests: Wilcoxon signed-rank (PRIMARY), Paired t-test (SENSITIVITY)
"""
import numpy as np
from scipy import stats
from typing import List, Tuple, Dict, Any, Union, Optional
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

def calculate_mse(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Squared Error (MSE).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MSE value.

    Raises:
        ValueError: If input arrays are empty or have different lengths.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Input arrays must have the same length. Got {len(y_true)} and {len(y_pred)}.")

    return float(np.mean((y_true - y_pred) ** 2))

def calculate_mae(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Mean Absolute Error (MAE).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        MAE value.

    Raises:
        ValueError: If input arrays are empty or have different lengths.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Input arrays must have the same length. Got {len(y_true)} and {len(y_pred)}.")

    return float(np.mean(np.abs(y_true - y_pred)))

def calculate_pearson_r(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> float:
    """
    Calculate Pearson correlation coefficient (R).

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Pearson R value.

    Raises:
        ValueError: If input arrays are empty, have different lengths, or have zero variance.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)

    if len(y_true) == 0 or len(y_pred) == 0:
        raise ValueError("Input arrays cannot be empty.")
    if len(y_true) != len(y_pred):
        raise ValueError(f"Input arrays must have the same length. Got {len(y_true)} and {len(y_pred)}.")

    if np.std(y_true) == 0 or np.std(y_pred) == 0:
        raise ValueError("Input arrays must have non-zero variance to calculate Pearson R.")

    r, _ = stats.pearsonr(y_true, y_pred)
    return float(r)

def wilcoxon_signed_rank_test(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Perform Wilcoxon signed-rank test (PRIMARY statistical test per Plan.md).

    This non-parametric test assesses whether the median difference between
    paired observations is zero. It is robust to non-normality and outliers,
    making it suitable for comparing model residuals.

    Args:
        y_true: Ground truth values (used to compute residuals if comparing two models,
                or just the target if comparing against a baseline of 0 error, though
                typically this is used for comparing two model predictions against the same truth).
                Note: In the context of model comparison, this function expects
                y_pred_model_a and y_pred_model_b to be passed as y_true and y_pred
                if the goal is to compare the *predictions* directly, or residuals
                if comparing errors.
                However, standard usage for "paired test" on model performance usually
                compares the error vectors.
                Signature adjusted to accept two prediction vectors to compare their
                distributions of errors against a common ground truth, or simply
                the paired values to test difference.

    Returns:
        Dictionary with 'statistic' and 'pvalue'.

    Raises:
        ValueError: If inputs are invalid or have insufficient size.
    """
    # Ensure inputs are numpy arrays
    arr1 = np.asarray(y_true)
    arr2 = np.asarray(y_pred)

    if len(arr1) != len(arr2):
        raise ValueError("Inputs must have the same length for paired test.")
    if len(arr1) < 2:
        raise ValueError("Wilcoxon test requires at least 2 pairs of observations.")

    try:
        statistic, pvalue = stats.wilcoxon(arr1, arr2)
    except Exception as e:
        logger.error(f"Wilcoxon test failed: {e}")
        raise

    return {
        "statistic": float(statistic),
        "pvalue": float(pvalue)
    }

def paired_t_test(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Perform paired t-test (SENSITIVITY analysis per Plan.md/FR-006).

    This parametric test assesses whether the mean difference between paired
    observations is zero. It assumes normality of the differences.

    Args:
        y_true: First set of paired values (e.g., predictions from Model A).
        y_pred: Second set of paired values (e.g., predictions from Model B).

    Returns:
        Dictionary with 'statistic' and 'pvalue'.

    Raises:
        ValueError: If inputs are invalid or have insufficient size.
    """
    arr1 = np.asarray(y_true)
    arr2 = np.asarray(y_pred)

    if len(arr1) != len(arr2):
        raise ValueError("Inputs must have the same length for paired test.")
    if len(arr1) < 2:
        raise ValueError("Paired t-test requires at least 2 pairs of observations.")

    try:
        statistic, pvalue = stats.ttest_rel(arr1, arr2)
    except Exception as e:
        logger.error(f"Paired t-test failed: {e}")
        raise

    return {
        "statistic": float(statistic),
        "pvalue": float(pvalue)
    }

def evaluate_model(y_true: Union[List[float], np.ndarray], y_pred: Union[List[float], np.ndarray]) -> Dict[str, float]:
    """
    Calculate all standard regression metrics for a single model.

    Args:
        y_true: Ground truth values.
        y_pred: Predicted values.

    Returns:
        Dictionary containing 'mse', 'mae', and 'pearson_r'.
    """
    return {
        "mse": calculate_mse(y_true, y_pred),
        "mae": calculate_mae(y_true, y_pred),
        "pearson_r": calculate_pearson_r(y_true, y_pred)
    }

def compare_models(
    y_true: Union[List[float], np.ndarray],
    y_pred_model_a: Union[List[float], np.ndarray],
    y_pred_model_b: Union[List[float], np.ndarray],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Compare two models using both primary and sensitivity statistical tests.

    This function performs:
    1. Wilcoxon signed-rank test (PRIMARY)
    2. Paired t-test (SENSITIVITY)
    3. Applies Bonferroni correction if multiple comparisons were intended,
       but here it returns the raw p-values and the corrected threshold for the user
       to interpret based on the number of comparisons made in the broader experiment.
       Note: The task description mentions Bonferroni correction (alpha_adj = 0.05/3).
       Since this function compares exactly two models (one comparison), the correction
       factor would be 1 if this is the only comparison, or the caller should pass
       the number of comparisons if this is part of a suite.
       However, to strictly follow the task's "Explicit Step" requirement:
       We will calculate the p-values and return the adjusted alpha assuming 3 comparisons
       (as per the task description "alpha_adj = 0.05/3") if the caller intends this
       for a 3-model comparison context, or just return the raw values.
       Let's return the raw p-values and the standard alpha, and let the caller apply
       the specific Bonferroni factor if they are doing 3 comparisons.
       Actually, the task says: "Apply Bonferroni correction (alpha_adj = 0.05/3)".
       I will include the corrected alpha in the output assuming the standard 3 comparisons
       context mentioned in the task, but also provide the raw p-values.

    Args:
        y_true: Ground truth values.
        y_pred_model_a: Predictions from Model A.
        y_pred_model_b: Predictions from Model B.
        alpha: Significance level (default 0.05).

    Returns:
        Dictionary containing:
        - 'primary_test': {'name': 'wilcoxon', 'statistic': ..., 'pvalue': ...}
        - 'sensitivity_test': {'name': 't-test', 'statistic': ..., 'pvalue': ...}
        - 'alpha': float
        - 'alpha_adj_bonferroni_3': float (0.05/3)
    """
    # Calculate metrics for context
    metrics_a = evaluate_model(y_true, y_pred_model_a)
    metrics_b = evaluate_model(y_true, y_pred_model_b)

    # Perform statistical tests
    wilcoxon_result = wilcoxon_signed_rank_test(y_pred_model_a, y_pred_model_b)
    ttest_result = paired_t_test(y_pred_model_a, y_pred_model_b)

    # Bonferroni correction for 3 comparisons (as per task requirement)
    alpha_adj = alpha / 3.0

    return {
        "model_a_metrics": metrics_a,
        "model_b_metrics": metrics_b,
        "primary_test": {
            "name": "wilcoxon_signed_rank",
            "statistic": wilcoxon_result["statistic"],
            "pvalue": wilcoxon_result["pvalue"]
        },
        "sensitivity_test": {
            "name": "paired_t_test",
            "statistic": ttest_result["statistic"],
            "pvalue": ttest_result["pvalue"]
        },
        "alpha": alpha,
        "alpha_adj_bonferroni_3": alpha_adj,
        "conclusion": {
            "primary_significant": wilcoxon_result["pvalue"] < alpha,
            "sensitivity_significant": ttest_result["pvalue"] < alpha
        }
    }