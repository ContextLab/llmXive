"""
Perturbation Matrix Constructor.
Creates sparse, deterministic perturbations (diagonal, block-sparse, random sparse)
to be added to the Wigner matrix.

Implements Spec Objectives 2, 7 and Constitution Principle VII (Sparse Perturbation Structural Fidelity).
"""
import numpy as np
from scipy import sparse
from typing import Literal, Optional

PerturbationType = Literal["diagonal", "block-sparse", "random sparse"]

def create_perturbation(
    N: int,
    theta: float,
    rank: int,
    pattern: PerturbationType = "diagonal",
    sparsity_density: float = 1.0,
    seed: Optional[int] = None
) -> np.ndarray:
    """
    Create a perturbation matrix P of size N x N.
    
    Parameters:
    -----------
    N : int
        Dimension of the matrix.
    theta : float
        Strength of the perturbation (norm scaling factor).
    rank : int
        Target rank of the perturbation (number of non-zero eigenvalues).
    pattern : str
        'diagonal', 'block-sparse', or 'random sparse'.
    sparsity_density : float
        Fraction of non-zero elements (0.0 to 1.0). 
        Only applies to 'block-sparse' and 'random sparse'.
        For 'diagonal', this is ignored (effectively 1.0 on support).
    seed : int, optional
        Random seed for reproducibility.
        
    Returns:
    --------
    np.ndarray
        N x N perturbation matrix.
        
    Raises:
    -------
    ValueError
        If pattern is unknown or parameters are invalid.
        
    Notes:
    ------
    - For 'diagonal': Places `theta` on the first `rank` diagonal entries.
    - For 'block-sparse': Creates a dense `rank x rank` block in the top-left,
      then applies a random binary mask with density `sparsity_density`.
    - For 'random sparse': Generates `rank` random unit vectors, applies sparsity mask,
      and sums their outer products scaled by `theta`.
    
    Rank Preservation Verification:
    The function attempts to maintain the specified rank. For 'random sparse',
    if a vector becomes zero after masking, it is skipped, potentially reducing
    the effective rank. The caller should verify the rank if strict adherence is required.
    """
    if rank < 0 or rank > N:
        raise ValueError(f"Rank {rank} must be between 0 and N ({N}).")
    if not (0.0 <= sparsity_density <= 1.0):
        raise ValueError(f"Sparsity density must be between 0.0 and 1.0, got {sparsity_density}.")
    
    if seed is not None:
        rng = np.random.default_rng(seed)
    else:
        rng = np.random.default_rng()

    P = np.zeros((N, N))

    if pattern == "diagonal":
        # Rank-k diagonal perturbation
        # Place theta on the first k diagonal entries
        # To ensure rank is exactly k (if theta != 0), we set distinct positions
        count = 0
        for i in range(N):
            if count < rank:
                P[i, i] = theta
                count += 1
        
    elif pattern == "block-sparse":
        # Block-sparse perturbation
        # 1. Create a dense rank-k block in the top-left corner
        # We construct a dense matrix of size rank x rank with random values,
        # then embed it into the N x N matrix.
        # To ensure rank is exactly k, we can use a random matrix of size rank x rank
        # and ensure it is full rank (prob 1 for continuous distribution).
        
        if rank == 0:
            return P
            
        block_size = rank
        # Generate a random dense block
        block = rng.standard_normal((block_size, block_size))
        
        # Embed into P
        P[:block_size, :block_size] = block
        
        # Apply sparsity mask to the non-zero block region
        # Mask is applied element-wise
        if sparsity_density < 1.0:
            mask = rng.random((block_size, block_size)) < sparsity_density
            P[:block_size, :block_size] = P[:block_size, :block_size] * mask
            
        # Scale by theta
        P[:block_size, :block_size] *= theta
        
        # Note: Sparsity masking might reduce the rank. 
        # Theoretical rank preservation is probabilistic.
        
    elif pattern == "random sparse":
        # Random sparse perturbation
        # Sum of `rank` rank-1 matrices: P = theta * sum(u_i * u_i^T)
        # where u_i are random vectors with sparsity mask applied.
        
        if rank == 0:
            return P

        for r in range(rank):
            # Generate a random vector
            v = rng.standard_normal(N)
            
            # Normalize to unit length
            norm_v = np.linalg.norm(v)
            if norm_v == 0:
                continue # Should be extremely rare
            v = v / norm_v
            
            # Apply sparsity mask
            if sparsity_density < 1.0:
                mask = rng.random(N) < sparsity_density
                v = v * mask
                # Re-check norm after masking
                norm_v_masked = np.linalg.norm(v)
                if norm_v_masked == 0:
                    # Vector vanished, skip this component
                    continue
                # Optional: Re-normalize to maintain unit norm contribution?
                # The spec says "verify rank preservation". If we don't re-normalize,
                # the contribution is scaled by the mask. 
                # Standard BBP perturbation usually assumes fixed norm.
                # Let's re-normalize to ensure the "strength" theta is applied to the direction.
                v = v / norm_v_masked
            
            # Add outer product
            P += theta * np.outer(v, v)
    
    else:
        raise ValueError(f"Unknown pattern: {pattern}. Supported: 'diagonal', 'block-sparse', 'random sparse'.")

    return P

def verify_rank_preservation(
    P: np.ndarray,
    expected_rank: int,
    tol: float = 1e-8
) -> tuple[bool, int]:
    """
    Verify if the perturbation matrix P has the expected rank.
    
    Parameters:
    -----------
    P : np.ndarray
        The perturbation matrix.
    expected_rank : int
        The target rank.
    tol : float
        Tolerance for singular value thresholding.
        
    Returns:
    --------
    (bool, int)
        A tuple (is_correct, actual_rank).
        is_correct is True if actual_rank == expected_rank.
    """
    # Compute singular values
    s = np.linalg.svd(P, compute_uv=False)
    actual_rank = np.sum(s > tol)
    return actual_rank == expected_rank, actual_rank
