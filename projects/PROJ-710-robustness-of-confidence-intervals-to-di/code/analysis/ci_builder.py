"""
Confidence Interval Builder for Bootstrap Resampling.

This module provides functionality for constructing 95% confidence intervals
using the percentile method with 1,000 bootstrap resamples.
"""

import numpy as np
from typing import Union, List, Tuple, Optional
from scipy import stats

# Constants
DEFAULT_BOOTSTRAP_RESAMPLES = 1000
DEFAULT_CONFIDENCE_LEVEL = 0.95
MIN_SAMPLE_SIZE = 30  # Minimum sample size for reliable bootstrap

def bootstrap_resample(data: np.ndarray, n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
                       random_state: Optional[int] = None) -> np.ndarray:
    """
    Generate bootstrap resamples of the data.

    Args:
        data: 1D array of observations
        n_resamples: Number of bootstrap resamples to generate
        random_state: Random seed for reproducibility

    Returns:
        Array of shape (n_resamples,) containing bootstrap statistics
    """
    if random_state is not None:
        np.random.seed(random_state)

    n = len(data)
    if n < MIN_SAMPLE_SIZE:
        raise ValueError(f"Sample size {n} is below minimum required {MIN_SAMPLE_SIZE} for bootstrap")

    # Generate bootstrap statistics (mean)
    bootstrap_means = np.empty(n_resamples)
    for i in range(n_resamples):
        resample_indices = np.random.choice(n, size=n, replace=True)
        resample = data[resample_indices]
        bootstrap_means[i] = np.mean(resample)

    return bootstrap_means


def compute_percentile_ci(bootstrap_distribution: np.ndarray,
                          confidence_level: float = DEFAULT_CONFIDENCE_LEVEL) -> Tuple[float, float]:
    """
    Compute percentile confidence interval from bootstrap distribution.

    Args:
        bootstrap_distribution: Array of bootstrap statistics
        confidence_level: Confidence level (e.g., 0.95 for 95% CI)

    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100

    lower_bound = np.percentile(bootstrap_distribution, lower_percentile)
    upper_bound = np.percentile(bootstrap_distribution, upper_percentile)

    return lower_bound, upper_bound


def build_ci_for_mean(data: np.ndarray, n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
                      confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
                      random_state: Optional[int] = None) -> Tuple[float, float, float]:
    """
    Build a confidence interval for the population mean using bootstrap percentile method.

    Args:
        data: 1D array of observations
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level for the CI
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (point_estimate, ci_lower, ci_upper)
    """
    if len(data) < MIN_SAMPLE_SIZE:
        raise ValueError(f"Sample size {len(data)} is below minimum required {MIN_SAMPLE_SIZE}")

    # Calculate point estimate
    point_estimate = np.mean(data)

    # Generate bootstrap distribution
    bootstrap_means = bootstrap_resample(data, n_resamples, random_state)

    # Compute percentile CI
    ci_lower, ci_upper = compute_percentile_ci(bootstrap_means, confidence_level)

    return point_estimate, ci_lower, ci_upper


def build_ci_for_regression_coefficient(X: np.ndarray, y: np.ndarray,
                                        n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
                                        confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
                                        random_state: Optional[int] = None) -> Tuple[float, float, float]:
    """
    Build a confidence interval for a regression coefficient using bootstrap.

    Args:
        X: 2D array of features (n_samples, n_features)
        y: 1D array of target values
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level for the CI
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (point_estimate, ci_lower, ci_upper) for the first coefficient
    """
    if len(y) < MIN_SAMPLE_SIZE:
        raise ValueError(f"Sample size {len(y)} is below minimum required {MIN_SAMPLE_SIZE}")

    n_samples, n_features = X.shape

    # Calculate point estimate using OLS
    # beta = (X^T X)^-1 X^T y
    try:
        beta_hat = np.linalg.lstsq(X, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        raise ValueError("Design matrix is singular; cannot compute OLS estimates")

    point_estimate = beta_hat[0]  # Focus on first coefficient

    # Generate bootstrap distribution of coefficients
    bootstrap_coeffs = np.empty(n_resamples)

    if random_state is not None:
        np.random.seed(random_state)

    for i in range(n_resamples):
        # Resample indices
        indices = np.random.choice(n_samples, size=n_samples, replace=True)
        X_resample = X[indices]
        y_resample = y[indices]

        # Compute coefficient for resample
        try:
            beta_resample = np.linalg.lstsq(X_resample, y_resample, rcond=None)[0]
            bootstrap_coeffs[i] = beta_resample[0]
        except np.linalg.LinAlgError:
            # Handle singular matrix in resample
            bootstrap_coeffs[i] = np.nan

    # Remove NaN values
    valid_coeffs = bootstrap_coeffs[~np.isnan(bootstrap_coeffs)]

    if len(valid_coeffs) < n_resamples * 0.9:
        raise ValueError("Too many singular matrices in bootstrap resamples; check for collinearity")

    # Compute percentile CI
    ci_lower, ci_upper = compute_percentile_ci(valid_coeffs, confidence_level)

    return point_estimate, ci_lower, ci_upper


def build_ci_for_variance(data: np.ndarray, n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
                          confidence_level: float = DEFAULT_CONFIDENCE_LEVEL,
                          random_state: Optional[int] = None) -> Tuple[float, float, float]:
    """
    Build a confidence interval for the population variance using bootstrap.

    Args:
        data: 1D array of observations
        n_resamples: Number of bootstrap resamples
        confidence_level: Confidence level for the CI
        random_state: Random seed for reproducibility

    Returns:
        Tuple of (point_estimate, ci_lower, ci_upper)
    """
    if len(data) < MIN_SAMPLE_SIZE:
        raise ValueError(f"Sample size {len(data)} is below minimum required {MIN_SAMPLE_SIZE}")

    # Calculate point estimate
    point_estimate = np.var(data, ddof=1)  # Sample variance

    # Generate bootstrap distribution
    bootstrap_vars = np.empty(n_resamples)

    if random_state is not None:
        np.random.seed(random_state)

    n = len(data)
    for i in range(n_resamples):
        indices = np.random.choice(n, size=n, replace=True)
        resample = data[indices]
        bootstrap_vars[i] = np.var(resample, ddof=1)

    # Compute percentile CI
    ci_lower, ci_upper = compute_percentile_ci(bootstrap_vars, confidence_level)

    return point_estimate, ci_lower, ci_upper


def validate_ci_coverage(ground_truth_value: float, ci_lower: float, ci_upper: float) -> bool:
    """
    Check if the confidence interval covers the ground truth value.

    Args:
        ground_truth_value: True parameter value
        ci_lower: Lower bound of CI
        ci_upper: Upper bound of CI

    Returns:
        True if the interval covers the ground truth, False otherwise
    """
    return ci_lower <= ground_truth_value <= ci_upper