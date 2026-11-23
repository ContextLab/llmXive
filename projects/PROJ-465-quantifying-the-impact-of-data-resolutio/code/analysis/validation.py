"""
Validation utilities for the gravitational wave resolution impact study.

This module implements validation logic for injected data scenarios,
uncertainty scaling, and bias threshold checking as per US-2 requirements.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np

from code.config import DATA_DIR, RESULTS_DIR

logger = logging.getLogger(__name__)


def scale_uncertainty_to_90_ci(uncertainty_1sigma: float) -> float:
    """
    Scale a 1-sigma statistical uncertainty to a 90% confidence interval width.

    Uses the standard normality assumption: 90% CI ≈ 1.645 * σ.

    Args:
        uncertainty_1sigma: The 1-sigma uncertainty value.

    Returns:
        The scaled 90% confidence interval width.
    """
    if uncertainty_1sigma is None or np.isnan(uncertainty_1sigma) or uncertainty_1sigma <= 0:
        raise ValueError(f"Invalid 1-sigma uncertainty: {uncertainty_1sigma}. Must be positive and finite.")

    # Standard normal 90% CI factor
    factor = 1.645
    return uncertainty_1sigma * factor


def scale_catalog_uncertainties(catalog_params: Dict[str, Any]) -> Dict[str, float]:
    """
    Scale catalog-reported uncertainties to 90% confidence intervals.

    Args:
        catalog_params: Dictionary containing catalog parameters with uncertainty keys
                        (e.g., 'mass_1_err', 'chi_eff_err').

    Returns:
        Dictionary with scaled 90% CI uncertainties.
    """
    scaled = {}
    for key, value in catalog_params.items():
        if key.endswith('_err') and isinstance(value, (int, float)):
            scaled[key] = scale_uncertainty_to_90_ci(float(value))
        else:
            scaled[key] = value
    return scaled


def check_bias_against_catalog_ci(
    bias_values: Dict[str, float],
    catalog_uncertainties_90ci: Dict[str, float],
    threshold_factor: float = 1.0
) -> Dict[str, bool]:
    """
    Check if bias values exceed the catalog-reported 90% confidence interval.

    Args:
        bias_values: Dictionary of parameter biases (e.g., {'mass_1': 0.05, 'chi_eff': 0.01}).
        catalog_uncertainties_90ci: Dictionary of 90% CI uncertainties for comparison.
        threshold_factor: Multiplier for the uncertainty threshold (default 1.0).

    Returns:
        Dictionary indicating whether each bias exceeds the threshold.
    """
    exceeded = {}
    for param, bias in bias_values.items():
        # Map bias key to uncertainty key (e.g., 'mass_1' -> 'mass_1_err')
        err_key = f"{param}_err"
        if err_key in catalog_uncertainties_90ci:
            threshold = abs(catalog_uncertainties_90ci[err_key]) * threshold_factor
            exceeded[param] = abs(bias) > threshold
        else:
            logger.warning(f"No catalog uncertainty found for parameter '{param}'. Skipping check.")
            exceeded[param] = False
    return exceeded


def validate_injected_data_scenario(
    posterior_samples: Dict[str, np.ndarray],
    injected_parameters: Dict[str, float],
    tolerance: float = 1e-6
) -> Tuple[bool, Dict[str, float]]:
    """
    Validate that bias in injected data scenarios is effectively zero.

    For simulated injection scenarios, the posterior should recover the injected
    parameters with bias < tolerance (default 1e-6).

    Args:
        posterior_samples: Dictionary of parameter names to posterior sample arrays.
        injected_parameters: Dictionary of true injected parameter values.
        tolerance: Maximum acceptable absolute bias (default 1e-6).

    Returns:
        Tuple of (is_valid, bias_dict):
            - is_valid: True if all biases are below tolerance.
            - bias_dict: Dictionary of absolute biases for each parameter.

    Raises:
        ValueError: If posterior_samples or injected_parameters are empty or mismatched.
    """
    if not posterior_samples or not injected_parameters:
        raise ValueError("posterior_samples and injected_parameters must not be empty.")

    common_params = set(posterior_samples.keys()) & set(injected_parameters.keys())
    if not common_params:
        raise ValueError("No common parameters between posterior and injection.")

    bias_dict = {}
    all_valid = True

    for param in common_params:
        samples = posterior_samples[param]
        true_value = injected_parameters[param]

        # Calculate mean of posterior samples
        posterior_mean = np.mean(samples)
        bias = abs(posterior_mean - true_value)
        bias_dict[param] = bias

        if bias >= tolerance:
            all_valid = False
            logger.warning(
                f"Bias for '{param}' ({bias:.2e}) exceeds tolerance ({tolerance:.2e}). "
                f"Posterior mean: {posterior_mean:.6e}, Injected: {true_value:.6e}"
            )
        else:
            logger.info(f"Bias for '{param}' ({bias:.2e}) within tolerance.")

    return all_valid, bias_dict


def main():
    """
    Main entry point for validation testing.

    This function demonstrates the validation logic for injected data scenarios.
    In a real execution, it would load actual posterior files and injection metadata.
    """
    logging.basicConfig(level=logging.INFO)

    # Example demonstration with synthetic data (for testing purposes only)
    # In production, this would load real data from disk
    injected = {
        'mass_1': 30.0,
        'mass_2': 25.0,
        'chi_eff': 0.0
    }

    # Simulate a posterior that perfectly recovers injection (ideal case)
    posterior = {
        'mass_1': np.random.normal(30.0, 0.0001, 1000),
        'mass_2': np.random.normal(25.0, 0.0001, 1000),
        'chi_eff': np.random.normal(0.0, 0.0001, 1000)
    }

    is_valid, biases = validate_injected_data_scenario(posterior, injected, tolerance=1e-6)

    print(f"Validation Result: {'PASS' if is_valid else 'FAIL'}")
    print("Biases:")
    for param, bias in biases.items():
        print(f"  {param}: {bias:.2e}")

    return is_valid


if __name__ == "__main__":
    main()
