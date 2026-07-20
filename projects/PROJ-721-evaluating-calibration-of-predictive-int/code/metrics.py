"""
Metrics module for evaluating predictive interval calibration.

This module provides functions to compute:
1. Empirical Coverage: The proportion of actual test values falling within the predicted interval.
2. Interval Score: A proper scoring rule that penalizes both under-coverage and interval width.
"""

from __future__ import annotations

import logging
from typing import Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


def empirical_coverage(
    lower: Union[np.ndarray, pd.Series],
    upper: Union[np.ndarray, pd.Series],
    actual: Union[np.ndarray, pd.Series]
) -> float:
    """
    Calculate the empirical coverage rate of a prediction interval.

    The empirical coverage is the fraction of actual values that fall within
    the predicted lower and upper bounds.

    Args:
        lower: Array-like of lower bounds of the prediction intervals.
        upper: Array-like of upper bounds of the prediction intervals.
        actual: Array-like of actual observed values.

    Returns:
        float: The empirical coverage rate (between 0.0 and 1.0).

    Raises:
        ValueError: If input arrays have different lengths or contain NaN values.
    """
    # Convert to numpy arrays for consistent handling
    lower_arr = np.asarray(lower)
    upper_arr = np.asarray(upper)
    actual_arr = np.asarray(actual)

    # Validate inputs
    if not (len(lower_arr) == len(upper_arr) == len(actual_arr)):
        raise ValueError(
            f"Input arrays must have the same length. "
            f"Got: lower={len(lower_arr)}, upper={len(upper_arr)}, actual={len(actual_arr)}"
        )

    if np.any(np.isnan(lower_arr)) or np.any(np.isnan(upper_arr)) or np.any(np.isnan(actual_arr)):
        raise ValueError("Input arrays contain NaN values.")

    if len(actual_arr) == 0:
        logger.warning("Empty input arrays provided. Returning 0.0 coverage.")
        return 0.0

    # Calculate coverage: 1 if actual is within [lower, upper], else 0
    within_interval = (actual_arr >= lower_arr) & (actual_arr <= upper_arr)
    coverage = np.mean(within_interval)

    return float(coverage)


def interval_score(
    lower: Union[np.ndarray, pd.Series],
    upper: Union[np.ndarray, pd.Series],
    actual: Union[np.ndarray, pd.Series],
    alpha: float
) -> float:
    """
    Calculate the Winkler Interval Score (also known as Interval Score).

    The interval score is a proper scoring rule for prediction intervals.
    It penalizes intervals that are too wide and intervals that do not cover the actual value.
    Score = (Upper - Lower) + (2/alpha) * (Lower - Actual) * I(Actual < Lower) + (2/alpha) * (Actual - Upper) * I(Actual > Upper)

    Args:
        lower: Array-like of lower bounds of the prediction intervals.
        upper: Array-like of upper bounds of the prediction intervals.
        actual: Array-like of actual observed values.
        alpha: Significance level (e.g., 0.1 for 90% interval, 0.2 for 80% interval).
               Must be strictly between 0 and 1.

    Returns:
        float: The mean interval score. Lower is better.

    Raises:
        ValueError: If inputs are invalid or alpha is out of range.
    """
    # Convert to numpy arrays
    lower_arr = np.asarray(lower, dtype=float)
    upper_arr = np.asarray(upper, dtype=float)
    actual_arr = np.asarray(actual, dtype=float)

    # Validate alpha
    if not (0 < alpha < 1):
        raise ValueError(f"Alpha must be strictly between 0 and 1. Got: {alpha}")

    # Validate lengths
    n = len(lower_arr)
    if not (n == len(upper_arr) == len(actual_arr)):
        raise ValueError(
            f"Input arrays must have the same length. "
            f"Got: lower={len(lower_arr)}, upper={len(upper_arr)}, actual={len(actual_arr)}"
        )

    if n == 0:
        logger.warning("Empty input arrays provided. Returning 0.0 interval score.")
        return 0.0

    # Calculate width penalty
    width = upper_arr - lower_arr

    # Calculate coverage penalty
    # Penalty = (2/alpha) * distance from interval if outside
    penalty_lower = (2.0 / alpha) * np.maximum(0, lower_arr - actual_arr)
    penalty_upper = (2.0 / alpha) * np.maximum(0, actual_arr - upper_arr)

    # Total score per observation
    scores = width + penalty_lower + penalty_upper

    return float(np.mean(scores))


def coverage_deviation(
    empirical: float,
    nominal: float
) -> float:
    """
    Calculate the absolute deviation between empirical and nominal coverage.

    Args:
        empirical: The observed empirical coverage rate.
        nominal: The target nominal coverage rate (e.g., 0.80, 0.90).

    Returns:
        float: The absolute deviation |empirical - nominal|.
    """
    return float(abs(empirical - nominal))


def hypothesis_test_coverage(
    empirical: float,
    nominal: float,
    n_samples: int
) -> float:
    """
    Perform a hypothesis test to determine if the empirical coverage
    significantly deviates from the nominal coverage.

    Uses a binomial test (exact) or normal approximation for large N.
    H0: The true coverage probability is equal to the nominal level.

    Args:
        empirical: The observed empirical coverage rate.
        nominal: The target nominal coverage rate.
        n_samples: The number of samples (test points) used to calculate empirical.

    Returns:
        float: The two-sided p-value.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be positive.")

    # Calculate number of successes (points inside interval)
    successes = int(round(empirical * n_samples))

    # Use binomial test for exact p-value
    # We use a two-sided test
    p_value = stats.binom_test(successes, n=n_samples, p=nominal, alternative='two-sided')

    return float(p_value)