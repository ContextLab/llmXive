"""
Iterative Eigenvalue Solver.
Uses ARPACK (scipy.sparse.linalg.eigsh) to compute top eigenvalues
of large symmetric matrices.

This module provides strict validation against the theoretical semicircle
edge (±2.0) to distinguish true outliers from numerical artifacts.
"""
import numpy as np
from scipy.sparse.linalg import eigsh, LinearOperator
from scipy import sparse

def compute_top_eigenvalues(matrix: np.ndarray, k: int = 10, which: str = 'LA', tol: float = 1e-10) -> np.ndarray:
    """
    Compute the top k eigenvalues of a symmetric matrix using an iterative solver.
    
    Parameters:
    -----------
    matrix : np.ndarray
        Symmetric matrix (dense or sparse).
    k : int
        Number of eigenvalues to compute.
    which : str
        Which part of spectrum ('LA' for largest algebraic).
    tol : float
        Tolerance for the iterative solver (default 1e-10).
        
    Returns:
    --------
    np.ndarray
        Array of k eigenvalues, sorted in descending order.
    """
    N = matrix.shape[0]
    if k >= N:
        # Fallback to dense solver if asking for too many eigenvalues
        # This avoids ARPACK convergence issues for small matrices
        return np.linalg.eigvalsh(matrix)[::-1][:k]

    # Convert to sparse format if input is dense to save memory
    if not sparse.issparse(matrix):
        mat_sparse = sparse.csr_matrix(matrix)
    else:
        mat_sparse = matrix

    try:
        # Use eigsh with strict tolerance to ensure accuracy
        # ARPACK requires k < N-1
        evals, evecs = eigsh(mat_sparse, k=k, which=which, tol=tol)
        # Sort in descending order (LA returns unsorted)
        return np.sort(evals)[::-1]
    except Exception as e:
        # Fallback for small matrices or convergence issues
        # Log the warning but proceed with dense calculation
        import warnings
        warnings.warn(f"eigsh failed (k={k}, N={N}): {e}. Falling back to dense solver.")
        evals_full = np.linalg.eigvalsh(matrix)
        return np.sort(evals_full)[::-1][:k]

def validate_eigenvalues(eigenvalues: np.ndarray, N: int, tol: float = 1e-10) -> dict:
    """
    Validate eigenvalues against the theoretical semicircle edge (±2.0).
    
    This validation is STRICT: it checks if eigenvalues exceed 2.0 + tolerance.
    It does NOT validate against the predicted BBP threshold (1 + 1/theta) to
    avoid circular reasoning where the theory being tested is used for validation.
    
    Parameters:
    -----------
    eigenvalues : np.ndarray
        Array of computed eigenvalues (sorted descending).
    N : int
        Dimension of the original matrix (used for theoretical context if needed).
    tol : float
        Numerical tolerance for outlier detection (default 1e-10).
        
    Returns:
    --------
    dict
        Dictionary containing:
        - max_eigenvalue: The largest eigenvalue found.
        - theoretical_edge: The semicircle law edge (2.0).
        - is_outlier_present: Boolean indicating if any eigenvalue > 2.0 + tol.
        - outliers: List of eigenvalues strictly greater than 2.0 + tol.
    """
    # Theoretical edge for Wigner matrices scaled by 1/sqrt(N) is exactly 2.0
    theoretical_edge = 2.0
    
    # Strict threshold: must exceed theoretical edge by at least tolerance
    threshold = theoretical_edge + tol
    
    outliers = []
    for ev in eigenvalues:
        if ev > threshold:
            outliers.append(float(ev))
    
    return {
        "max_eigenvalue": float(eigenvalues[0]) if len(eigenvalues) > 0 else None,
        "theoretical_edge": theoretical_edge,
        "threshold_used": threshold,
        "tolerance": tol,
        "is_outlier_present": len(outliers) > 0,
        "outliers": outliers,
        "num_eigenvalues_checked": len(eigenvalues)
    }