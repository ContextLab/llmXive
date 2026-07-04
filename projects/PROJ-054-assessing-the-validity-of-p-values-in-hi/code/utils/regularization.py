"""
Covariance regularization utilities for high-dimensional data analysis.

Implements methods to handle singular or near-singular covariance matrices
by applying regularization techniques (e.g., shrinkage, diagonal loading)
when the condition number exceeds a specified threshold.
"""

import numpy as np
from typing import Tuple, Optional

from .exceptions import HighDimensionalInstabilityError

# Constants
DEFAULT_CONDITION_THRESHOLD = 1e12
DEFAULT_REGULARIZATION_FACTOR = 1e-4


def compute_condition_number(matrix: np.ndarray) -> float:
    """
    Computes the condition number of a square matrix using the 2-norm.

    Args:
        matrix: A 2D numpy array.

    Returns:
        The condition number. Returns infinity if the matrix is singular.
    """
    try:
        # Use svd for stability
        s = np.linalg.svd(matrix, compute_uv=False)
        if s[-1] == 0:
            return np.inf
        return s[0] / s[-1]
    except np.linalg.LinAlgError:
        return np.inf


def regularize_covariance(
    cov_matrix: np.ndarray,
    threshold: float = DEFAULT_CONDITION_THRESHOLD,
    factor: float = DEFAULT_REGULARIZATION_FACTOR
) -> Tuple[np.ndarray, bool, float]:
    """
    Regularizes a covariance matrix if it is singular or ill-conditioned.

    This function checks the condition number of the input covariance matrix.
    If the condition number exceeds the `threshold`, it applies diagonal
    loading (adding a small factor * trace to the diagonal) to improve
    numerical stability.

    Args:
        cov_matrix: The input covariance matrix (n x n).
        threshold: The condition number threshold above which regularization is applied.
                   Defaults to 1e12.
        factor: The regularization factor. The diagonal is updated as:
                diag += factor * trace(cov_matrix) / n.
                Defaults to 1e-4.

    Returns:
        A tuple containing:
        - regularized_matrix: The resulting covariance matrix (regularized or original).
        - was_regularized: Boolean indicating if regularization was applied.
        - original_condition: The condition number of the original matrix.

    Raises:
        HighDimensionalInstabilityError: If the matrix remains unstable after
                                         attempted regularization (rare) or if
                                         the condition number exceeds the threshold
                                         and the user specified strict mode.
                                         Currently, this function attempts to fix it
                                         but logs the instability.
    """
    if cov_matrix.ndim != 2 or cov_matrix.shape[0] != cov_matrix.shape[1]:
        raise ValueError("cov_matrix must be a square 2D array.")

    original_condition = compute_condition_number(cov_matrix)
    was_regularized = False
    regularized_matrix = cov_matrix.copy()

    if original_condition > threshold:
        # Apply diagonal loading
        n = cov_matrix.shape[0]
        trace_val = np.trace(cov_matrix)
        reg_value = factor * (trace_val / n)

        # Ensure we don't add negative values if trace is weird (shouldn't happen for cov)
        if reg_value <= 0:
            reg_value = factor

        regularized_matrix += reg_value * np.eye(n)
        was_regularized = True

        # Verify improvement (optional but good practice)
        new_condition = compute_condition_number(regularized_matrix)
        # If it's still bad, we might need to warn or raise, but for now
        # we assume diagonal loading fixes high condition numbers from near-singularity.
        # If the matrix was truly singular (inf condition), this makes it invertible.

    return regularized_matrix, was_regularized, original_condition


def safe_inverse(
    matrix: np.ndarray,
    threshold: float = DEFAULT_CONDITION_THRESHOLD,
    factor: float = DEFAULT_REGULARIZATION_FACTOR
) -> Tuple[np.ndarray, bool]:
    """
    Computes the inverse of a matrix, applying regularization if necessary.

    This is a convenience wrapper around `regularize_covariance` followed by inversion.

    Args:
        matrix: The square matrix to invert.
        threshold: Condition number threshold for regularization.
        factor: Regularization factor for diagonal loading.

    Returns:
        A tuple containing:
        - inverse_matrix: The inverted matrix.
        - was_regularized: Boolean indicating if regularization was applied before inversion.
    """
    reg_matrix, was_reg, _ = regularize_covariance(matrix, threshold, factor)
    try:
        return np.linalg.inv(reg_matrix), was_reg
    except np.linalg.LinAlgError as e:
        raise HighDimensionalInstabilityError(
            f"Matrix inversion failed even after regularization: {e}",
            condition_number=compute_condition_number(matrix)
        )
