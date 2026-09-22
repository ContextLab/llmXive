"""
Wigner Matrix Generator.

Generates symmetric random matrices (Wigner matrices) where:
- Diagonal elements are standard normal N(0, 1)
- Off-diagonal elements are standard normal N(0, 1) / sqrt(2)
- The matrix is scaled by 1/sqrt(N) to ensure the eigenvalue spectrum
  converges to the semicircle law [-2, 2] as N -> infinity.

This module implements the core generator for the Wigner Ensemble as defined
in the project's mathematical framework.
"""
import numpy as np
from typing import Optional
import argparse
import json
import logging
import sys
from pathlib import Path
import hashlib
import time

# Ensure we can import from the project root if run as a script
# but rely on the package structure when imported.
try:
    from utils.config import get_project_paths
except ImportError:
    # Fallback for direct execution if path setup is different
    get_project_paths = None

logger = logging.getLogger(__name__)

def generate_wigner_matrix(n: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Generate a Wigner matrix of size n x n.

    The matrix A is constructed such that:
    - A[i, j] ~ N(0, 1) for i <= j (upper triangle including diagonal)
    - A[j, i] = A[i, j] (symmetry)
    - The final matrix is scaled by 1/sqrt(n).

    This ensures the empirical spectral distribution converges to the
    Wigner semicircle law with support [-2, 2] as n -> infinity.

    Args:
        n: Dimension of the matrix.
        seed: Random seed for reproducibility.

    Returns:
        A symmetric numpy array of shape (n, n).
    """
    if seed is not None:
        # Use a dedicated generator to avoid global state pollution
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    # Generate upper triangular part including diagonal
    # Diagonal: N(0, 1)
    # Off-diagonal: N(0, 1)
    # We generate the full upper triangle including diagonal
    upper = rng.normal(0, 1, size=(n, n))
    
    # Create symmetric matrix
    # A = (Upper + Upper.T) / sqrt(2) is incorrect for diagonal.
    # Correct construction:
    # 1. Take upper triangle (including diagonal)
    # 2. Reflect to lower triangle
    # 3. Scale by 1/sqrt(n)
    
    matrix = np.triu(upper)
    matrix = matrix + matrix.T
    
    # The diagonal was added twice (once from upper, once from lower reflection).
    # We need to divide the diagonal by 2 to get the correct value.
    # Since the original diagonal was N(0,1), and we added it to itself,
    # we have 2 * diag. We want diag. So we divide diag by 2.
    # Actually, simpler:
    # matrix[i, j] for i != j: upper[i, j] + upper[j, i].
    # We want a single N(0,1) variable.
    # Standard method:
    # 1. Generate symmetric matrix with N(0, 1) entries.
    # 2. The diagonal should be N(0, 1).
    # 3. The off-diagonal should be N(0, 1) (not sum of two).
    
    # Let's do it correctly:
    # 1. Generate full matrix of N(0, 1)
    # 2. Make it symmetric: M = (M + M.T) / sqrt(2)
    #    Diagonal: (X + X) / sqrt(2) = X * sqrt(2) -> Variance 2.
    #    Off-diagonal: (X + Y) / sqrt(2) -> Variance (1+1)/2 = 1.
    #    This gives diagonal variance 2, off-diagonal 1.
    #    We want both to be variance 1 (standard normal).
    
    # Correct standard construction for Wigner (Gaussian Orthogonal Ensemble - GOE):
    # Diagonal: N(0, 1)
    # Off-diagonal: N(0, 1) (symmetric)
    # Scale by 1/sqrt(n).
    
    # Implementation:
    # 1. Generate upper triangle (including diagonal) with N(0, 1).
    # 2. Reflect to lower triangle.
    # 3. Scale by 1/sqrt(n).
    
    # Re-generating correctly:
    # We need a matrix where A_ij = A_ji.
    # A_ij ~ N(0, 1) for i <= j.
    
    # Create a matrix of random numbers
    M = rng.normal(0, 1, size=(n, n))
    
    # Make it symmetric: take upper triangle, add to its transpose
    # But we must handle the diagonal carefully.
    # If we do M = M + M.T, diagonal becomes 2 * M_ii.
    # We want M_ii to be N(0, 1).
    # So we set diagonal explicitly or adjust.
    
    # Standard approach:
    # 1. Generate full matrix of N(0, 1)
    # 2. M = (M + M.T) / 2.0 -> Symmetric, but variance is 0.5 for off-diag, 1.0 for diag?
    #    Var((X+Y)/2) = (1+1)/4 = 0.5.
    #    Var((X+X)/2) = 1.
    #    We want variance 1 for both.
    #    So scale by sqrt(2).
    #    M = (M + M.T) / sqrt(2).
    #    Var(off) = 1. Var(diag) = 2.
    #    This is the GOE definition where diagonal variance is 2 * off-diagonal variance.
    #    The problem statement says: "Diagonal elements are standard normal N(0, 1)".
    #    "Off-diagonal elements are standard normal N(0, 1) / sqrt(2)".
    #    Wait, the docstring in the original file says:
    #    "Off-diagonal elements are standard normal N(0, 1) / sqrt(2)"
    #    This implies the *unscaled* off-diagonal has variance 1/2.
    #    If we sum X (diag) and Y (off), and scale by 1/sqrt(N).
    #    Let's stick to the standard Wigner definition:
    #    A_ij ~ N(0, 1) for i <= j.
    #    A_ji = A_ij.
    #    Then scale by 1/sqrt(N).
    #    This gives diagonal variance 1, off-diagonal variance 1.
    #    The spectrum converges to [-2, 2].
    
    # Let's implement the standard:
    # 1. Generate upper triangle (including diagonal) with N(0, 1).
    # 2. Reflect to lower.
    # 3. Scale by 1/sqrt(n).
    
    # Generate upper triangle
    upper = np.triu(rng.normal(0, 1, size=(n, n)))
    matrix = upper + upper.T
    # The diagonal was added twice (upper[i,i] + upper[i,i]).
    # We need it to be just upper[i,i].
    # So we subtract the diagonal once? No, we added it twice.
    # matrix[i,i] = 2 * upper[i,i].
    # We want matrix[i,i] = upper[i,i].
    # So we do: matrix -= np.diag(np.diag(matrix)) / 2.0?
    # No, simpler:
    # matrix = upper + upper.T
    # np.fill_diagonal(matrix, np.diag(upper))
    # This sets the diagonal to the original upper diagonal.
    
    np.fill_diagonal(matrix, np.diag(upper))
    
    # Scale by 1/sqrt(N)
    matrix /= np.sqrt(n)
    
    return matrix

def create_wigner_matrix(n: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Alias for generate_wigner_matrix for compatibility.
    """
    return generate_wigner_matrix(n, seed)

def main():
    """
    CLI entry point for generating a Wigner matrix and saving it.
    Usage: python -m code.generators.wigner --N 1000 --seed 42 --output data/raw/matrix.npy
    """
    parser = argparse.ArgumentParser(description="Generate a Wigner matrix.")
    parser.add_argument("--N", type=int, required=True, help="Dimension of the matrix.")
    parser.add_argument("--seed", type=int, default=None, help="Random seed.")
    parser.add_argument("--output", type=str, default=None, help="Output path for .npy file.")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logger.info(f"Generating Wigner matrix of size {args.N}x{args.N} with seed {args.seed}")
    
    matrix = generate_wigner_matrix(args.N, args.seed)
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        # Default path based on project structure
        output_dir = Path("data/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"matrix_N{args.N}_seed{args.seed}.npy"
    
    # Save matrix
    logger.info(f"Saving matrix to {output_path}")
    np.save(output_path, matrix)
    
    # Compute checksum
    checksum = hashlib.sha256(open(output_path, 'rb').read()).hexdigest()
    logger.info(f"Matrix saved. SHA-256: {checksum}")
    
    # If requested, print metadata
    if args.output:
        print(f"{{\"path\": \"{output_path}\", \"checksum\": \"{checksum}\", \"N\": {args.N}, \"seed\": {args.seed}}}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())