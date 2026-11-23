"""
Eigenvalue solvers and validation logic for Random Matrix Theory simulations.

This module provides iterative solvers for large sparse matrices and validation
functions to distinguish physical outliers from numerical artifacts.
"""

import numpy as np
from scipy.sparse.linalg import eigsh, LinearOperator
from scipy import sparse
import warnings

from utils.config import get_outlier_tolerance


def compute_top_eigenvalues(matrix: np.ndarray, k: int = 1, which: str = 'LM') -> np.ndarray:
    """
    Compute the top k eigenvalues of a symmetric matrix.

    Args:
        matrix: Symmetric matrix (dense or sparse).
        k: Number of eigenvalues to compute.
        which: Which part of the spectrum to compute ('LM' for largest magnitude,
               'LA' for largest algebraic, etc.).

    Returns:
        Array of k eigenvalues, sorted in descending order.
    """
    if sparse.issparse(matrix):
        # Ensure the matrix is symmetric for eigsh
        matrix = sparse.csr_matrix((matrix + matrix.T) / 2)
        try:
            eigenvalues, _ = eigsh(matrix, k=k, which=which)
        except Exception as e:
            warnings.warn(f"eigsh failed: {e}. Falling back to dense solver.")
            eigenvalues = np.linalg.eigvalsh(matrix.toarray())
    else:
        # Ensure the matrix is symmetric
        matrix = (matrix + matrix.T) / 2
        eigenvalues = np.linalg.eigvalsh(matrix)

    # Sort in descending order
    eigenvalues = np.sort(eigenvalues)[::-1]
    return eigenvalues[:k]


def compute_top_eigenvalues_iterative(matrix: np.ndarray, k: int = 1, tol: float = None) -> np.ndarray:
    """
    Compute top eigenvalues using an iterative solver with explicit tolerance.

    This function wraps scipy.sparse.linalg.eigsh, loading the convergence tolerance
    from the project configuration (utils.config) if not explicitly provided.
    It ensures convergence criteria are met and handles non-convergence gracefully
    by falling back to a dense solver with a warning.

    Args:
        matrix: Symmetric matrix (dense or sparse).
        k: Number of eigenvalues to compute.
        tol: Convergence tolerance. If None, loads `OUTLIER_TOLERANCE` from config.py.

    Returns:
        Array of k eigenvalues, sorted in descending order.

    Raises:
        ValueError: If the matrix is not square or k is invalid.
    """
    if tol is None:
        tol = get_outlier_tolerance()

    if not isinstance(matrix, np.ndarray):
        if sparse.issparse(matrix):
            matrix = matrix.toarray()
        else:
            raise TypeError("Input matrix must be a numpy array or scipy sparse matrix.")

    if matrix.shape[0] != matrix.shape[1]:
        raise ValueError("Matrix must be square.")
    
    if k <= 0 or k >= matrix.shape[0]:
        # If k is too large for iterative, fallback to dense immediately
        # or adjust k. Here we fallback to dense for safety if k is too large.
        warnings.warn(f"k={k} is too large for iterative solver on N={matrix.shape[0]}. Falling back to dense.")
        matrix = (matrix + matrix.T) / 2
        return np.sort(np.linalg.eigvalsh(matrix))[::-1][:k]

    # Convert to sparse if dense
    if not sparse.issparse(matrix):
        # Ensure symmetry before converting to sparse to avoid numerical drift
        matrix = (matrix + matrix.T) / 2
        matrix_sparse = sparse.csr_matrix(matrix)
    else:
        matrix_sparse = matrix
        # Ensure symmetry
        matrix_sparse = (matrix_sparse + matrix_sparse.T) / 2

    try:
        # 'LA' (Largest Algebraic) is appropriate for finding the top edge of the spectrum
        eigenvalues, _ = eigsh(matrix_sparse, k=k, which='LA', tol=tol)
        
        # Sort in descending order
        eigenvalues = np.sort(eigenvalues)[::-1]
        return eigenvalues[:k]
    except Exception as e:
        # Handle non-convergence or numerical issues gracefully
        warnings.warn(f"Iterative solver (eigsh) failed with tol={tol}: {e}. Falling back to dense solver.")
        # Fallback to dense solver
        matrix_dense = matrix_sparse.toarray() if sparse.issparse(matrix_sparse) else matrix
        matrix_dense = (matrix_dense + matrix_dense.T) / 2
        full_eigenvalues = np.linalg.eigvalsh(matrix_dense)
        return np.sort(full_eigenvalues)[::-1][:k]


def validate_eigenvalues(eigenvalues: np.ndarray, tolerance: float = None) -> bool:
    """
    Validate eigenvalues against the theoretical Wigner semicircle edge.

    The theoretical edge of the semicircle law for a standard Wigner matrix
    (scaled by 1/sqrt(N)) is at ±2.0. This function checks if the largest
    eigenvalue exceeds the edge by a strictly configurable tolerance.

    This function implements the pure validation logic required by T007b:
    it distinguishes outliers from numerical artifacts using a strict tolerance
    loaded from config.py (default 1e-10) relative to the theoretical semicircle
    edge (±2.0).

    Args:
        eigenvalues: Array of eigenvalues (sorted descending is preferred,
                     but not required).
        tolerance: Optional tolerance override. If None, loaded from config.py.
                   Defaults to the value defined in config.py (typically 1e-10).

    Returns:
        True if the largest eigenvalue is strictly greater than (2.0 + tolerance),
        indicating a potential physical outlier. False otherwise.

    Note:
        This is a pure validation function. It does not execute simulations or
        generate data. It strictly compares the observed maximum eigenvalue
        against the theoretical boundary + tolerance.
    """
    if tolerance is None:
        tolerance = get_outlier_tolerance()

    if not isinstance(tolerance, (int, float)):
        raise ValueError("Tolerance must be a numeric value.")

    if not isinstance(eigenvalues, np.ndarray):
        eigenvalues = np.array(eigenvalues)

    if eigenvalues.size == 0:
        return False

    max_eigenvalue = np.max(eigenvalues)
    theoretical_edge = 2.0

    # Strict check: outlier if max_eigenvalue > theoretical_edge + tolerance
    # This implements the spec validation criteria: strict tolerance relative to ±2.0 edge.
    return max_eigenvalue > (theoretical_edge + tolerance)