"""
Generate 1D tight-binding Hamiltonians with disorder.
"""
import numpy as np
from typing import Tuple, Dict, Any
from code.config import get_config
from scipy import linalg
from scipy import sparse
from scipy.sparse.linalg import eigsh
import logging

logger = logging.getLogger(__name__)

def generate_hamiltonian(L: int, W: float, seed: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, bool]:
    """
    Generate a 1D tight-binding Hamiltonian with disorder.
    
    H = -t Σ(|i⟩⟨i+1| + |i+1⟩⟨i|) + Σ εᵢ |i⟩⟨i|
    
    where εᵢ ~ U(-W/2, W/2)
    
    Args:
        L: System size (number of sites).
        W: Disorder strength.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (Hamiltonian, eigenvalues, eigenvectors, residual_norm, converged)
    """
    np.random.seed(seed)
    
    # Hopping parameter
    t = 1.0
    
    # On-site disorder: εᵢ ~ U(-W/2, W/2)
    epsilon = np.random.uniform(-W/2, W/2, L)
    
    # Build Hamiltonian
    # Diagonal: on-site energies
    diag = epsilon
    
    # Off-diagonal: hopping
    off_diag = -t * np.ones(L - 1)
    
    # Create sparse matrix for efficiency
    from scipy.sparse import diags
    H_sparse = diags([off_diag, diag, off_diag], offsets=[-1, 0, 1], format='csr')
    
    # Convert to dense for small systems, keep sparse for large
    if L <= 1000:
        H = H_sparse.toarray()
        # Full diagonalization
        try:
            eigvals, eigvecs = linalg.eigh(H)
            residual_norm = 0.0  # Full diagonalization is exact
            converged = True
        except Exception as e:
            logger.warning(f"Full diagonalization failed, trying sparse: {e}")
            # Fallback to sparse
            H = H_sparse
            k = min(20, L)  # Number of eigenvalues to compute
            eigvals, eigvecs = eigsh(H, k=k, which='SM')  # Smallest magnitude
            # Compute residual for first eigenvalue
            residual = np.linalg.norm(H @ eigvecs[:, 0] - eigvals[0] * eigvecs[:, 0])
            residual_norm = float(residual)
            converged = residual < 1e-6
    else:
        # Use sparse for large systems
        H = H_sparse
        k = min(50, L)  # Number of eigenvalues to compute
        try:
            eigvals, eigvecs = eigsh(H, k=k, which='SM')  # Smallest magnitude
            # Compute residual for first eigenvalue
            residual = np.linalg.norm(H @ eigvecs[:, 0] - eigvals[0] * eigvecs[:, 0])
            residual_norm = float(residual)
            converged = residual < 1e-6
        except Exception as e:
            logger.error(f"Sparse diagonalization failed: {e}")
            raise
    
    return H, eigvals, eigvecs, residual_norm, converged

def generate_hamiltonian_batch(L: int, W: float, seeds: list) -> list:
    """
    Generate multiple Hamiltonians with different seeds.
    
    Args:
        L: System size.
        W: Disorder strength.
        seeds: List of seeds.
        
    Returns:
        List of (Hamiltonian, eigenvalues, eigenvectors) tuples.
    """
    results = []
    for seed in seeds:
        H, eigvals, eigvecs, residual, converged = generate_hamiltonian(L, W, seed)
        results.append({
            "H": H,
            "eigenvalues": eigvals,
            "eigenvectors": eigvecs,
            "residual": residual,
            "converged": converged,
            "seed": seed
        })
    return results

def main():
    """
    Main entry point for Hamiltonian generation.
    """
    config = get_config()
    
    # Example: Generate a single Hamiltonian
    L = 100
    W = 1.0
    seed = 42
    
    H, eigvals, eigvecs, residual, converged = generate_hamiltonian(L, W, seed)
    
    print(f"Generated Hamiltonian: L={L}, W={W}")
    print(f"Eigenvalue range: [{eigvals.min():.4f}, {eigvals.max():.4f}]")
    print(f"Residual norm: {residual:.2e}, Converged: {converged}")

if __name__ == "__main__":
    main()
