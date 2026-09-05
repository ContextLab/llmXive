"""
Wigner Matrix Generator.

Generates symmetric random matrices (Wigner matrices) where:
- Diagonal elements are standard normal N(0, 1)
- Off-diagonal elements are standard normal N(0, 1) / sqrt(2)
- The matrix is scaled by 1/sqrt(N) to ensure the eigenvalue spectrum
  converges to the semicircle law [-2, 2] as N -> infinity.
"""
import numpy as np
from typing import Optional

def generate_wigner_matrix(n: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate a Wigner matrix of size n x n.

    Args:
        n: Dimension of the matrix.
        seed: Random seed for reproducibility.

    Returns:
        A symmetric numpy array of shape (n, n).
    """
    if seed is not None:
        np.random.seed(seed)

    # Generate upper triangular part including diagonal
    # Diagonal: N(0, 1)
    # Off-diagonal: N(0, 1)
    upper = np.random.normal(0, 1, size=(n, n))
    
    # Make it symmetric: A = (A + A.T) / sqrt(2) for off-diagonals
    # But we need to handle diagonal carefully.
    # Standard Wigner construction:
    # A_ij ~ N(0, 1) for i <= j
    # A_ji = A_ij
    # Then scale by 1/sqrt(N)
    
    # Create symmetric matrix from upper triangle
    # Set lower triangle to upper triangle
    matrix = np.triu(upper)
    matrix = matrix + matrix.T
    # Subtract diagonal because we added it twice
    np.fill_diagonal(matrix, np.diag(matrix) / 2.0)
    
    # Scale by 1/sqrt(N)
    matrix /= np.sqrt(n)
    
    return matrix

def create_wigner_matrix(n: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Alias for generate_wigner_matrix for compatibility.
    """
    return generate_wigner_matrix(n, seed)
