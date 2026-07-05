"""
Numerical stability checks for spin system simulations.

Implements divergence detection to ensure the simulation does not
produce NaN, Inf, or unbounded energy values.
"""

import numpy as np
import logging
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger(__name__)

# Default thresholds for stability checks
DEFAULT_MAX_ENERGY_VALUE = 1e10
DEFAULT_MAX_SPATIAL_VARIANCE = 1e10
DEFAULT_ABS_TOLERANCE = 1e-9
DEFAULT_REL_TOLERANCE = 1e-6

class StabilityError(RuntimeError):
    """Custom exception for simulation stability failures."""
    pass

def check_for_nan_inf(
    array: np.ndarray, 
    name: str = "array", 
    raise_on_error: bool = True
) -> bool:
    """
    Check if an array contains NaN or Inf values.
    
    Args:
        array: The numpy array to check.
        name: Name of the array for logging purposes.
        raise_on_error: If True, raise StabilityError on detection.
        
    Returns:
        True if array is clean (no NaN/Inf), False otherwise.
        
    Raises:
        StabilityError: If NaN/Inf is detected and raise_on_error is True.
    """
    has_nan = np.any(np.isnan(array))
    has_inf = np.any(np.isinf(array))
    
    if has_nan or has_inf:
        msg = f"Numerical instability detected in {name}: NaN={has_nan}, Inf={has_inf}"
        logger.error(msg)
        if raise_on_error:
            raise StabilityError(msg)
        return False
    
    logger.debug(f"Stability check passed for {name}: no NaN/Inf")
    return True

def check_value_bounds(
    value: float, 
    max_value: float, 
    name: str = "value", 
    raise_on_error: bool = True
) -> bool:
    """
    Check if a scalar value exceeds a maximum threshold.
    
    Args:
        value: The scalar value to check.
        max_value: The maximum allowed absolute value.
        name: Name of the variable for logging.
        raise_on_error: If True, raise StabilityError on violation.
        
    Returns:
        True if value is within bounds, False otherwise.
        
    Raises:
        StabilityError: If value exceeds bounds and raise_on_error is True.
    """
    if abs(value) > max_value:
        msg = f"Value overflow detected in {name}: |{value}| > {max_value}"
        logger.error(msg)
        if raise_on_error:
            raise StabilityError(msg)
        return False
    
    logger.debug(f"Stability check passed for {name}: {value} <= {max_value}")
    return True

def check_spatial_variance_stability(
    variance_history: List[float],
    max_variance: float = DEFAULT_MAX_SPATIAL_VARIANCE,
    raise_on_error: bool = True
) -> bool:
    """
    Check if spatial variance values are within stable bounds.
    
    Args:
        variance_history: List of spatial variance values over time steps.
        max_variance: Maximum allowed variance threshold.
        raise_on_error: If True, raise StabilityError on violation.
        
    Returns:
        True if all variance values are stable, False otherwise.
    """
    if not variance_history:
        logger.warning("Empty variance history provided for stability check")
        return True
        
    for idx, var in enumerate(variance_history):
        if not check_value_bounds(var, max_variance, f"variance[t={idx}]", raise_on_error):
            return False
    return True

def check_energy_density_stability(
    energy_profile: np.ndarray,
    max_energy: float = DEFAULT_MAX_ENERGY_VALUE,
    raise_on_error: bool = True
) -> bool:
    """
    Check if energy density profile is within stable bounds.
    
    Args:
        energy_profile: Array of energy density values.
        max_energy: Maximum allowed energy density value.
        raise_on_error: If True, raise StabilityError on violation.
        
    Returns:
        True if energy profile is stable, False otherwise.
    """
    if not check_for_nan_inf(energy_profile, "energy_profile", raise_on_error):
        return False
        
    return check_value_bounds(
        np.max(np.abs(energy_profile)), 
        max_energy, 
        "energy_profile_max", 
        raise_on_error
    )

def detect_divergence(
    current_state: np.ndarray,
    previous_state: np.ndarray,
    abs_tol: float = DEFAULT_ABS_TOLERANCE,
    rel_tol: float = DEFAULT_REL_TOLERANCE,
    raise_on_error: bool = True
) -> bool:
    """
    Detect if the system is diverging by comparing state changes.
    
    A system is considered diverging if the relative change between
    consecutive states exceeds tolerance thresholds.
    
    Args:
        current_state: Current state vector (spins or energies).
        previous_state: Previous state vector.
        abs_tol: Absolute tolerance for small values.
        rel_tol: Relative tolerance for larger values.
        raise_on_error: If True, raise StabilityError on divergence.
        
    Returns:
        True if system is stable (no divergence), False if diverging.
        
    Raises:
        StabilityError: If divergence is detected and raise_on_error is True.
    """
    if current_state.shape != previous_state.shape:
        msg = f"State shape mismatch: {current_state.shape} vs {previous_state.shape}"
        logger.error(msg)
        if raise_on_error:
            raise StabilityError(msg)
        return False
    
    # Calculate relative difference
    diff = np.abs(current_state - previous_state)
    scale = np.maximum(np.abs(current_state), np.abs(previous_state))
    
    # Handle zero-scale case
    scale = np.where(scale < abs_tol, abs_tol, scale)
    relative_diff = diff / scale
    
    max_relative_change = np.max(relative_diff)
    
    if max_relative_change > rel_tol:
        msg = f"System divergence detected: max relative change {max_relative_change:.2e} > {rel_tol:.2e}"
        logger.error(msg)
        if raise_on_error:
            raise StabilityError(msg)
        return False
    
    logger.debug(f"Stability check passed: max relative change {max_relative_change:.2e}")
    return True

def run_full_stability_check(
    energy_profile: np.ndarray,
    variance_history: List[float],
    current_state: Optional[np.ndarray] = None,
    previous_state: Optional[np.ndarray] = None,
    max_energy: float = DEFAULT_MAX_ENERGY_VALUE,
    max_variance: float = DEFAULT_MAX_SPATIAL_VARIANCE,
    abs_tol: float = DEFAULT_ABS_TOLERANCE,
    rel_tol: float = DEFAULT_REL_TOLERANCE,
    raise_on_error: bool = True
) -> Dict[str, bool]:
    """
    Run a comprehensive suite of stability checks.
    
    Args:
        energy_profile: Current energy density profile.
        variance_history: List of spatial variance values.
        current_state: Current system state (optional, for divergence check).
        previous_state: Previous system state (optional, for divergence check).
        max_energy: Maximum allowed energy value.
        max_variance: Maximum allowed variance value.
        abs_tol: Absolute tolerance for divergence check.
        rel_tol: Relative tolerance for divergence check.
        raise_on_error: If True, raise on first failure.
        
    Returns:
        Dictionary with check names and pass/fail status.
    """
    results = {
        "energy_profile_nan_inf": True,
        "energy_profile_bounds": True,
        "variance_stability": True,
        "divergence_detection": True
    }
    
    # Check energy profile for NaN/Inf
    try:
        results["energy_profile_nan_inf"] = check_for_nan_inf(
            energy_profile, "energy_profile", raise_on_error=False
        )
    except StabilityError:
        results["energy_profile_nan_inf"] = False
    
    # Check energy profile bounds
    if results["energy_profile_nan_inf"]:
        try:
            results["energy_profile_bounds"] = check_energy_density_stability(
                energy_profile, max_energy, raise_on_error=False
            )
        except StabilityError:
            results["energy_profile_bounds"] = False
    
    # Check variance history
    try:
        results["variance_stability"] = check_spatial_variance_stability(
            variance_history, max_variance, raise_on_error=False
        )
    except StabilityError:
        results["variance_stability"] = False
    
    # Check divergence if states provided
    if current_state is not None and previous_state is not None:
        try:
            results["divergence_detection"] = detect_divergence(
                current_state, previous_state, abs_tol, rel_tol, raise_on_error=False
            )
        except StabilityError:
            results["divergence_detection"] = False
    
    # Log summary
    all_passed = all(results.values())
    if not all_passed:
        failed_checks = [k for k, v in results.items() if not v]
        logger.error(f"Stability check failed for: {', '.join(failed_checks)}")
        if raise_on_error:
            raise StabilityError(f"Stability checks failed: {failed_checks}")
    else:
        logger.debug("All stability checks passed")
    
    return results

def validate_metrics_stability(
    metrics: Dict[str, Any],
    raise_on_error: bool = True
) -> bool:
    """
    Validate stability of computed simulation metrics.
    
    Args:
        metrics: Dictionary containing simulation metrics.
        raise_on_error: If True, raise StabilityError on failure.
        
    Returns:
        True if all metrics are stable, False otherwise.
    """
    energy_profile = metrics.get("energy_profile")
    variance_history = metrics.get("variance_history", [])
    current_state = metrics.get("current_state")
    previous_state = metrics.get("previous_state")
    
    if energy_profile is None:
        logger.warning("No energy profile found in metrics for stability check")
        return True
    
    if not isinstance(variance_history, list):
        variance_history = [variance_history] if variance_history is not None else []
    
    try:
        results = run_full_stability_check(
            energy_profile,
            variance_history,
            current_state,
            previous_state,
            raise_on_error=raise_on_error
        )
        return all(results.values())
    except StabilityError:
        return False