"""
Statistical tests for comparing model performance.

Implements the Nadeau & Bengio corrected resampled t-test to account for
the overlap between training and test sets in cross-validation.

This implementation manually calculates the variance correction term rather
than using scipy.stats.ttest_rel directly, as required by the specification.
"""

import numpy as np
import logging
from typing import List, Tuple, Optional

from src.utils.logger import get_module_logger

logger = get_module_logger(__name__)


def nadeau_bengio_ttest(
    scores_model_a: List[float],
    scores_model_b: List[float],
    n_train: int,
    n_test: int,
    alpha: float = 0.05
) -> Tuple[float, float, bool]:
    """
    Perform the Nadeau & Bengio corrected resampled t-test.

    This test compares two models evaluated on the same cross-validation folds.
    It corrects for the dependence between folds by adjusting the variance
    estimate based on the ratio of training and test set sizes.

    Parameters
    ----------
    scores_model_a : List[float]
        Performance scores (e.g., R²) for model A on each outer fold.
    scores_model_b : List[float]
        Performance scores (e.g., R²) for model B on each outer fold.
    n_train : int
        Number of samples in the training set (used for variance correction).
    n_test : int
        Number of samples in the test set (used for variance correction).
    alpha : float
        Significance level (default 0.05).

    Returns
    -------
    t_statistic : float
        The calculated t-statistic.
    p_value : float
        The two-tailed p-value.
    is_significant : bool
        True if the difference is statistically significant at the given alpha.

    Raises
    ------
    ValueError
        If the input lists have different lengths or are empty.
    """
    if len(scores_model_a) != len(scores_model_b):
        raise ValueError("Score lists must have the same length.")
    if len(scores_model_a) == 0:
        raise ValueError("Score lists cannot be empty.")

    n_folds = len(scores_model_a)

    # Convert to numpy arrays
    a = np.array(scores_model_a)
    b = np.array(scores_model_b)

    # Calculate differences
    diff = a - b

    # Mean difference
    mean_diff = np.mean(diff)

    # Sample variance of the differences
    # Using ddof=1 for unbiased estimator
    var_diff = np.var(diff, ddof=1)

    # Nadeau & Bengio correction factor
    # The correction accounts for the fact that training sets overlap across folds.
    # Corrected variance = var_diff * (1/n_folds + n_test / (n_folds * n_train))
    # This is derived from: var(mean_diff) ≈ (σ²/n) * (1 + n_test/n_train)
    # where n is the number of folds.

    if n_train <= 0 or n_test <= 0:
        raise ValueError("n_train and n_test must be positive integers.")

    # Correction factor: (1/n_folds) + (n_test / (n_folds * n_train))
    # This represents the effective variance of the mean difference
    correction_factor = (1.0 / n_folds) + (n_test / (n_folds * n_train))

    # Corrected variance of the mean difference
    corrected_var_mean_diff = var_diff * correction_factor

    # Standard error of the mean difference
    se_mean_diff = np.sqrt(corrected_var_mean_diff)

    # Avoid division by zero
    if se_mean_diff < 1e-10:
        logger.warning("Standard error is near zero. Setting t-statistic to 0.")
        t_statistic = 0.0
        p_value = 1.0
        is_significant = False
        return t_statistic, p_value, is_significant

    # t-statistic
    t_statistic = mean_diff / se_mean_diff

    # Degrees of freedom: n_folds - 1
    df = n_folds - 1

    # Calculate p-value manually using the t-distribution
    # We use the survival function (sf) and multiply by 2 for two-tailed test
    # Approximation using scipy if available, otherwise manual calculation
    try:
        from scipy import stats
        p_value = 2 * stats.t.sf(np.abs(t_statistic), df)
    except ImportError:
        # Fallback: use a simple approximation if scipy is not available
        # This is less accurate but provides a reasonable estimate
        # For large df, t-distribution approaches normal distribution
        if df > 30:
            from math import erf, sqrt
            # Standard normal approximation
            z = abs(t_statistic)
            p_value = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
        else:
            # For small df, we cannot accurately calculate without scipy
            # Log a warning and return a conservative estimate
            logger.warning("Scipy not available and df <= 30. Returning conservative p-value estimate.")
            # Conservative estimate: if t > 2, p < 0.05 roughly
            if abs(t_statistic) > 2.0:
                p_value = 0.05
            else:
                p_value = 1.0

    is_significant = p_value < alpha

    logger.info(
        f"Nadeau-Bengio t-test: t={t_statistic:.4f}, p={p_value:.4f}, "
        f"significant={is_significant} (alpha={alpha})"
    )

    return t_statistic, p_value, is_significant


def run_model_comparison_test(
    model_a_scores: List[float],
    model_b_scores: List[float],
    n_train: int,
    n_test: int,
    model_a_name: str = "Model A",
    model_b_name: str = "Model B",
    alpha: float = 0.05
) -> dict:
    """
    Run a complete model comparison test and return a summary dictionary.

    Parameters
    ----------
    model_a_scores : List[float]
        Performance scores for model A.
    model_b_scores : List[float]
        Performance scores for model B.
    n_train : int
        Number of training samples.
    n_test : int
        Number of test samples.
    model_a_name : str
        Name of model A for reporting.
    model_b_name : str
        Name of model B for reporting.
    alpha : float
        Significance level.

    Returns
    -------
    dict
        A dictionary containing the test results, including:
        - mean_score_a, mean_score_b
        - t_statistic, p_value
        - is_significant
        - winner (name of the better model or 'No significant difference')
    """
    logger.info(f"Running comparison: {model_a_name} vs {model_b_name}")

    mean_a = np.mean(model_a_scores)
    mean_b = np.mean(model_b_scores)

    t_stat, p_val, is_sig = nadeau_bengio_ttest(
        model_a_scores, model_b_scores, n_train, n_test, alpha
    )

    if is_sig:
        if mean_a > mean_b:
            winner = model_a_name
        else:
            winner = model_b_name
    else:
        winner = "No significant difference"

    result = {
        "model_a": model_a_name,
        "model_b": model_b_name,
        "mean_score_a": float(mean_a),
        "mean_score_b": float(mean_b),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "is_significant": bool(is_sig),
        "alpha": alpha,
        "winner": winner,
        "n_folds": len(model_a_scores),
        "n_train": n_train,
        "n_test": n_test
    }

    logger.info(f"Comparison result: {winner} (p={p_val:.4f})")

    return result
