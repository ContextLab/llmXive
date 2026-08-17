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
import warnings

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
        
    Raises:
    -------
    RuntimeError
        If the iterative solver fails to converge and fallback is not applicable.
    """
    N = matrix.shape[0]
    
    # Fallback to dense solver if asking for too many eigenvalues or matrix is small
    # ARPACK requires k < N-1 to converge reliably
    if k >= N - 1:
        warnings.warn(f"Matrix size N={N} is too small for k={k} eigenvalues in ARPACK. Falling back to dense solver.")
        evals_full = np.linalg.eigvalsh(matrix)
        return np.sort(evals_full)[::-1][:k]

    # Convert to sparse format if input is dense to save memory
    if not sparse.issparse(matrix):
        # Ensure symmetry for dense input (ARPACK expects symmetric/Hermitian)
        # We take the average of A and A.T to ensure numerical symmetry
        matrix_sym = (matrix + matrix.T) / 2.0
        mat_sparse = sparse.csr_matrix(matrix_sym)
    else:
        mat_sparse = matrix

    try:
        # Use eigsh with strict tolerance to ensure accuracy
        # ARPACK requires k < N-1
        # maxiter can be increased if convergence is slow, but default is usually sufficient
        evals, evecs = eigsh(mat_sparse, k=k, which=which, tol=tol)
        # Sort in descending order (LA returns unsorted)
        return np.sort(evals)[::-1]
    except Exception as e:
        # Handle non-convergence or other ARPACK errors
        error_msg = str(e)
        if "No convergent values" in error_msg or "did not converge" in error_msg.lower():
            raise RuntimeError(f"eigsh failed to converge for N={N}, k={k}, tol={tol}. "
                               "The matrix may not be symmetric or the tolerance is too strict for the spectrum gap.") from e
        else:
            # For other errors (e.g., invalid input), attempt fallback only if safe
            if N < 500:
                warnings.warn(f"eigsh failed (k={k}, N={N}): {e}. Falling back to dense solver.")
                evals_full = np.linalg.eigvalsh(matrix)
                return np.sort(evals_full)[::-1][:k]
            else:
                raise RuntimeError(f"eigsh failed with unexpected error: {e}. "
                                   "Falling back to dense solver disabled for large matrices (N >= 500).") from e

def validate_eigenvalues(eigenvalues: np.ndarray, N: int, perturbation_norm: Optional[float] = None, tol: float = 1e-10) -> dict:
    """
    Validate eigenvalues against the theoretical semicircle edge (±2.0).
    
    This validation is STRICT: it checks if eigenvalues exceed 2.0 + tolerance.
    It explicitly uses the BBP threshold as the TARGET for empirical verification,
    NOT as a constraint to avoid. If a perturbation_norm is provided, it calculates
    the theoretical BBP threshold (theta + 1/theta) and compares the max eigenvalue
    against it, but the primary "outlier" flag is based on the semicircle edge.
    
    Parameters:
    -----------
    eigenvalues : np.ndarray
        Array of computed eigenvalues (sorted descending).
    N : int
        Dimension of the original matrix (used for theoretical context if needed).
    perturbation_norm : float, optional
        The norm (theta) of the rank-1 perturbation. If provided, the BBP
        threshold is calculated for comparison.
    tol : float
        Numerical tolerance for outlier detection (default 1e-10).
        
    Returns:
    --------
    dict
        Dictionary containing:
        - max_eigenvalue: The largest eigenvalue found.
        - theoretical_edge: The semicircle law edge (2.0).
        - bbp_threshold: The predicted BBP threshold (theta + 1/theta) if perturbation_norm provided, else None.
        - is_outlier_present: Boolean indicating if any eigenvalue > 2.0 + tol.
        - outliers: List of eigenvalues strictly greater than 2.0 + tol.
        - bbp_deviation: Difference between max_eigenvalue and bbp_threshold (if applicable).
    """
    # Theoretical edge for Wigner matrices scaled by 1/sqrt(N) is exactly 2.0
    theoretical_edge = 2.0
    
    # Strict threshold: must exceed theoretical edge by at least tolerance
    threshold = theoretical_edge + tol
    
    outliers = []
    for ev in eigenvalues:
        if ev > threshold:
            outliers.append(float(ev))
    
    result = {
        "max_eigenvalue": float(eigenvalues[0]) if len(eigenvalues) > 0 else None,
        "theoretical_edge": theoretical_edge,
        "threshold_used": threshold,
        "tolerance": tol,
        "is_outlier_present": len(outliers) > 0,
        "outliers": outliers,
        "num_eigenvalues_checked": len(eigenvalues),
        "bbp_threshold": None,
        "bbp_deviation": None
    }
    
    if perturbation_norm is not None:
        theta = perturbation_norm
        # BBP prediction: lambda_out = theta + 1/theta for theta > 1
        # This is the target we are empirically verifying
        bbp_pred = theta + 1.0 / theta
        result["bbp_threshold"] = bbp_pred
        
        if result["max_eigenvalue"] is not None:
            result["bbp_deviation"] = result["max_eigenvalue"] - bbp_pred
    
    return result