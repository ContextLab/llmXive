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


def calculate_coverage_batch(
    intervals_df: pd.DataFrame,
    actuals_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Calculate empirical coverage for a batch of series, models, and horizons.

    This function processes the intermediate interval outputs from T015 and
    computes the empirical coverage rate for each (series_id, model, horizon) combination.

    Args:
        intervals_df: DataFrame with columns: series_id, model, horizon, lower, upper
                      (where lower/upper can be lists/arrays or the df is exploded)
        actuals_df: DataFrame with columns: series_id, horizon, actual_value

    Returns:
        pd.DataFrame: DataFrame with columns: series_id, model, horizon, empirical_coverage

    Raises:
        ValueError: If required columns are missing or data alignment fails.
    """
    required_interval_cols = {'series_id', 'model', 'horizon', 'lower', 'upper'}
    required_actual_cols = {'series_id', 'horizon', 'actual_value'}

    if not required_interval_cols.issubset(intervals_df.columns):
        missing = required_interval_cols - set(intervals_df.columns)
        raise ValueError(f"Missing columns in intervals_df: {missing}")

    if not required_actual_cols.issubset(actuals_df.columns):
        missing = required_actual_cols - set(actuals_df.columns)
        raise ValueError(f"Missing columns in actuals_df: {missing}")

    results = []

    # Group by series_id, model, horizon to calculate coverage
    # Assuming lower/upper are array-like in the cells, or the data is already exploded
    # We handle the case where lower/upper are lists/arrays in a single cell per group
    for (series_id, model, horizon), group in intervals_df.groupby(['series_id', 'model', 'horizon']):
        # Get the interval bounds (assuming they are identical for the group or aggregated)
        # If the input is already a single row per (series, model, horizon) with lists:
        lower_vals = group['lower'].iloc[0] if hasattr(group['lower'].iloc[0], '__len__') else group['lower'].values
        upper_vals = group['upper'].iloc[0] if hasattr(group['upper'].iloc[0], '__len__') else group['upper'].values

        # Get actuals for this series and horizon
        actuals = actuals_df[
            (actuals_df['series_id'] == series_id) &
            (actuals_df['horizon'] == horizon)
        ]['actual_value'].values

        if len(actuals) == 0:
            logger.warning(f"No actuals found for series {series_id}, horizon {horizon}")
            continue

        # Ensure lengths match
        if isinstance(lower_vals, list):
            lower_vals = np.array(lower_vals)
        if isinstance(upper_vals, list):
            upper_vals = np.array(upper_vals)

        if len(lower_vals) != len(actuals):
            # If lengths don't match, try to align or skip
            # For robustness, we assume the first N or last N match, but here we strict fail or warn
            logger.warning(
                f"Length mismatch for series {series_id}, model {model}, horizon {horizon}. "
                f"Lower/Upper len: {len(lower_vals)}, Actuals len: {len(actuals)}. Skipping."
            )
            continue

        cov = empirical_coverage(lower_vals, upper_vals, actuals)
        results.append({
            'series_id': series_id,
            'model': model,
            'horizon': horizon,
            'empirical_coverage': cov
        })

    return pd.DataFrame(results)


def save_coverage_results(
    coverage_df: pd.DataFrame,
    output_path: str
) -> None:
    """
    Save the calculated coverage results to a CSV file.

    Args:
        coverage_df: DataFrame containing coverage results.
        output_path: Path to the output CSV file.
    """
    coverage_df.to_csv(output_path, index=False)
    logger.info(f"Saved coverage results to {output_path}")
