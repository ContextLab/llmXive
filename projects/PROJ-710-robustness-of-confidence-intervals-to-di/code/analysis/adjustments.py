"""
Adjustment methods for DP-perturbed statistics to restore nominal coverage.

Implements bias-correction for means (Covington et al. 2021)
and variance-inflation for regression coefficients (Karwa & Vadhan 2017).
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from scipy import stats


def apply_bias_correction_mean(
    noisy_mean: float,
    epsilon: float,
    sensitivity: float,
    noise_type: str = "laplace"
) -> float:
    """
    Apply bias correction to a noisy mean estimate.

    Based on Covington et al. (2021), the expectation of the noisy mean
    under Laplace noise is the true mean (unbiased), but under Gaussian
    noise with variance sigma^2 = 2 * sensitivity^2 * log(1.25/delta) / epsilon^2,
    it is also unbiased. However, for small epsilon, the noise scale can
    introduce bias in finite samples or if the noise mechanism is not perfectly
    centered.

    For this implementation, we apply a correction that accounts for the
    expected absolute deviation when the noise distribution has non-zero
    mean (which shouldn't happen for centered Laplace/Gaussian, but we
    provide the framework).

    Parameters
    ----------
    noisy_mean : float
        The mean estimate computed from DP-noisy data.
    epsilon : float
        The privacy budget.
    sensitivity : float
        The L1 sensitivity of the mean statistic.
    noise_type : str
        Either "laplace" or "gaussian".

    Returns
    -------
    float
        Bias-corrected mean estimate.

    Notes
    -----
    For centered Laplace and Gaussian mechanisms, the expectation is
    unbiased. This function currently returns the noisy mean as-is,
    but provides the structure for future corrections if needed.
    """
    # For centered mechanisms, E[noise] = 0, so no bias correction needed
    # This is a placeholder for more sophisticated corrections if required
    return noisy_mean


def apply_variance_inflation_regression(
    point_estimate: np.ndarray,
    standard_error: float,
    epsilon: float,
    sensitivity: float,
    noise_type: str = "laplace",
    delta: float = 1e-5
) -> Tuple[np.ndarray, float]:
    """
    Apply variance inflation to regression coefficient estimates.

    Based on Karwa & Vadhan (2017), the variance of the noisy estimator
    is inflated by the variance of the added noise.

    For Laplace noise with scale b = sensitivity / epsilon:
        Var(noise) = 2 * b^2 = 2 * sensitivity^2 / epsilon^2

    For Gaussian noise with scale sigma = sensitivity * sqrt(2 * log(1.25/delta)) / epsilon:
        Var(noise) = sigma^2 = 2 * sensitivity^2 * log(1.25/delta) / epsilon^2

    The adjusted variance is:
        Var_adjusted = Var_original + Var_noise

    Parameters
    ----------
    point_estimate : np.ndarray
        Array of regression coefficient estimates.
    standard_error : float
        The standard error of the point estimate (from the original data).
    epsilon : float
        The privacy budget.
    sensitivity : float
        The L1 sensitivity of the regression coefficient.
    noise_type : str
        Either "laplace" or "gaussian".
    delta : float
        The failure probability for Gaussian mechanism (default 1e-5).

    Returns
    -------
    Tuple[np.ndarray, float]
        The point estimate (unchanged, as noise is centered) and the
        adjusted standard error.
    """
    epsilon = float(epsilon)
    sensitivity = float(sensitivity)

    if epsilon <= 0:
        raise ValueError("Epsilon must be positive")

    if noise_type == "laplace":
        # Laplace scale parameter
        scale = sensitivity / epsilon
        noise_variance = 2 * (scale ** 2)
    elif noise_type == "gaussian":
        # Gaussian scale parameter
        scale = sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon
        noise_variance = scale ** 2
    else:
        raise ValueError(f"Unknown noise type: {noise_type}")

    # Original variance
    original_variance = standard_error ** 2

    # Adjusted variance
    adjusted_variance = original_variance + noise_variance
    adjusted_se = np.sqrt(adjusted_variance)

    return point_estimate, adjusted_se


def apply_adjustments_to_summary(
    point_estimate: float,
    standard_error: float,
    epsilon: float,
    sensitivity: float,
    statistic_type: str,
    noise_type: str = "laplace",
    delta: float = 1e-5
) -> Tuple[float, float]:
    """
    Apply appropriate adjustments based on the statistic type.

    Parameters
    ----------
    point_estimate : float
        The point estimate (mean or regression coefficient).
    standard_error : float
        The standard error of the estimate.
    epsilon : float
        The privacy budget.
    sensitivity : float
        The L1 sensitivity of the statistic.
    statistic_type : str
        Either "mean" or "regression".
    noise_type : str
        Either "laplace" or "gaussian".
    delta : float
        The failure probability for Gaussian mechanism.

    Returns
    -------
    Tuple[float, float]
        The adjusted point estimate and adjusted standard error.
    """
    if statistic_type == "mean":
        corrected_mean = apply_bias_correction_mean(
            point_estimate, epsilon, sensitivity, noise_type
        )
        return corrected_mean, standard_se
    elif statistic_type == "regression":
        corrected_coef, adjusted_se = apply_variance_inflation_regression(
            np.array([point_estimate]),
            standard_error,
            epsilon,
            sensitivity,
            noise_type,
            delta
        )
        return float(corrected_coef[0]), adjusted_se
    else:
        raise ValueError(f"Unknown statistic type: {statistic_type}")


def compute_adjusted_ci(
    point_estimate: float,
    adjusted_se: float,
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Compute a confidence interval using the adjusted standard error.

    Parameters
    ----------
    point_estimate : float
        The (possibly bias-corrected) point estimate.
    adjusted_se : float
        The variance-inflated standard error.
    confidence_level : float
        The desired confidence level (default 0.95).

    Returns
    -------
    Tuple[float, float]
        The lower and upper bounds of the confidence interval.
    """
    alpha = 1 - confidence_level
    z_score = stats.norm.ppf(1 - alpha / 2)
    margin = z_score * adjusted_se
    return point_estimate - margin, point_estimate + margin
