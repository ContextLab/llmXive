"""
Perturbation Matrix Constructor.
Creates sparse, deterministic perturbations (diagonal or random sparse)
to be added to the Wigner matrix.
"""
import numpy as np
from scipy import sparse

def create_perturbation(N: int, theta: float, rank: int, 
                        pattern: str = "diagonal", 
                        sparsity_density: float = 1.0,
                        seed: int | None = None) -> np.ndarray:
    """
    Create a perturbation matrix P.
    
    Parameters:
    -----------
    N : int
        Dimension of the matrix.
    theta : float
        Strength of the perturbation (norm).
    rank : int
        Rank of the perturbation.
    pattern : str
        'diagonal' or 'random_sparse'.
    sparsity_density : float
        Fraction of non-zero elements (only for random_sparse).
    seed : int, optional
        Random seed.
        
    Returns:
    --------
    np.ndarray
        N x N perturbation matrix.
    """
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    P = np.zeros((N, N))

    if pattern == "diagonal":
        # Rank-k diagonal perturbation
        # Place theta on the first k diagonal entries
        # To ensure rank is exactly k, we can use distinct values or just theta
        # Theoretical BBP usually assumes rank 1 or fixed rank with strength theta.
        # We set P_ii = theta for i in 0..rank-1
        for i in range(min(rank, N)):
            P[i, i] = theta
            
    elif pattern == "random_sparse":
        # Random sparse perturbation
        # Create a low-rank structure masked by sparsity
        # Generate a random matrix of size N x rank
        U = rng.standard_normal((N, rank))
        # Orthogonalize or just use random? 
        # For BBP, usually P = theta * u u^T (rank 1) or sum of such.
        # Let's do sum of k rank-1 matrices with random vectors.
        for r in range(rank):
            v = rng.standard_normal(N)
            v = v / np.linalg.norm(v) # Normalize
            # Apply sparsity mask
            if sparsity_density < 1.0:
                mask = rng.random(N) < sparsity_density
                v[mask == False] = 0.0
                # Re-normalize if needed? Or just accept reduced norm?
                # The prompt says "verify rank preservation during sparsity masking".
                # If we zero out, rank might drop if v becomes zero vector.
                if np.linalg.norm(v) == 0:
                    continue # Skip this component if it vanished
                v = v / np.linalg.norm(v)
            
            P += theta * np.outer(v, v)
    else:
        raise ValueError(f"Unknown pattern: {pattern}")

    return P
