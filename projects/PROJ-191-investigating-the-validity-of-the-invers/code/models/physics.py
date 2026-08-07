"""
Physics models for gravitational force calculations.

Implements Newtonian and Yukawa-modified gravity force models.
"""
import numpy as np
from typing import Union

# Gravitational constant (m^3 kg^-1 s^-2)
G = 6.67430e-11
# Mass of source and test masses (kg) - these would be read from data/config
# For now, we use placeholder values that would be calibrated
M_SOURCE = 1.0  # kg
M_TEST = 1.0e-3  # kg (1 gram)


def newtonian_force(separation: Union[np.ndarray, float]) -> Union[np.ndarray, float]:
    """
    Calculate Newtonian gravitational force.
    
    F = G * M1 * M2 / r^2
    
    Args:
        separation: Separation distance(s) in meters.
    
    Returns:
        Force(s) in Newtons.
    """
    separation = np.asarray(separation)
    # Avoid division by zero
    separation = np.maximum(separation, 1e-12)
    return G * M_SOURCE * M_TEST / (separation ** 2)


def yukawa_force(
    separation: Union[np.ndarray, float], 
    alpha: float, 
    lambda_val: float
) -> Union[np.ndarray, float]:
    """
    Calculate Yukawa-modified gravitational force.
    
    F = F_newton * (1 + alpha * exp(-r/lambda))
    
    Args:
        separation: Separation distance(s) in meters.
        alpha: Strength parameter (dimensionless, relative to gravity).
        lambda_val: Range parameter in meters.
    
    Returns:
        Force(s) in Newtons.
    """
    separation = np.asarray(separation)
    # Avoid division by zero
    separation = np.maximum(separation, 1e-12)
    
    f_newton = newtonian_force(separation)
    correction = 1 + alpha * np.exp(-separation / lambda_val)
    
    return f_newton * correction


def log_likelihood_yukawa(
    params: np.ndarray,
    separation: np.ndarray,
    force: np.ndarray,
    sigma: Union[np.ndarray, float] = 1e-15
) -> float:
    """
    Compute log-likelihood for Yukawa model with Gaussian errors.
    
    Args:
        params: [alpha, lambda]
        separation: Separation distances
        force: Measured forces
        sigma: Uncertainty (scalar or array)
    
    Returns:
        Log-likelihood value.
    """
    alpha, lambda_val = params
    
    model = yukawa_force(separation, alpha, lambda_val)
    residuals = force - model
    
    # Simple Gaussian log-likelihood
    # log L = -0.5 * sum((r/sigma)^2 + log(2*pi*sigma^2))
    if np.isscalar(sigma):
        log_likelihood = -0.5 * np.sum(
            (residuals / sigma) ** 2 + 
            np.log(2 * np.pi * sigma ** 2)
        )
    else:
        log_likelihood = -0.5 * np.sum(
            (residuals / sigma) ** 2 + 
            np.log(2 * np.pi * sigma ** 2)
        )
    
    return log_likelihood


def log_likelihood_newtonian(
    separation: np.ndarray,
    force: np.ndarray,
    sigma: Union[np.ndarray, float] = 1e-15
) -> float:
    """
    Compute log-likelihood for Newtonian model with Gaussian errors.
    
    Args:
        separation: Separation distances
        force: Measured forces
        sigma: Uncertainty (scalar or array)
    
    Returns:
        Log-likelihood value.
    """
    model = newtonian_force(separation)
    residuals = force - model
    
    if np.isscalar(sigma):
        log_likelihood = -0.5 * np.sum(
            (residuals / sigma) ** 2 + 
            np.log(2 * np.pi * sigma ** 2)
        )
    else:
        log_likelihood = -0.5 * np.sum(
            (residuals / sigma) ** 2 + 
            np.log(2 * np.pi * sigma ** 2)
        )
    
    return log_likelihood


def main():
    """Test physics functions."""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Test data
    r = np.array([1e-4, 2e-4, 5e-4])  # 100um, 200um, 500um
    
    f_newton = newtonian_force(r)
    print(f"Newtonian forces: {f_newton}")
    
    f_yukawa = yukawa_force(r, alpha=1.0, lambda_val=1e-4)
    print(f"Yukawa forces (alpha=1, lambda=100um): {f_yukawa}")
    
    # Test likelihood
    ll_newt = log_likelihood_newtonian(r, f_newton, sigma=1e-20)
    print(f"Newtonian log-likelihood: {ll_newt}")
    
    ll_yuk = log_likelihood_yukawa(np.array([1.0, 1e-4]), r, f_yukawa, sigma=1e-20)
    print(f"Yukawa log-likelihood: {ll_yuk}")


if __name__ == "__main__":
    main()