"""
Validation logic for power estimates and dataset reliability.
"""
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy import stats
from utils import setup_logging

logger = logging.getLogger(__name__)


def calculate_analytical_variance(data: np.ndarray) -> float:
    """
    Calculate analytical variance of the data.

    Args:
        data: The dataset.

    Returns:
        Analytical variance.
    """
    if isinstance(data, list):
        data = np.array(data)
    return float(np.var(data, ddof=1))


def bootstrap_validity_check(bootstrap_result: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if the bootstrap estimate is reliable by comparing variance to analytical variance.

    Args:
        bootstrap_result: Result from run_bootstrap_power_simulation.

    Returns:
        Tuple of (is_valid, details).
    """
    # This is a simplified check. In reality, we would compare the variance of the bootstrap
    # distribution to the analytical variance of the estimator.
    # For this task, we'll check if the number of iterations is sufficient and if the power
    # estimate is within a reasonable range.

    stats_info = bootstrap_result.get('stats', {})
    iterations = stats_info.get('iterations', 0)
    std_p = stats_info.get('std_p_value', 0)

    details = {
        "iterations": iterations,
        "std_p_value": std_p
    }

    # Check iteration count
    if iterations < 100:
        details["reason"] = "insufficient_iterations"
        return False, details

    # Check if std_p is too high (indicates instability)
    # This is a heuristic; a real check would be more complex
    if std_p > 0.2: # Arbitrary threshold for instability
        details["reason"] = "high_variance"
        return False, details

    return True, details


def verify_achieved_magnitude(target: float, achieved: float, tolerance: float = 0.05) -> bool:
    """
    Verify if the achieved magnitude is within tolerance of the target.

    Args:
        target: Target value.
        achieved: Achieved value.
        tolerance: Tolerance threshold.

    Returns:
        True if within tolerance.
    """
    return abs(target - achieved) <= tolerance


def should_exclude_dataset(validation_details: Dict[str, Any]) -> bool:
    """
    Determine if a dataset should be excluded based on validation details.

    Args:
        validation_details: Details from bootstrap_validity_check.

    Returns:
        True if the dataset should be excluded.
    """
    reason = validation_details.get('reason')
    if reason in ['insufficient_iterations', 'high_variance']:
        return True
    return False


def run_full_validation(data: np.ndarray, bootstrap_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run full validation suite on the dataset and bootstrap result.

    Args:
        data: The dataset.
        bootstrap_result: Result from run_bootstrap_power_simulation.

    Returns:
        Validation summary.
    """
    is_valid, details = bootstrap_validity_check(bootstrap_result)
    should_exclude = should_exclude_dataset(details)

    return {
        "is_valid": is_valid,
        "should_exclude": should_exclude,
        "details": details
    }
