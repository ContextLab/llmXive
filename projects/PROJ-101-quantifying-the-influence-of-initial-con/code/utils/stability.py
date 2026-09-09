"""
Numerical stability utilities for trajectory analysis.

This module provides functions to check numerical validity, boundedness,
convergence, and divergence detection for chaotic system trajectories.
"""
import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass, field
import warnings
import sys

# Configure logging
import logging
logger = logging.getLogger(__name__)


class NumericalStabilityError(Exception):
    """Exception raised for numerical stability violations."""
    pass


class DivergenceError(Exception):
    """Exception raised when a trajectory diverges beyond acceptable bounds."""
    pass


class NonConvergenceError(Exception):
    """Exception raised when convergence criteria are not met."""
    pass


@dataclass
class StabilityReport:
    """Container for stability analysis results."""
    is_stable: bool
    bounded: bool
    converged: bool
    max_value: float
    divergence_rate: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "is_stable": self.is_stable,
            "bounded": self.bounded,
            "converged": self.converged,
            "max_value": self.max_value,
            "divergence_rate": self.divergence_rate,
            "warnings": self.warnings,
            "details": self.details
        }


def check_numerical_validity(
    state_vector: np.ndarray,
    threshold: float = 1e12
) -> Tuple[bool, List[str]]:
    """
    Check if a state vector contains valid numerical values.

    Args:
        state_vector: The state vector to check.
        threshold: Threshold for considering values as overflow.

    Returns:
        Tuple of (is_valid, list_of_warnings).
    """
    warnings_list = []
    is_valid = True

    # Check for NaN
    if np.any(np.isnan(state_vector)):
        warnings_list.append("State vector contains NaN values")
        is_valid = False

    # Check for Inf
    if np.any(np.isinf(state_vector)):
        warnings_list.append("State vector contains Inf values")
        is_valid = False

    # Check for overflow
    max_val = np.max(np.abs(state_vector))
    if max_val > threshold:
        warnings_list.append(f"State vector values exceed threshold ({max_val:.2e} > {threshold:.2e})")
        is_valid = False

    return is_valid, warnings_list


def check_boundedness(
    state_vector: np.ndarray,
    threshold: float = 100.0
) -> bool:
    """
    Check if a state vector remains within acceptable bounds.

    Args:
        state_vector: The state vector to check.
        threshold: Maximum allowed absolute value.

    Returns:
        True if bounded, False otherwise.
    """
    if state_vector.size == 0:
        return True

    max_val = np.max(np.abs(state_vector))
    is_bounded = max_val <= threshold

    if not is_bounded:
        logger.warning(f"State vector exceeds bound: max(|state|) = {max_val:.2e} > {threshold}")

    return is_bounded


def check_convergence(
    values: np.ndarray,
    tol: float = 1e-6,
    window: int = 10
) -> bool:
    """
    Check if a sequence of values has converged.

    Args:
        values: Array of values to check.
        tol: Tolerance for convergence.
        window: Number of recent values to compare.

    Returns:
        True if converged, False otherwise.
    """
    if len(values) < window + 1:
        return False

    # Check relative change in the last 'window' values
    recent_values = values[-window:]
    max_rel_change = 0.0

    for i in range(1, len(recent_values)):
        denom = abs(recent_values[i - 1])
        if denom < 1e-12:
            rel_change = abs(recent_values[i])
        else:
            rel_change = abs(recent_values[i] - recent_values[i - 1]) / denom
        max_rel_change = max(max_rel_change, rel_change)

    is_converged = max_rel_change < tol

    if not is_converged:
        logger.debug(f"Convergence not achieved: max relative change = {max_rel_change:.2e} > {tol}")

    return is_converged


def detect_divergence_rate(
    trajectory: np.ndarray,
    time_steps: Optional[np.ndarray] = None
) -> Optional[float]:
    """
    Estimate the divergence rate of a trajectory.

    Args:
        trajectory: 2D array of shape (n_steps, n_dims).
        time_steps: Optional array of time values.

    Returns:
        Estimated divergence rate (Lyapunov-like), or None if undetectable.
    """
    if trajectory.ndim != 2 or trajectory.shape[0] < 2:
        return None

    n_steps, n_dims = trajectory.shape

    # Use default time steps if not provided
    if time_steps is None:
        time_steps = np.arange(n_steps)

    # Compute norm at each step
    norms = np.linalg.norm(trajectory, axis=1)

    # Filter out zero or near-zero norms to avoid log issues
    valid_mask = norms > 1e-12
    if np.sum(valid_mask) < 2:
        return None

    valid_times = time_steps[valid_mask]
    valid_norms = norms[valid_mask]

    # Log-transform
    log_norms = np.log(valid_norms)

    # Simple linear fit to estimate growth rate
    try:
        # Fit log_norm = rate * time + intercept
        coeffs = np.polyfit(valid_times, log_norms, 1)
        rate = coeffs[0]
        return rate
    except (ValueError, np.linalg.LinAlgError):
        return None


def validate_trajectory(
    trajectory: np.ndarray,
    max_bound: float = 100.0,
    min_steps: int = 100,
    check_convergence: bool = False,
    convergence_tol: float = 1e-6
) -> StabilityReport:
    """
    Perform a comprehensive validation of a trajectory.

    Args:
        trajectory: 2D array of shape (n_steps, n_dims).
        max_bound: Maximum allowed absolute value for any state component.
        min_steps: Minimum required number of time steps.
        check_convergence: Whether to check for convergence.
        convergence_tol: Tolerance for convergence check.

    Returns:
        StabilityReport with validation results.
    """
    warnings_list = []
    is_stable = True
    bounded = True
    converged = True

    # Check dimensions
    if trajectory.ndim != 2:
        warnings_list.append(f"Trajectory should be 2D, got {trajectory.ndim}D")
        is_stable = False

    n_steps, n_dims = trajectory.shape

    # Check minimum steps
    if n_steps < min_steps:
        warnings_list.append(f"Trajectory too short: {n_steps} < {min_steps} steps")
        is_stable = False

    # Check numerical validity
    is_valid, validity_warnings = check_numerical_validity(trajectory.flatten())
    warnings_list.extend(validity_warnings)
    if not is_valid:
        is_stable = False

    # Check boundedness
    max_val = np.max(np.abs(trajectory))
    if max_val > max_bound:
        bounded = False
        warnings_list.append(f"Trajectory exceeds bound: {max_val:.2e} > {max_bound}")
        is_stable = False

    # Check convergence if requested
    if check_convergence and n_steps > 10:
        # Use the norm of the state for convergence check
        norms = np.linalg.norm(trajectory, axis=1)
        converged = check_convergence(norms, tol=convergence_tol)
        if not converged:
            warnings_list.append("Trajectory does not appear to have converged")

    # Detect divergence rate
    divergence_rate = detect_divergence_rate(trajectory)

    return StabilityReport(
        is_stable=is_stable,
        bounded=bounded,
        converged=converged,
        max_value=float(max_val),
        divergence_rate=divergence_rate,
        warnings=warnings_list,
        details={
            "n_steps": n_steps,
            "n_dims": n_dims,
            "min_value": float(np.min(trajectory)),
            "mean_norm": float(np.mean(np.linalg.norm(trajectory, axis=1)))
        }
    )
