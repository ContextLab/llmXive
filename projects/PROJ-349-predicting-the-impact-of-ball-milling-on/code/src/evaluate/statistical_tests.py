"""
Statistical tests for model comparison.

Implements the Nadeau & Bengio corrected resampled t-test to account for
the overlap between training and test sets in cross-validation.

This implementation does NOT use scipy.stats.ttest_rel directly but
manually calculates the corrected variance term.
"""

import logging
from typing import List, Tuple, Optional

import numpy as np

from src.utils.logger import get_module_logger

logger: logging.Logger = get_module_logger(__name__)


def nadeau_bengio_ttest(
    scores_model_a: np.ndarray,
    scores_model_b: np.ndarray,
    n_folds: int,
    n_train: int,
    n_test: int,
    alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Perform the Nadeau & Bengio corrected resampled t-test.

    This test compares the performance of two models across k-fold cross-validation,
    accounting for the dependency between folds due to overlapping training sets.

    The corrected variance formula is:
    var_corrected = var(diff) * (1/k + n_test/n_total)

    Where:
    - var(diff) is the sample variance of the differences
    - k is the number of folds (n_folds)
    - n_test is the size of the test set per fold
    - n_total is the total number of samples (n_train + n_test)

    Args:
        scores_model_a: Array of shape (n_folds,) containing performance scores for model A.
        scores_model_b: Array of shape (n_folds,) containing performance scores for model B.
        n_folds: Number of folds used in cross-validation.
        n_train: Number of samples in the training set per fold.
        n_test: Number of samples in the test set per fold.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple containing:
            - t_statistic: The calculated t-statistic.
            - p_value: The two-tailed p-value.
            - is_significant: Boolean indicating if the difference is significant at alpha.

    Raises:
        ValueError: If input arrays have mismatched lengths or invalid dimensions.
    """
    scores_model_a = np.asarray(scores_model_a)
    scores_model_b = np.asarray(scores_model_b)

    if scores_model_a.shape != scores_model_b.shape:
        raise ValueError(
            f"Score arrays must have the same shape. "
            f"Got {scores_model_a.shape} and {scores_model_b.shape}"
        )

    if scores_model_a.ndim != 1:
        raise ValueError(f"Score arrays must be 1D. Got {scores_model_a.ndim}D")

    if len(scores_model_a) != n_folds:
        logger.warning(
            f"Length of score arrays ({len(scores_model_a)}) does not match n_folds ({n_folds}). "
            "Using length of arrays as n_folds."
        )
        n_folds = len(scores_model_a)

    # Calculate the difference in scores for each fold
    # Positive difference means Model A performed better
    differences = scores_model_a - scores_model_b

    # Mean difference
    mean_diff = np.mean(differences)

    # Sample variance of differences
    # Using ddof=1 for sample variance (unbiased estimator)
    var_diff = np.var(differences, ddof=1)
    n = n_folds

    # Nadeau & Bengio correction factor
    # The variance of the mean difference in cross-validation is inflated because
    # the test sets are not independent (training sets overlap).
    # Correction: var_corrected = var_diff * (1/n + n_test / (n_train + n_test))
    n_total = n_train + n_test
    correction_factor = (1.0 / n) + (n_test / n_total)

    # Corrected variance of the mean difference
    var_corrected = var_diff * correction_factor

    # Standard error of the mean difference
    se_corrected = np.sqrt(var_corrected)

    # Avoid division by zero
    if se_corrected < 1e-10:
        logger.warning("Corrected standard error is near zero. Setting to small epsilon.")
        se_corrected = 1e-10

    # Calculate t-statistic
    t_statistic = mean_diff / se_corrected

    # Calculate p-value using the t-distribution
    # Degrees of freedom for the t-test in this context is typically n_folds - 1
    df = n_folds - 1

    # Manual calculation of two-tailed p-value using the survival function of t-dist
    # Since we don't want to rely on scipy for the core logic, we implement the
    # approximation or use a simple lookup if available. However, for a robust
    # implementation without scipy's stats module, we can approximate or use
    # a standard library approach if strictly necessary.
    #
    # Given the constraints of standard scientific computing in this project,
    # we will use the standard scipy.stats import ONLY for the p-value calculation
    # as it is a standard library dependency in data science contexts and
    # the core "correction" logic is implemented manually.
    #
    # If scipy is not available, we would need a custom implementation of the t-distribution CDF.
    try:
        from scipy.stats import t
        p_value = 2 * t.sf(np.abs(t_statistic), df)
    except ImportError:
        logger.warning("scipy not found. Using normal approximation for p-value (less accurate for small n).")
        # Normal approximation for large n
        from math import erf, sqrt
        # p = 2 * (1 - Phi(|t|))
        # Phi(x) = 0.5 * (1 + erf(x / sqrt(2)))
        z = abs(t_statistic)
        p_value = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))

    is_significant = p_value < alpha

    logger.info(
        f"Nadeau-Bengio t-test: t={t_statistic:.4f}, p={p_value:.4f}, "
        f"significant={is_significant} (alpha={alpha})"
    )

    return t_statistic, p_value, is_significant


def compare_models(
    scores_model_a: np.ndarray,
    scores_model_b: np.ndarray,
    n_folds: int,
    n_train: int,
    n_test: int,
    model_name_a: str = "Model A",
    model_name_b: str = "Model B",
    alpha: float = 0.05
) -> dict:
    """
    Compare two models using the Nadeau & Bengio corrected t-test.

    Args:
        scores_model_a: Performance scores for model A across folds.
        scores_model_b: Performance scores for model B across folds.
        n_folds: Number of cross-validation folds.
        n_train: Training set size per fold.
        n_test: Test set size per fold.
        model_name_a: Name of model A for reporting.
        model_name_b: Name of model B for reporting.
        alpha: Significance level.

    Returns:
        Dictionary containing test results:
            - t_statistic: Calculated t-value.
            - p_value: Calculated p-value.
            - is_significant: Whether the difference is statistically significant.
            - mean_diff: Mean difference in scores (Model A - Model B).
            - winner: Name of the better performing model (or "Tie" if not significant).
            - details: String summary of the test.
    """
    t_stat, p_val, sig = nadeau_bengio_ttest(
        scores_model_a, scores_model_b, n_folds, n_train, n_test, alpha
    )

    mean_diff = np.mean(scores_model_a) - np.mean(scores_model_b)

    if sig:
        winner = model_name_a if mean_diff > 0 else model_name_b
        direction = "better" if mean_diff > 0 else "worse"
        report = (
            f"{winner} is significantly {direction} than the other model "
            f"(p={p_val:.4f}, t={t_stat:.4f})."
        )
    else:
        winner = "No significant difference"
        report = (
            f"No significant difference between {model_name_a} and {model_name_b} "
            f"(p={p_val:.4f}, t={t_stat:.4f})."
        )

    return {
        "t_statistic": t_stat,
        "p_value": p_val,
        "is_significant": sig,
        "mean_diff": mean_diff,
        "mean_score_a": float(np.mean(scores_model_a)),
        "mean_score_b": float(np.mean(scores_model_b)),
        "winner": winner,
        "details": report,
        "method": "Nadeau & Bengio corrected resampled t-test"
    }