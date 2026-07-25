"""
Covariance regularization utilities.
"""
import numpy as np
from typing import Tuple, Optional
from .exceptions import HighDimensionalInstabilityError

def is_condition_number_acceptable(
    matrix: np.ndarray,
    threshold: float = 1e12
) -> bool:
    """
    Check if the condition number of a matrix is acceptable.

    Args:
        matrix: Input matrix
        threshold: Maximum acceptable condition number

    Returns:
        True if condition number is below threshold, False otherwise.
    """
    try:
        cond = np.linalg.cond(matrix)
        return cond < threshold
    except np.linalg.LinAlgError:
        return False

def regularize_covariance(
    cov_matrix: np.ndarray,
    alpha: float = 0.01,
    threshold: float = 1e12
) -> np.ndarray:
    """
    Regularize a covariance matrix to ensure numerical stability.

    Args:
        cov_matrix: Input covariance matrix
        alpha: Regularization strength (added to diagonal)
        threshold: Condition number threshold

    Returns:
        Regularized covariance matrix.
    """
    n = cov_matrix.shape[0]
    regularized = cov_matrix + alpha * np.eye(n)

    if not is_condition_number_acceptable(regularized, threshold):
        # Increase regularization if still unstable
        alpha *= 10
        regularized = cov_matrix + alpha * np.eye(n)
        if not is_condition_number_acceptable(regularized, threshold):
            raise HighDimensionalInstabilityError(
                f"Matrix remains unstable after regularization. "
                f"Condition number exceeds {threshold}."
            )

    return regularized
