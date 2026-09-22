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


def compute_top_eigenvalues_iterative(matrix: np.ndarray, k: int = 1, tol: float = 1e-6) -> np.ndarray:
    """
    Compute top eigenvalues using an iterative solver with explicit tolerance.

    Args:
        matrix: Symmetric matrix.
        k: Number of eigenvalues.
        tol: Convergence tolerance.

    Returns:
        Array of k eigenvalues.
    """
    if not sparse.issparse(matrix):
        matrix = sparse.csr_matrix(matrix)

    # Ensure symmetry
    matrix = (matrix + matrix.T) / 2

    try:
        eigenvalues, _ = eigsh(matrix, k=k, which='LA', tol=tol)
        return np.sort(eigenvalues)[::-1]
    except Exception as e:
        warnings.warn(f"Iterative solver failed: {e}. Using dense fallback.")
        return np.linalg.eigvalsh(matrix.toarray())[:k][::-1]


def validate_eigenvalues(eigenvalues: np.ndarray, tolerance: float = None) -> bool:
    """
    Validate eigenvalues against the theoretical Wigner semicircle edge.

    The theoretical edge of the semicircle law for a standard Wigner matrix
    (scaled by 1/sqrt(N)) is at ±2.0. This function checks if the largest
    eigenvalue exceeds the edge by a strictly configurable tolerance.

    Args:
        eigenvalues: Array of eigenvalues (sorted descending is preferred,
                     but not required).
        tolerance: Optional tolerance override. If None, loaded from config.py.
                   Defaults to a sufficiently small value (e.g., 1e-6) if not
                   found in config.

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
    return max_eigenvalue > (theoretical_edge + tolerance)