"""
Physics models for testing the inverse-square law at sub-millimeter scales.

This module implements:
1. Newtonian gravitational force (baseline).
2. Yukawa-modified gravitational force (test for new physics).

The Yukawa potential modifies the Newtonian potential as:
    V(r) = -G * M1 * M2 / r * (1 + alpha * exp(-r / lambda))

Consequently, the force is:
    F(r) = -dV/dr = -G * M1 * M2 / r^2 * (1 + alpha * (1 + r/lambda) * exp(-r / lambda))

We model the force magnitude F(r) (positive for attraction) as:
    F(r) = F_newton(r) * (1 + alpha * (1 + r/lambda) * exp(-r / lambda))
"""

import numpy as np
from typing import Union

# Physical constant (Standard Gravitational Constant)
# Value: 6.67430e-11 m^3 kg^-1 s^-2
G = 6.67430e-11

def newtonian_force(
    r: Union[np.ndarray, float],
    m1: float,
    m2: float
) -> Union[np.ndarray, float]:
    """
    Calculate the Newtonian gravitational force between two masses.

    F = G * m1 * m2 / r^2

    Args:
        r: Separation distance in meters (scalar or array).
        m1: Mass of object 1 in kg.
        m2: Mass of object 2 in kg.

    Returns:
        Force magnitude in Newtons.

    Raises:
        ValueError: If r contains non-positive values.
    """
    r_arr = np.asarray(r, dtype=float)
    if np.any(r_arr <= 0):
        raise ValueError("Separation distance r must be positive.")

    return (G * m1 * m2) / (r_arr ** 2)


def yukawa_force(
    r: Union[np.ndarray, float],
    m1: float,
    m2: float,
    alpha: float,
    lambda_param: float
) -> Union[np.ndarray, float]:
    """
    Calculate the Yukawa-modified gravitational force.

    The modification factor is: 1 + alpha * (1 + r/lambda) * exp(-r/lambda)

    Args:
        r: Separation distance in meters (scalar or array).
        m1: Mass of object 1 in kg.
        m2: Mass of object 2 in kg.
        alpha: Strength of the Yukawa interaction (dimensionless).
        lambda_param: Range of the Yukawa interaction in meters.

    Returns:
        Force magnitude in Newtons.

    Raises:
        ValueError: If r contains non-positive values or lambda_param <= 0.
    """
    r_arr = np.asarray(r, dtype=float)
    if np.any(r_arr <= 0):
        raise ValueError("Separation distance r must be positive.")
    if lambda_param <= 0:
        raise ValueError("Yukawa range lambda must be positive.")

    # Newtonian component
    f_newton = (G * m1 * m2) / (r_arr ** 2)

    # Yukawa correction factor
    # factor = 1 + alpha * (1 + r/lambda) * exp(-r/lambda)
    ratio = r_arr / lambda_param
    correction = 1.0 + alpha * (1.0 + ratio) * np.exp(-ratio)

    return f_newton * correction


def log_likelihood_yukawa(
    r: np.ndarray,
    forces_obs: np.ndarray,
    sigma: np.ndarray,
    m1: float,
    m2: float,
    alpha: float,
    lambda_param: float
) -> float:
    """
    Compute the log-likelihood for the Yukawa model assuming Gaussian errors.

    log L = -0.5 * sum( ((F_obs - F_model) / sigma)^2 + log(2 * pi * sigma^2) )

    Args:
        r: Separation distances (m).
        forces_obs: Observed force values (N).
        sigma: Uncertainties (N) for each observation.
        m1: Mass 1 (kg).
        m2: Mass 2 (kg).
        alpha: Yukawa strength parameter.
        lambda_param: Yukawa range parameter (m).

    Returns:
        Log-likelihood value.
    """
    forces_model = yukawa_force(r, m1, m2, alpha, lambda_param)
    residuals = forces_obs - forces_model
    chi_sq = np.sum((residuals / sigma) ** 2)
    log_det = np.sum(np.log(2 * np.pi * sigma ** 2))

    return -0.5 * (chi_sq + log_det)


def log_likelihood_newtonian(
    r: np.ndarray,
    forces_obs: np.ndarray,
    sigma: np.ndarray,
    m1: float,
    m2: float
) -> float:
    """
    Compute the log-likelihood for the standard Newtonian model.

    This is equivalent to the Yukawa model with alpha = 0.

    Args:
        r: Separation distances (m).
        forces_obs: Observed force values (N).
        sigma: Uncertainties (N) for each observation.
        m1: Mass 1 (kg).
        m2: Mass 2 (kg).

    Returns:
        Log-likelihood value.
    """
    # alpha=0 implies correction factor is 1.0
    forces_model = newtonian_force(r, m1, m2)
    residuals = forces_obs - forces_model
    chi_sq = np.sum((residuals / sigma) ** 2)
    log_det = np.sum(np.log(2 * np.pi * sigma ** 2))

    return -0.5 * (chi_sq + log_det)