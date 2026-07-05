"""
Diffusion rate calculator for spin system simulations.

This module implements the calculation of the diffusion rate, defined as the
rate of change of spatial variance over time (finite difference).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple

import numpy as np

from code.src.simulation.metrics import compute_spatial_variance
from code.src.simulation.stability import check_for_nan_inf, StabilityError

logger = logging.getLogger(__name__)


def calculate_diffusion_rate(
    variance_history: List[float],
    time_steps: List[float],
    method: str = "forward",
    min_variance_increase: float = 0.0,
    enforce_monotonicity: bool = True
) -> Dict[str, Any]:
    """
    Calculate the rate of change of spatial variance (diffusion rate) using finite differences.

    The diffusion rate is defined as:
        D = d(variance) / dt

    Args:
        variance_history: List of spatial variance values at each time step.
        time_steps: List of time values corresponding to each variance measurement.
        method: Finite difference method ('forward', 'backward', 'central').
        min_variance_increase: Minimum required increase in variance to consider diffusion valid.
        enforce_monotonicity: If True, assert that variance is non-decreasing (monotonic).

    Returns:
        Dictionary containing:
            - 'diffusion_rates': List of calculated diffusion rates.
            - 'mean_diffusion_rate': Average diffusion rate over the simulation.
            - 'max_diffusion_rate': Maximum instantaneous diffusion rate.
            - 'min_diffusion_rate': Minimum instantaneous diffusion rate.
            - 'is_monotonic': Boolean indicating if variance is monotonically increasing.
            - 'monotonicity_violations': Number of times variance decreased.
            - 'valid': Boolean indicating if the diffusion rate calculation is valid.
            - 'error_message': Optional error message if calculation failed.

    Raises:
        StabilityError: If variance history contains NaN or Inf values.
        ValueError: If input lists have mismatched lengths or are empty.
    """
    if len(variance_history) != len(time_steps):
        raise ValueError(
            f"variance_history and time_steps must have the same length. "
            f"Got {len(variance_history)} and {len(time_steps)}."
        )

    if len(variance_history) < 2:
        raise ValueError(
            "At least 2 time steps are required to calculate diffusion rate."
        )

    variance_array = np.array(variance_history, dtype=np.float64)
    time_array = np.array(time_steps, dtype=np.float64)

    # Check for numerical stability
    nan_inf_check = check_for_nan_inf(variance_array, "variance_history")
    if not nan_inf_check["valid"]:
        raise StabilityError(
            f"Invalid variance history detected: {nan_inf_check['error_message']}"
        )

    # Assert monotonicity if required
    is_monotonic = True
    monotonicity_violations = 0
    if enforce_monotonicity:
        differences = np.diff(variance_array)
        violations_mask = differences < 0
        monotonicity_violations = int(np.sum(violations_mask))
        if monotonicity_violations > 0:
            logger.warning(
                f"Variance history is not monotonically increasing. "
                f"Found {monotonicity_violations} violations. "
                f"Variance values: {variance_array}"
            )
            is_monotonic = False

    # Calculate finite differences based on method
    if method == "forward":
        # D_i = (V_{i+1} - V_i) / (t_{i+1} - t_i)
        d_var = np.diff(variance_array)
        d_time = np.diff(time_array)
        # Avoid division by zero
        d_time = np.where(d_time == 0, 1e-10, d_time)
        diffusion_rates = d_var / d_time

    elif method == "backward":
        # D_i = (V_i - V_{i-1}) / (t_i - t_{i-1})
        d_var = np.diff(variance_array)
        d_time = np.diff(time_array)
        d_time = np.where(d_time == 0, 1e-10, d_time)
        # Shift to align with current time step (index 1 to end)
        diffusion_rates = d_var / d_time

    elif method == "central":
        # D_i = (V_{i+1} - V_{i-1}) / (t_{i+1} - t_{i-1})
        # Valid for indices 1 to N-2
        if len(variance_array) < 3:
            logger.warning(
                "Central difference method requires at least 3 time steps. "
                "Falling back to forward difference."
            )
            d_var = np.diff(variance_array)
            d_time = np.diff(time_array)
            d_time = np.where(d_time == 0, 1e-10, d_time)
            diffusion_rates = d_var / d_time
        else:
            d_var = variance_array[2:] - variance_array[:-2]
            d_time = time_array[2:] - time_array[:-2]
            d_time = np.where(d_time == 0, 1e-10, d_time)
            diffusion_rates = d_var / d_time
    else:
        raise ValueError(f"Unknown finite difference method: {method}")

    # Calculate statistics
    mean_rate = float(np.mean(diffusion_rates))
    max_rate = float(np.max(diffusion_rates))
    min_rate = float(np.min(diffusion_rates))

    # Validate against minimum increase threshold
    # If the total variance increase is less than min_variance_increase, mark as invalid
    total_variance_change = variance_array[-1] - variance_array[0]
    is_valid = total_variance_change >= min_variance_increase

    if not is_valid:
        logger.warning(
            f"Total variance change ({total_variance_change}) is less than "
            f"minimum required ({min_variance_increase}). Diffusion rate may be invalid."
        )

    return {
        "diffusion_rates": diffusion_rates.tolist(),
        "mean_diffusion_rate": mean_rate,
        "max_diffusion_rate": max_rate,
        "min_diffusion_rate": min_rate,
        "is_monotonic": is_monotonic,
        "monotonicity_violations": monotonicity_violations,
        "valid": is_valid,
        "error_message": None
    }


def compute_diffusion_from_simulation(
    spin_states_history: List[np.ndarray],
    graph: Any,
    time_steps: List[float],
    method: str = "forward"
) -> Dict[str, Any]:
    """
    Compute diffusion rate directly from a history of spin states.

    Args:
        spin_states_history: List of 1D arrays, each representing spin states at a time step.
        graph: NetworkX graph object (used for spatial variance calculation).
        time_steps: List of time values corresponding to each spin state.
        method: Finite difference method for rate calculation.

    Returns:
        Dictionary with diffusion rate metrics and intermediate variance history.
    """
    if len(spin_states_history) != len(time_steps):
        raise ValueError(
            f"spin_states_history and time_steps must have the same length. "
            f"Got {len(spin_states_history)} and {len(time_steps)}."
        )

    variance_history = []
    for i, states in enumerate(spin_states_history):
        try:
            variance = compute_spatial_variance(states, graph)
            variance_history.append(variance)
        except Exception as e:
            logger.error(f"Failed to compute variance at time step {i}: {e}")
            raise

    return calculate_diffusion_rate(
        variance_history=variance_history,
        time_steps=time_steps,
        method=method
    )