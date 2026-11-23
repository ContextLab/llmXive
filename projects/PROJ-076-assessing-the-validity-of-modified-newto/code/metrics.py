"""
Metric Calculator for Galaxy Rotation Curve Fits.

Implements reduced chi-squared (χ²), Akaike Information Criterion (AIC),
and Bayesian Information Criterion (BIC) calculations for MOND and NFW models.

Dependencies:
- numpy: Numerical operations
- scipy.stats: Chi-squared distribution (optional, for p-values if needed later)
- pandas: Dataframe handling (if needed for aggregation)
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any

from utils import get_logger, safe_divide

logger = get_logger(__name__)


def calculate_reduced_chi2(
    residuals: np.ndarray,
    uncertainties: np.ndarray,
    degrees_of_freedom: int
) -> float:
    """
    Calculate the reduced chi-squared statistic.

    χ²_reduced = (1/ν) * Σ((obs - pred)² / σ²)

    Args:
        residuals: Array of (observed - predicted) values.
        uncertainties: Array of measurement uncertainties (σ).
        degrees_of_freedom: Number of data points minus number of fitted parameters (ν).

    Returns:
        Reduced chi-squared value.
    """
    if degrees_of_freedom <= 0:
        logger.warning("Degrees of freedom <= 0. Returning infinity for reduced chi2.")
        return float('inf')

    if len(residuals) != len(uncertainties):
        raise ValueError(
            f"Residuals length ({len(residuals)}) must match uncertainties length ({len(uncertainties)})"
        )

    # Avoid division by zero in uncertainties
    if np.any(uncertainties == 0):
        logger.warning("Zero uncertainty detected. Setting to small epsilon to avoid division by zero.")
        uncertainties = np.where(uncertainties == 0, 1e-10, uncertainties)

    chi2 = np.sum((residuals / uncertainties) ** 2)
    reduced_chi2 = safe_divide(chi2, degrees_of_freedom)

    return float(reduced_chi2)


def calculate_aic(
    chi2: float,
    k: int
) -> float:
    """
    Calculate the Akaike Information Criterion (AIC).

    AIC = 2k + χ² (assuming Gaussian likelihood with fixed variance)
    Note: For least squares, the constant terms often cancel in comparison,
    so we use the simplified form AIC = 2k + χ².

    Args:
        chi2: The chi-squared statistic (not reduced).
        k: Number of fitted parameters.

    Returns:
        AIC value.
    """
    if k <= 0:
        logger.warning("Number of parameters (k) must be > 0.")
        k = 1

    aic = 2 * k + chi2
    return float(aic)


def calculate_bic(
    chi2: float,
    k: int,
    n: int
) -> float:
    """
    Calculate the Bayesian Information Criterion (BIC).

    BIC = k * ln(n) + χ²

    Args:
        chi2: The chi-squared statistic (not reduced).
        k: Number of fitted parameters.
        n: Number of data points.

    Returns:
        BIC value.
    """
    if n <= 0:
        raise ValueError("Number of data points (n) must be > 0.")
    if k <= 0:
        logger.warning("Number of parameters (k) must be > 0.")
        k = 1

    bic = k * np.log(n) + chi2
    return float(bic)


def compute_fit_metrics(
    residuals: np.ndarray,
    uncertainties: np.ndarray,
    n_params: int
) -> Dict[str, float]:
    """
    Compute all goodness-of-fit metrics for a single galaxy fit.

    Args:
        residuals: Array of (observed - predicted) values.
        uncertainties: Array of measurement uncertainties.
        n_params: Number of free parameters in the model.

    Returns:
        Dictionary containing:
            - 'reduced_chi2': Reduced chi-squared statistic
            - 'chi2': Raw chi-squared statistic
            - 'aic': Akaike Information Criterion
            - 'bic': Bayesian Information Criterion
            - 'n_dof': Degrees of freedom
            - 'n_points': Number of data points
    """
    n_points = len(residuals)
    n_dof = n_points - n_params

    if n_dof <= 0:
        logger.error(f"Invalid degrees of freedom: n_points={n_points}, n_params={n_params}")
        # Return NaNs to indicate failure
        return {
            'reduced_chi2': float('nan'),
            'chi2': float('nan'),
            'aic': float('nan'),
            'bic': float('nan'),
            'n_dof': n_dof,
            'n_points': n_points
        }

    # Avoid division by zero in uncertainties
    valid_unc = np.where(uncertainties == 0, 1e-10, uncertainties)
    chi2 = float(np.sum((residuals / valid_unc) ** 2))

    reduced_chi2 = safe_divide(chi2, n_dof)
    aic = calculate_aic(chi2, n_params)
    bic = calculate_bic(chi2, n_params, n_points)

    return {
        'reduced_chi2': reduced_chi2,
        'chi2': chi2,
        'aic': aic,
        'bic': bic,
        'n_dof': n_dof,
        'n_points': n_points
    }


def main():
    """
    Main entry point for metrics calculation.

    This script is designed to be called by the fitting pipeline (fit.py)
    or a batch processing script to generate results.
    It does not run standalone as a data generator but provides the functions
    required by T024.
    """
    logger.info("Metrics module loaded. Use compute_fit_metrics() for calculations.")
    # Example usage (commented out as this is a library module):
    # res = np.array([1.0, 2.0, 3.0])
    # unc = np.array([0.5, 0.5, 0.5])
    # metrics = compute_fit_metrics(res, unc, n_params=2)
    # print(metrics)


if __name__ == "__main__":
    main()
