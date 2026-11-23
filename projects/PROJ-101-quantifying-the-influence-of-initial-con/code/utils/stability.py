"""
Numerical stability utilities for trajectory analysis.

This module provides functions to check numerical validity, boundedness,
convergence, and divergence detection for chaotic system trajectories.
It also includes a guard that raises an error when a trajectory becomes
unphysical (state norm exceeds a safe threshold) and a helper to emit a
warning for excessively noisy simulations.
"""
import numpy as np
import warnings
import logging
from dataclasses import dataclass, field
from typing import Tuple, Optional, List

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Exceptions
# ----------------------------------------------------------------------
class NumericalStabilityError(Exception):
    """Exception raised for numerical stability violations."""
    pass


class DivergenceError(Exception):
    """Exception raised when a trajectory diverges beyond acceptable bounds."""
    pass


class NonConvergenceError(Exception):
    """Exception raised when convergence criteria are not met."""
    pass


# ----------------------------------------------------------------------
# Data container
# ----------------------------------------------------------------------
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
            "details": self.details,
        }


# ----------------------------------------------------------------------
# Numerical checks
# ----------------------------------------------------------------------
def check_numerical_validity(
    state_vector: np.ndarray,
    threshold: float = 1e12,
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
        warnings_list.append(
            f"State vector values exceed threshold ({max_val:.2e} > {threshold:.2e})"
        )
        is_valid = False

    return is_valid, warnings_list


def check_boundedness(
    state_vector: np.ndarray,
    threshold: float = 20.0,
) -> bool:
    """
    Check if a state vector remains within acceptable bounds.

    The default threshold (20.0) implements the project‑specific guard
    that defines an *unphysical* trajectory.

    Args:
        state_vector: The state vector to check.
        threshold: Maximum allowed absolute value (default 20.0).

    Returns:
        True if bounded, False otherwise.
    """
    if state_vector.size == 0:
        return True

    max_val = np.max(np.abs(state_vector))
    is_bounded = max_val <= threshold

    if not is_bounded:
        logger.warning(
            f"State vector exceeds bound: max(|state|) = {max_val:.2e} > {threshold}"
        )

    return is_bounded


def raise_if_unphysical(
    state_vector: np.ndarray,
    threshold: float = 20.0,
) -> None:
    """
    Guard that raises :class:`UnphysicalTrajectoryError` if the Euclidean norm
    of the supplied state vector exceeds ``threshold`` (default 20.0).

    This function is deliberately lightweight and performs the check
    lazily; callers should invoke it at each integration step or after a
    batch integration to enforce the boundedness contract required by
    task **T007**.

    Args:
        state_vector: The state vector (or full trajectory array) to inspect.
        threshold: Norm threshold beyond which the trajectory is considered
                   unphysical.

    Raises:
        UnphysicalTrajectoryError: If ``np.linalg.norm(state_vector)`` > ``threshold``.
    """
    # Local import to avoid circular dependencies (data.generator also imports this module)
    from ..data.generator import UnphysicalTrajectoryError

    # Compute the Euclidean norm (L2) of the vector or, if a 2‑D array is given,
    # the maximum norm across all time steps.
    if state_vector.ndim == 1:
        norm_val = np.linalg.norm(state_vector)
    else:
        # For a full trajectory we consider the worst‑case norm.
        norm_val = np.max(np.linalg.norm(state_vector, axis=1))

    if norm_val > threshold:
        raise UnphysicalTrajectoryError(
            f"Unphysical trajectory: norm {norm_val:.2f} exceeds allowed maximum {threshold}"
        )


def check_noise_level(
    sigma_noise: float,
    threshold: float = 0.1,
) -> None:
    """
    Emit a :class:`HighNoiseWarning` if the supplied noise level exceeds the
    configured threshold.

    The warning class ``HighNoiseWarning`` is defined in ``data.generator``.
    Importing it lazily avoids circular imports.

    Args:
        sigma_noise: The standard deviation of the injected Gaussian noise.
        threshold: Noise level above which a warning is raised (default 0.1).

    Raises:
        None – the function only emits a warning.
    """
    if sigma_noise > threshold:
        # Import inside the function to avoid circular imports.
        from ..data.generator import HighNoiseWarning

        warnings.warn(
            HighNoiseWarning(
                f"High noise level: sigma_noise={sigma_noise:.4f} exceeds {threshold}"
            ),
            category=HighNoiseWarning,
        )


def check_convergence(
    values: np.ndarray,
    tol: float = 1e-6,
    window: int = 10,
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
        logger.debug(
            f"Convergence not achieved: max relative change = {max_rel_change:.2e} > {tol}"
        )

    return is_converged


def detect_divergence_rate(
    trajectory: np.ndarray,
    time_steps: Optional[np.ndarray] = None,
) -> Optional[float]:
    """
    Estimate the divergence rate of a trajectory.

    Args:
        trajectory: 2D array of shape (n_steps, n_dims).
        time_steps: Optional array of time values.

    Returns:
        Estimated divergence rate (Lyapunov‑like), or None if undetectable.
    """
    if trajectory.ndim != 2 or trajectory.shape[0] < 2:
        return None

    n_steps, n_dims = trajectory.shape

    if time_steps is None:
        time_steps = np.arange(n_steps)

    norms = np.linalg.norm(trajectory, axis=1)

    valid_mask = norms > 1e-12
    if np.sum(valid_mask) < 2:
        return None

    valid_times = time_steps[valid_mask]
    valid_norms = norms[valid_mask]

    log_norms = np.log(valid_norms)

    try:
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
    convergence_tol: float = 1e-6,
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

    # Check boundedness (legacy threshold)
    max_val = np.max(np.abs(trajectory))
    if max_val > max_bound:
        bounded = False
        warnings_list.append(f"Trajectory exceeds bound: {max_val:.2e} > {max_bound}")
        is_stable = False

    # Additional check using the new guard (threshold 20.0)
    try:
        raise_if_unphysical(trajectory, threshold=20.0)
    except Exception as e:
        # The guard raises UnphysicalTrajectoryError; we record it as unbounded.
        bounded = False
        warnings_list.append(str(e))
        is_stable = False

    # Check convergence if requested
    if check_convergence and n_steps > 10:
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
            "mean_norm": float(np.mean(np.linalg.norm(trajectory, axis=1))),
        },
    )