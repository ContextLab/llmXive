"""
Statistical tests for model comparison.
Implements Nadeau & Bengio corrected resampled t-test.
"""
import numpy as np
import logging
from typing import List, Tuple, Optional

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)


def nadeau_bengio_ttest(
    model1_scores: np.ndarray,
    model2_scores: np.ndarray,
    n_train: int,
    n_test: int,
    alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Perform the Nadeau & Bengio corrected resampled t-test.

    This test accounts for the variance inflation due to overlapping
    training and test sets in cross-validation.

    Formula:
      t = (mean_diff) / sqrt( (1/k + n_test/n_total) * var_diff )

    Where:
      k = number of folds (outer loop iterations)
      n_test = size of test set per fold
      n_total = total number of samples
      mean_diff = mean of (score_model1 - score_model2) across folds
      var_diff = variance of the differences across folds

    Args:
        model1_scores: Array of performance scores (e.g., R2) for model 1 (shape: k,)
        model2_scores: Array of performance scores for model 2 (shape: k,)
        n_train: Number of training samples per fold
        n_test: Number of test samples per fold
        alpha: Significance level (default 0.05)

    Returns:
        t_statistic: The calculated t-value
        p_value: Two-tailed p-value
        is_significant: Boolean indicating if p < alpha
    """
    if len(model1_scores) != len(model2_scores):
        raise ValueError("Model scores must have the same length.")

    k = len(model1_scores)
    n_total = n_train + n_test

    # Calculate differences
    diffs = model1_scores - model2_scores
    mean_diff = np.mean(diffs)
    var_diff = np.var(diffs, ddof=1)  # Sample variance

    # Nadeau & Bengio correction factor
    # The variance of the mean difference is inflated by the correlation
    # between folds. The correction term is (1/k + n_test/n_total).
    # Standard error of the mean difference:
    se_mean_diff = np.sqrt( (1.0 / k + float(n_test) / float(n_total)) * var_diff )

    if se_mean_diff == 0:
        # If there is no variance in differences, the t-stat is undefined (infinite)
        # If mean_diff is 0, p=1. If mean_diff != 0, p=0.
        if mean_diff == 0:
            return 0.0, 1.0, False
        else:
            # Effectively infinite t-stat
            logger.warning("Standard error is zero. T-statistic is infinite.")
            return float('inf'), 0.0, (abs(mean_diff) > 0)

    t_stat = mean_diff / se_mean_diff

    # Degrees of freedom
    # For the corrected t-test, the effective degrees of freedom is often
    # approximated as k-1 (number of folds - 1).
    df = k - 1

    # Calculate two-tailed p-value using the t-distribution
    # We approximate the CDF of the t-distribution manually or use scipy if available.
    # Since scipy is a standard dependency in this project, we use it for accuracy.
    try:
        from scipy import stats
        p_value = 2 * stats.t.sf(np.abs(t_stat), df)
    except ImportError:
        # Fallback to a simple approximation if scipy is not available
        # This is less accurate but ensures the code runs.
        # Using a normal approximation for large df, but this is a fallback.
        # For strict compliance, scipy is preferred.
        logger.warning("scipy not found. Using normal approximation for p-value.")
        from math import erf, sqrt
        # Normal approximation
        z = t_stat
        p_value = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))

    is_significant = p_value < alpha

    logger.info(f"Nadeau-Bengio t-test: t={t_stat:.4f}, p={p_value:.4f}, significant={is_significant}")

    return t_stat, p_value, is_significant


def run_model_comparison_test(
    model1_scores: List[float],
    model2_scores: List[float],
    n_train: int,
    n_test: int,
    model1_name: str = "Model 1",
    model2_name: str = "Model 2",
    alpha: float = 0.05
) -> dict:
    """
    Run the Nadeau & Bengio t-test and return a summary dictionary.

    Args:
        model1_scores: List of scores for model 1
        model2_scores: List of scores for model 2
        n_train: Training set size per fold
        n_test: Test set size per fold
        model1_name: Name of model 1
        model2_name: Name of model 2
        alpha: Significance level

    Returns:
        dict: Summary of the test results
    """
    arr1 = np.array(model1_scores)
    arr2 = np.array(model2_scores)

    t_stat, p_value, is_significant = nadeau_bengio_ttest(
        arr1, arr2, n_train, n_test, alpha
    )

    mean1 = np.mean(arr1)
    mean2 = np.mean(arr2)
    diff = mean1 - mean2

    return {
        "model1_name": model1_name,
        "model2_name": model2_name,
        "model1_mean": float(mean1),
        "model2_mean": float(mean2),
        "mean_difference": float(diff),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "alpha": alpha,
        "is_significant": is_significant,
        "folds": len(model1_scores),
        "n_train": n_train,
        "n_test": n_test
    }
