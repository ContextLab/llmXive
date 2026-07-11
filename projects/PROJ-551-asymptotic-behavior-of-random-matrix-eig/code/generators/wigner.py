"""
Wigner Matrix Generator.
Generates symmetric matrices with independent entries above the diagonal,
scaled by 1/sqrt(N) to converge to the semicircle law.

This implementation strictly adheres to the standard Wigner ensemble convention:
- Off-diagonal entries W_ij (i < j) are i.i.d. N(0, 1/N)
- Diagonal entries W_ii are i.i.d. N(0, 2/N)

This scaling ensures the eigenvalue distribution converges to the Wigner
semicircle law with support [-2, 2] as N -> infinity.
"""
import numpy as np
from typing import Optional

def generate_wigner_matrix(N: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate an N x N Wigner matrix.
    
    Parameters:
    -----------
    N : int
        Dimension of the matrix. Must be positive.
    seed : int, optional
        Random seed for reproducibility. If None, uses global random state.
        
    Returns:
    --------
    np.ndarray
        Symmetric matrix W of shape (N, N) where:
        - W_ij ~ N(0, 1/N) for i < j (and W_ji = W_ij)
        - W_ii ~ N(0, 2/N)
        
    Raises:
    -------
    ValueError
        If N is not a positive integer.
        
    Notes:
    ------
    The eigenvalues of this matrix, when N is large, will follow the
    Wigner semicircle distribution with radius 2. Outliers beyond |λ| > 2
    indicate the presence of significant perturbations (BBP transition).
    """
    if N <= 0:
        raise ValueError(f"Matrix dimension N must be positive, got {N}")
    
    # Initialize random number generator with optional seed
    rng = np.random.default_rng(seed)
    
    # Create empty matrix
    W = np.zeros((N, N), dtype=np.float64)
    
    # Generate upper triangular indices (excluding diagonal)
    # np.triu_indices returns arrays of row and column indices
    row_idx, col_idx = np.triu_indices(N, k=1)
    
    # Generate off-diagonal entries: N(0, 1/N)
    # Number of unique off-diagonal entries
    n_off_diag = len(row_idx)
    off_diag_values = rng.standard_normal(n_off_diag) / np.sqrt(N)
    
    # Fill upper triangle
    W[row_idx, col_idx] = off_diag_values
    
    # Make symmetric by copying upper to lower triangle
    W[col_idx, row_idx] = off_diag_values
    
    # Generate diagonal entries: N(0, 2/N)
    # Diagonal variance is twice the off-diagonal variance
    diag_values = rng.standard_normal(N) * np.sqrt(2.0 / N)
    np.fill_diagonal(W, diag_values)
    
    # Verify symmetry (sanity check, can be removed in production)
    # assert np.allclose(W, W.T), "Generated matrix is not symmetric"
    
    return W

# Legacy function name kept for backward compatibility if needed
def create_wigner_matrix(N: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Alias for generate_wigner_matrix for compatibility.
    """
    return generate_wigner_matrix(N, seed)