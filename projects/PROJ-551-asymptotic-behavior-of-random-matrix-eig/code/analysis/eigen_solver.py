"""
Eigenvalue solver utilities for random matrix analysis.

Provides iterative solvers for large sparse matrices and validation logic
to distinguish true spectral outliers from numerical artifacts.
"""

import numpy as np
from scipy.sparse.linalg import eigsh, LinearOperator
from scipy import sparse
import warnings

# Theoretical edge of the semicircle law for Wigner matrices
# (scaled by 1/sqrt(N))
SEMICIRCLE_EDGE = 2.0

# Strict numerical tolerance for validation
VALIDATION_TOLERANCE = 1e-10


def compute_top_eigenvalues(
    matrix: np.ndarray,
    k: int = 10,
    which: str = 'LM',
    tol: float = 1e-10
) -> np.ndarray:
    """
    Compute the top k eigenvalues of a symmetric matrix using ARPACK.

    Args:
        matrix: Input symmetric matrix (dense or sparse).
        k: Number of eigenvalues to compute.
        which: Which eigenvalues to compute ('LM' for largest magnitude,
               'LA' for largest algebraic).
        tol: Convergence tolerance for the iterative solver.

    Returns:
        Array of k eigenvalues sorted in descending order.

    Raises:
        RuntimeError: If the solver fails to converge.
    """
    n = matrix.shape[0]
    if k >= n:
        raise ValueError(f"k ({k}) must be less than matrix dimension ({n})")

    # Ensure matrix is symmetric for eigsh
    # We assume input is symmetric, but enforce it for numerical stability
    if sparse.issparse(matrix):
        # For sparse, we trust the user provided a symmetric structure
        A = matrix
    else:
        # Make symmetric explicitly
        A = (matrix + matrix.T) / 2.0
        if not sparse.issparse(A):
            A = sparse.csr_matrix(A)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            eigenvalues, _ = eigsh(A, k=k, which=which, tol=tol)
    except Exception as e:
        raise RuntimeError(f"Eigenvalue solver failed to converge: {e}")

    # Sort in descending order
    eigenvalues = np.sort(eigenvalues)[::-1]
    return eigenvalues


def validate_eigenvalues(
    eigenvalues: np.ndarray,
    edge: float = SEMICIRCLE_EDGE,
    tolerance: float = VALIDATION_TOLERANCE
) -> dict:
    """
    Validate eigenvalues to distinguish outliers from numerical artifacts.

    This function implements a pure validation logic that checks if an eigenvalue
    is a true outlier (significantly beyond the theoretical semicircle edge)
    versus a numerical artifact (floating point noise near the edge).

    Args:
        eigenvalues: Array of eigenvalues to validate (typically sorted descending).
        edge: Theoretical edge of the semicircle law (default 2.0).
        tolerance: Strict tolerance for distinguishing outliers (default 1e-10).

    Returns:
        A dictionary containing:
            - 'is_outlier': bool, True if the top eigenvalue is a confirmed outlier
            - 'max_eigenvalue': float, the largest eigenvalue
            - 'distance_from_edge': float, how far the max eigenvalue is from the edge
            - 'validation_passed': bool, True if the distance > tolerance
            - 'reason': str, explanation of the validation result

    The validation logic:
        - An eigenvalue is considered a TRUE outlier if:
            eigenvalue > edge + tolerance
        - An eigenvalue is considered a NUMERICAL ARTIFACT if:
            |eigenvalue - edge| <= tolerance
        - The function returns binary pass/fail for the "outlier" hypothesis.
    """
    if eigenvalues.size == 0:
        return {
            'is_outlier': False,
            'max_eigenvalue': None,
            'distance_from_edge': None,
            'validation_passed': False,
            'reason': 'No eigenvalues provided'
        }

    max_eig = eigenvalues[0]
    distance = max_eig - edge

    # Strict validation: must exceed edge by more than the tolerance
    # to be considered a real outlier, not a numerical artifact.
    if distance > tolerance:
        return {
            'is_outlier': True,
            'max_eigenvalue': float(max_eig),
            'distance_from_edge': float(distance),
            'validation_passed': True,
            'reason': f'Eigenvalue {max_eig:.10f} exceeds edge {edge} by {distance:.10e} > {tolerance}'
        }
    else:
        return {
            'is_outlier': False,
            'max_eigenvalue': float(max_eig),
            'distance_from_edge': float(distance),
            'validation_passed': False,
            'reason': f'Eigenvalue {max_eig:.10f} is within tolerance {tolerance} of edge {edge} (distance={distance:.10e}) - likely numerical artifact'
        }

# The following functions are placeholders for the iterative solver wrapper
# mentioned in T007a. They are included here to maintain API consistency
# but the actual implementation of the wrapper logic is in T007a.
# This file is extended by T007b to add the validation logic.

def _create_linear_operator(matrix: np.ndarray) -> LinearOperator:
    """
    Create a LinearOperator from a dense matrix for use with eigsh.
    """
    n = matrix.shape[0]
    def matvec(v):
        return matrix @ v
    return LinearOperator((n, n), matvec=matvec, dtype=matrix.dtype)

def compute_top_eigenvalues_iterative(
    matrix: np.ndarray,
    k: int = 10,
    tol: float = 1e-10
) -> np.ndarray:
    """
    Wrapper for iterative eigenvalue computation using LinearOperator.
    This is the function referenced in T007a.
    """
    if sparse.issparse(matrix):
        A = matrix
    else:
        A = (matrix + matrix.T) / 2.0
        A = sparse.csr_matrix(A)

    try:
        eigenvalues, _ = eigsh(A, k=k, which='LA', tol=tol)
    except Exception as e:
        raise RuntimeError(f"Iterative solver failed: {e}")

    return np.sort(eigenvalues)[::-1]