"""
Numerical stability utilities for chaotic system simulations.

Provides tools for:
- Convergence detection (checking if sequences stabilize)
- Boundedness checks (verifying trajectories stay within physical limits)
- Divergence rate detection
- Comprehensive numerical validity reporting
"""

import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass, field
import warnings
import sys

# Import numerical settings from config
try:
    from ..config import NumericalSettings, get_full_config
except ImportError:
    # Fallback for direct execution/testing
    from config import NumericalSettings, get_full_config


class NumericalStabilityError(Exception):
    """Base exception for numerical stability issues."""
    pass


class DivergenceError(NumericalStabilityError):
    """Raised when a trajectory diverges beyond acceptable bounds."""
    pass


class NonConvergenceError(NumericalStabilityError):
    """Raised when a sequence fails to converge within tolerance."""
    pass


@dataclass
class StabilityReport:
    """
    Comprehensive report on the numerical stability of a trajectory or sequence.

    Attributes:
        is_valid: Overall validity flag
        boundedness_check: Result of boundedness check
        convergence_check: Result of convergence check (if applicable)
        divergence_rate: Estimated rate of divergence (if detected)
        max_value: Maximum absolute value observed
        mean_value: Mean absolute value observed
        warnings: List of warning messages
        details: Dictionary of additional diagnostic information
    """
    is_valid: bool
    boundedness_check: Optional[dict] = None
    convergence_check: Optional[dict] = None
    divergence_rate: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert report to dictionary for serialization."""
        return {
            'is_valid': self.is_valid,
            'boundedness_check': self.boundedness_check,
            'convergence_check': self.convergence_check,
            'divergence_rate': self.divergence_rate,
            'max_value': self.max_value,
            'mean_value': self.mean_value,
            'warnings': self.warnings,
            'details': self.details
        }


def check_numerical_validity(
    trajectory: np.ndarray,
    settings: Optional[NumericalSettings] = None
) -> StabilityReport:
    """
    Perform a comprehensive numerical validity check on a trajectory.

    Args:
        trajectory: 2D array of shape (time_steps, dimensions)
        settings: Numerical settings configuration

    Returns:
        StabilityReport with all checks performed
    """
    if settings is None:
        config = get_full_config()
        settings = config.numerical

    report = StabilityReport(is_valid=True)
    report.details['shape'] = trajectory.shape
    report.details['dtype'] = str(trajectory.dtype)

    # Check for NaN or Inf
    if np.any(np.isnan(trajectory)):
        report.is_valid = False
        report.warnings.append("NaN values detected in trajectory")
        report.details['nan_count'] = int(np.sum(np.isnan(trajectory)))

    if np.any(np.isinf(trajectory)):
        report.is_valid = False
        report.warnings.append("Inf values detected in trajectory")
        report.details['inf_count'] = int(np.sum(np.isinf(trajectory)))

    # Compute basic statistics
    report.max_value = float(np.max(np.abs(trajectory)))
    report.mean_value = float(np.mean(np.abs(trajectory)))

    # Perform boundedness check
    boundedness_result = check_boundedness(trajectory, settings)
    report.boundedness_check = boundedness_result
    if not boundedness_result['is_bounded']:
        report.is_valid = False
        report.warnings.append(f"Boundedness check failed: {boundedness_result['reason']}")

    # Perform convergence check (for the last portion of trajectory)
    if trajectory.shape[0] > settings.convergence_window:
        convergence_result = check_convergence(
            trajectory[-settings.convergence_window:],
            settings
        )
        report.convergence_check = convergence_result
        if not convergence_result['has_converged']:
            # Not necessarily invalid, but worth noting
            report.warnings.append("Convergence check indicates non-convergence in final window")

    return report


def check_boundedness(
    trajectory: np.ndarray,
    settings: Optional[NumericalSettings] = None,
    threshold: Optional[float] = None
) -> dict:
    """
    Check if a trajectory remains within physically reasonable bounds.

    For chaotic systems like Lorenz, trajectories should stay within
    a bounded attractor. This function checks if any point exceeds
    the specified threshold.

    Args:
        trajectory: 2D array of shape (time_steps, dimensions)
        settings: Numerical settings (provides default threshold)
        threshold: Maximum allowed absolute value (overrides settings)

    Returns:
        Dictionary with 'is_bounded' boolean and 'reason' string
    """
    if settings is None:
        config = get_full_config()
        settings = config.numerical

    if threshold is None:
        threshold = settings.boundedness_threshold

    max_val = np.max(np.abs(trajectory))

    if max_val > threshold:
        # Find when it first exceeded
        flat_trajectory = np.abs(trajectory)
        exceeded_mask = flat_trajectory > threshold
        first_exceed_idx = np.argmax(exceeded_mask.any(axis=1))
        time_exceeded = first_exceed_idx if exceeded_mask.any() else -1

        return {
            'is_bounded': False,
            'reason': f"Trajectory exceeded bound {threshold} at time step {time_exceeded} (max={max_val})",
            'max_value': float(max_val),
            'threshold': threshold,
            'time_exceeded': int(time_exceeded)
        }

    return {
        'is_bounded': True,
        'reason': f"All values within bound {threshold} (max={max_val})",
        'max_value': float(max_val),
        'threshold': threshold
    }


def check_convergence(
    sequence: np.ndarray,
    settings: Optional[NumericalSettings] = None,
    window_ratio: float = 0.5
) -> dict:
    """
    Check if a sequence has converged to a stable value.

    Uses relative change over a sliding window to detect convergence.

    Args:
        sequence: 1D or 2D array (time_steps, dimensions) or (time_steps,)
        settings: Numerical settings (provides tolerances)
        window_ratio: Fraction of sequence to use for final convergence check

    Returns:
        Dictionary with 'has_converged' boolean and diagnostic info
    """
    if settings is None:
        config = get_full_config()
        settings = config.numerical

    if len(sequence.shape) == 1:
        sequence = sequence.reshape(-1, 1)

    n_steps = sequence.shape[0]
    window_size = max(int(n_steps * window_ratio), settings.convergence_window)

    if n_steps < window_size:
        return {
            'has_converged': False,
            'reason': f"Sequence too short ({n_steps}) for convergence check (need >= {window_size})",
            'window_size': window_size
        }

    # Compute differences in the final window
    final_window = sequence[-window_size:]
    differences = np.abs(np.diff(final_window, axis=0))

    # Check if max relative change is below tolerance
    mean_values = np.mean(np.abs(final_window), axis=0)
    # Avoid division by zero
    mean_values = np.where(mean_values == 0, 1e-16, mean_values)

    relative_changes = np.max(differences, axis=0) / mean_values

    max_relative_change = np.max(relative_changes)

    if max_relative_change < settings.convergence_tolerance:
        return {
            'has_converged': True,
            'reason': f"Converged with max relative change {max_relative_change:.2e} < {settings.convergence_tolerance}",
            'max_relative_change': float(max_relative_change),
            'tolerance': settings.convergence_tolerance,
            'window_size': window_size
        }
    else:
        return {
            'has_converged': False,
            'reason': f"Did not converge: max relative change {max_relative_change:.2e} >= {settings.convergence_tolerance}",
            'max_relative_change': float(max_relative_change),
            'tolerance': settings.convergence_tolerance,
            'window_size': window_size
        }


def detect_divergence_rate(
    trajectory: np.ndarray,
    settings: Optional[NumericalSettings] = None
) -> Tuple[Optional[float], dict]:
    """
    Estimate the rate of divergence for a trajectory.

    Uses linear regression on log(abs(value)) vs time to estimate
    exponential growth rate (Lyapunov-like exponent).

    Args:
        trajectory: 2D array of shape (time_steps, dimensions)
        settings: Numerical settings

    Returns:
        Tuple of (divergence_rate, diagnostics)
        divergence_rate is None if no divergence detected or insufficient data
    """
    if trajectory.shape[0] < 10:
        return None, {'reason': 'Insufficient data points for divergence analysis'}

    # Use the norm of the state vector over time
    norms = np.linalg.norm(trajectory, axis=1)

    # Avoid log(0)
    norms_safe = np.where(norms == 0, 1e-16, norms)
    log_norms = np.log(norms_safe)

    # Linear regression: log_norms = rate * time + intercept
    time_steps = np.arange(len(log_norms))

    # Compute slope using least squares
    n = len(time_steps)
    sum_x = np.sum(time_steps)
    sum_y = np.sum(log_norms)
    sum_xy = np.sum(time_steps * log_norms)
    sum_xx = np.sum(time_steps ** 2)

    denominator = n * sum_xx - sum_x ** 2
    if abs(denominator) < 1e-16:
        return None, {'reason': 'Cannot compute regression: denominator too small'}

    rate = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - rate * sum_x) / n

    # Compute R-squared
    y_pred = rate * time_steps + intercept
    ss_res = np.sum((log_norms - y_pred) ** 2)
    ss_tot = np.sum((log_norms - np.mean(log_norms)) ** 2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    diagnostics = {
        'rate': float(rate),
        'intercept': float(intercept),
        'r_squared': float(r_squared),
        'initial_norm': float(norms[0]),
        'final_norm': float(norms[-1]),
        'total_growth': float(norms[-1] / norms[0]) if norms[0] > 0 else float('inf')
    }

    # Determine if this indicates divergence
    is_diverging = rate > settings.divergence_rate_threshold
    diagnostics['is_diverging'] = is_diverging
    diagnostics['threshold'] = settings.divergence_rate_threshold

    if is_diverging:
        return rate, diagnostics
    else:
        return None, diagnostics


def validate_trajectory(
    trajectory: np.ndarray,
    settings: Optional[NumericalSettings] = None,
    raise_on_error: bool = False
) -> StabilityReport:
    """
    Validate a trajectory against all numerical stability criteria.

    This is a convenience function that combines all checks and
    optionally raises exceptions.

    Args:
        trajectory: 2D array of shape (time_steps, dimensions)
        settings: Numerical settings
        raise_on_error: If True, raise exceptions on failures

    Returns:
        StabilityReport

    Raises:
        NumericalStabilityError: If trajectory contains NaN/Inf and raise_on_error=True
        DivergenceError: If trajectory diverges and raise_on_error=True
        NonConvergenceError: If trajectory doesn't converge and raise_on_error=True
    """
    report = check_numerical_validity(trajectory, settings)

    if raise_on_error:
        if not report.is_valid:
            if any("NaN" in w or "Inf" in w for w in report.warnings):
                raise NumericalStabilityError(f"Invalid trajectory: {report.warnings}")
            if any("Boundedness" in w for w in report.warnings):
                raise DivergenceError(f"Trajectory diverged: {report.warnings}")

        # Check divergence rate
        if trajectory.shape[0] >= 10:
            rate, diag = detect_divergence_rate(trajectory, settings)
            if rate is not None and rate > settings.divergence_rate_threshold * 2:
                raise DivergenceError(
                    f"Excessive divergence rate detected: {rate:.4f} > {settings.divergence_rate_threshold * 2}"
                )

    return report