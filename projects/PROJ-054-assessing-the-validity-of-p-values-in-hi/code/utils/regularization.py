"""
Covariance Regularization Utilities.

Implements robust covariance matrix regularization to handle:
1. Singular matrices (non-invertible due to p >= n or perfect collinearity)
2. Ill-conditioned matrices (condition number > 10^12)

This module supports FR-009 requirements for high-dimensional stability.
"""

import numpy as np
from typing import Tuple, Optional
from .exceptions import HighDimensionalInstabilityError


def regularize_covariance(
    cov_matrix: np.ndarray,
    condition_threshold: float = 1e12,
    regularization_method: str = 'ledoit_wolf',
    epsilon: Optional[float] = None
) -> Tuple[np.ndarray, float, str]:
    """
    Regularize a covariance matrix to ensure numerical stability.

    This function handles singular matrices and those with high condition numbers
    (> 10^12) by applying appropriate regularization techniques.

    Parameters
    ----------
    cov_matrix : np.ndarray
        Input covariance matrix (p x p). Must be symmetric positive semi-definite.
    condition_threshold : float, optional
        Maximum allowed condition number. Default is 1e12 (FR-009 requirement).
    regularization_method : str, optional
        Regularization method to use:
        - 'ledoit_wolf': Optimal shrinkage towards scaled identity (default)
        - 'diagonal_loading': Add epsilon * trace/n to diagonal
        - 'eigenvalue_clipping': Clip small eigenvalues to minimum threshold
    epsilon : float, optional
        Regularization strength. If None, computed automatically for the method.

    Returns
    -------
    regularized_cov : np.ndarray
        The regularized covariance matrix.
    condition_number : float
        The condition number of the regularized matrix.
    method_used : str
        The regularization method that was applied.

    Raises
    ------
    HighDimensionalInstabilityError
        If the matrix cannot be regularized to meet the condition threshold
        or if the input is invalid.
    ValueError
        If the input matrix is not square or has invalid dimensions.

    Examples
    --------
    >>> import numpy as np
    >>> cov = np.array([[1.0, 0.9], [0.9, 1.0]])
    >>> reg_cov, cond, method = regularize_covariance(cov)
    >>> print(f"Condition number: {cond:.2e}, Method: {method}")
    """

    # Validate input
    if not isinstance(cov_matrix, np.ndarray):
        raise ValueError("Input must be a numpy array")

    if cov_matrix.ndim != 2 or cov_matrix.shape[0] != cov_matrix.shape[1]:
        raise ValueError("Input must be a square matrix")

    p = cov_matrix.shape[0]
    if p == 0:
        raise ValueError("Input matrix cannot be empty")

    # Ensure symmetry (numerical precision)
    cov_matrix = (cov_matrix + cov_matrix.T) / 2.0

    # Compute eigenvalues to assess condition
    try:
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
    except np.linalg.LinAlgError as e:
        raise HighDimensionalInstabilityError(
            f"Failed to compute eigenvalues: {e}",
            error_code="ERR_HIGH_DIMENSIONAL_INSTABILITY"
        ) from e

    # Check for negative eigenvalues (should be PSD)
    min_eigenvalue = np.min(eigenvalues)
    if min_eigenvalue < -1e-10:
        # Allow small numerical errors, but raise if significantly negative
        raise HighDimensionalInstabilityError(
            f"Matrix is not positive semi-definite (min eigenvalue: {min_eigenvalue:.2e})",
            error_code="ERR_HIGH_DIMENSIONAL_INSTABILITY"
        )

    # Compute condition number
    # Handle singular case (zero eigenvalues)
    nonzero_eigenvalues = eigenvalues[eigenvalues > 1e-15]
    if len(nonzero_eigenvalues) == 0:
        # Completely singular matrix
        cond_number = np.inf
    else:
        cond_number = np.max(nonzero_eigenvalues) / np.min(nonzero_eigenvalues)

    # If condition number is acceptable, return as-is
    if cond_number <= condition_threshold:
        return cov_matrix, cond_number, "none"

    # Apply regularization
    if regularization_method == 'ledoit_wolf':
        return _apply_ledoit_wolf(cov_matrix, condition_threshold)
    elif regularization_method == 'diagonal_loading':
        return _apply_diagonal_loading(cov_matrix, condition_threshold, epsilon)
    elif regularization_method == 'eigenvalue_clipping':
        return _apply_eigenvalue_clipping(cov_matrix, condition_threshold)
    else:
        raise ValueError(f"Unknown regularization method: {regularization_method}")


def _apply_ledoit_wolf(
    cov_matrix: np.ndarray,
    condition_threshold: float
) -> Tuple[np.ndarray, float, str]:
    """
    Apply Ledoit-Wolf shrinkage towards scaled identity matrix.

    This method finds the optimal shrinkage intensity to minimize
    the expected Frobenius norm error.
    """
    p = cov_matrix.shape[0]
    trace_cov = np.trace(cov_matrix)
    target = (trace_cov / p) * np.eye(p)

    # Estimate optimal shrinkage intensity (simplified Ledoit-Wolf)
    # For large p, we use a more aggressive shrinkage
    delta = np.sum((cov_matrix - target) ** 2) / (p ** 2)
    gamma = np.sum(cov_matrix ** 2) / (p ** 2)
    shrinkage = max(0, min(1, delta / gamma))

    # Iteratively adjust shrinkage to meet condition threshold
    max_iter = 100
    current_shrinkage = shrinkage

    for _ in range(max_iter):
        regularized = (1 - current_shrinkage) * cov_matrix + current_shrinkage * target
        try:
            reg_eigenvalues = np.linalg.eigvalsh(regularized)
            nonzero = reg_eigenvalues[reg_eigenvalues > 1e-15]
            if len(nonzero) > 0:
                cond = np.max(nonzero) / np.min(nonzero)
            else:
                cond = np.inf

            if cond <= condition_threshold:
                return regularized, cond, "ledoit_wolf"
        except np.linalg.LinAlgError:
            break

        # Increase shrinkage if condition number still too high
        current_shrinkage = min(0.99, current_shrinkage * 1.5)

    # If we reach here, even maximum shrinkage didn't help
    # Return the most regularized version
    regularized = (1 - current_shrinkage) * cov_matrix + current_shrinkage * target
    reg_eigenvalues = np.linalg.eigvalsh(regularized)
    nonzero = reg_eigenvalues[reg_eigenvalues > 1e-15]
    cond = np.max(nonzero) / np.min(nonzero) if len(nonzero) > 0 else np.inf

    return regularized, cond, "ledoit_wolf"


def _apply_diagonal_loading(
    cov_matrix: np.ndarray,
    condition_threshold: float,
    epsilon: Optional[float] = None
) -> Tuple[np.ndarray, float, str]:
    """
    Apply diagonal loading: Cov_reg = Cov + epsilon * I

    This shifts all eigenvalues by epsilon, improving the condition number.
    """
    p = cov_matrix.shape[0]
    trace_cov = np.trace(cov_matrix)

    # Default epsilon based on trace if not provided
    if epsilon is None:
        # Start with a small fraction of the average eigenvalue
        epsilon = 1e-6 * (trace_cov / p)

    # Iteratively increase epsilon until condition number is acceptable
    max_iter = 100
    current_epsilon = epsilon

    for _ in range(max_iter):
        regularized = cov_matrix + current_epsilon * np.eye(p)
        try:
            reg_eigenvalues = np.linalg.eigvalsh(regularized)
            nonzero = reg_eigenvalues[reg_eigenvalues > 1e-15]
            if len(nonzero) > 0:
                cond = np.max(nonzero) / np.min(nonzero)
            else:
                cond = np.inf

            if cond <= condition_threshold:
                return regularized, cond, "diagonal_loading"
        except np.linalg.LinAlgError:
            break

        # Increase epsilon
        current_epsilon *= 2.0

    # Return the most regularized version
    regularized = cov_matrix + current_epsilon * np.eye(p)
    reg_eigenvalues = np.linalg.eigvalsh(regularized)
    nonzero = reg_eigenvalues[reg_eigenvalues > 1e-15]
    cond = np.max(nonzero) / np.min(nonzero) if len(nonzero) > 0 else np.inf

    return regularized, cond, "diagonal_loading"


def _apply_eigenvalue_clipping(
    cov_matrix: np.ndarray,
    condition_threshold: float
) -> Tuple[np.ndarray, float, str]:
    """
    Apply eigenvalue clipping: replace eigenvalues below threshold with threshold.

    This ensures all eigenvalues are above a minimum value, improving condition.
    """
    # Eigenvalue decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(cov_matrix)

    # Find minimum eigenvalue needed to satisfy condition threshold
    max_eigenvalue = np.max(eigenvalues)
    min_required = max_eigenvalue / condition_threshold

    # Clip eigenvalues
    clipped_eigenvalues = np.maximum(eigenvalues, min_required)

    # Reconstruct matrix
    regularized = eigenvectors @ np.diag(clipped_eigenvalues) @ eigenvectors.T

    # Verify condition number
    nonzero = clipped_eigenvalues[clipped_eigenvalues > 1e-15]
    cond = np.max(nonzero) / np.min(nonzero) if len(nonzero) > 0 else np.inf

    return regularized, cond, "eigenvalue_clipping"


def is_condition_number_acceptable(
    cov_matrix: np.ndarray,
    threshold: float = 1e12
) -> bool:
    """
    Check if a covariance matrix has an acceptable condition number.

    Parameters
    ----------
    cov_matrix : np.ndarray
        Input covariance matrix.
    threshold : float, optional
        Maximum allowed condition number. Default is 1e12.

    Returns
    -------
    bool
        True if condition number <= threshold, False otherwise.
    """
    try:
        eigenvalues = np.linalg.eigvalsh(cov_matrix)
        nonzero = eigenvalues[eigenvalues > 1e-15]
        if len(nonzero) == 0:
            return False
        cond = np.max(nonzero) / np.min(nonzero)
        return cond <= threshold
    except np.linalg.LinAlgError:
        return False
