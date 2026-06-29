"""
Hamiltonian generation for XXZ Heisenberg spin chains with random disorder.

This module implements the construction of the XXZ Heisenberg Hamiltonian
with randomly perturbed nearest-neighbour couplings as specified in FR-002.
The couplings J_i are drawn from a uniform distribution U[1-delta, 1+delta].

References:
    - FR-002: Generate XXZ Heisenberg Hamiltonian with random nearest-neighbour couplings.
"""

import numpy as np
from scipy.sparse import csr_matrix, kron, identity
from typing import Tuple, List, Optional

from config import ConfigError, validate_float

# Pauli matrices and Identity for spin-1/2
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=np.complex128)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=np.complex128)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=np.complex128)
IDENTITY = np.array([[1, 0], [0, 1]], dtype=np.complex128)

def _pauli_matrix(i: int, sigma: np.ndarray, L: int) -> csr_matrix:
    """
    Construct the operator sigma acting on site i (0-indexed) in a chain of length L.
    Returns a sparse matrix of shape (2^L, 2^L).
    """
    ops = [IDENTITY] * L
    ops[i] = sigma
    # Build Kronecker product from right to left (standard convention: site 0 is rightmost)
    # However, for Hamiltonian sums, order doesn't strictly matter for correctness,
    # just consistency. We'll build: I x I x ... x sigma_i ... x I
    result = csr_matrix(ops[0])
    for op in ops[1:]:
        result = kron(result, op)
    return result

def generate_xxz_hamiltonian(
    L: int,
    delta: float,
    seed: Optional[int] = None
) -> csr_matrix:
    """
    Generate the XXZ Heisenberg Hamiltonian with random nearest-neighbour couplings.

    The Hamiltonian is defined as:
        H = sum_{i=0}^{L-2} J_i * (S_i^x S_{i+1}^x + S_i^y S_{i+1}^y + S_i^z S_{i+1}^z)

    where J_i ~ Uniform(1 - delta, 1 + delta).
    Spin operators S are related to Pauli matrices by S = (1/2) * sigma.

    Args:
        L: Chain length (number of spins). Must be >= 2.
        delta: Disorder strength. Couplings are in [1-delta, 1+delta].
        seed: Random seed for reproducibility.

    Returns:
        csr_matrix: The sparse Hamiltonian matrix of shape (2^L, 2^L).

    Raises:
        ConfigError: If L < 2 or delta is out of bounds [0, 1].
    """
    if L < 2:
        raise ConfigError(f"Chain length L must be >= 2, got {L}")
    
    try:
        validate_float(delta, "delta", min_val=0.0, max_val=1.0)
    except ValueError as e:
        raise ConfigError(str(e))

    if seed is not None:
        np.random.seed(seed)

    # Generate random couplings J_i for i in 0..L-2
    # J_i ~ U[1-delta, 1+delta]
    couplings = np.random.uniform(1.0 - delta, 1.0 + delta, size=L - 1)

    H = csr_matrix((2**L, 2**L), dtype=np.complex128)

    # Pre-compute Pauli operators for efficiency
    # We need sigma_x, sigma_y, sigma_z on each site
    paulis = {
        'x': [_pauli_matrix(i, SIGMA_X, L) for i in range(L)],
        'y': [_pauli_matrix(i, SIGMA_Y, L) for i in range(L)],
        'z': [_pauli_matrix(i, SIGMA_Z, L) for i in range(L)]
    }

    # Construct H = sum J_i * (S_i . S_{i+1})
    # S_i . S_{i+1} = (1/4) * (sigma_i^x sigma_{i+1}^x + sigma_i^y sigma_{i+1}^y + sigma_i^z sigma_{i+1}^z)
    factor = 0.25  # (1/2)*(1/2)

    for i in range(L - 1):
        J_i = couplings[i]
        
        # Term: S_i^x S_{i+1}^x
        term_xx = paulis['x'][i] * paulis['x'][i+1]
        
        # Term: S_i^y S_{i+1}^y
        term_yy = paulis['y'][i] * paulis['y'][i+1]
        
        # Term: S_i^z S_{i+1}^z
        term_zz = paulis['z'][i] * paulis['z'][i+1]
        
        interaction = (term_xx + term_yy + term_zz) * factor
        
        H += J_i * interaction

    return H

def get_coupling_distribution_stats(
    delta: float,
    n_samples: int = 10000,
    seed: Optional[int] = None
) -> Tuple[float, float, float, float]:
    """
    Compute statistics of the coupling distribution for verification.

    Args:
        delta: Disorder strength.
        n_samples: Number of samples to draw.
        seed: Random seed.

    Returns:
        Tuple of (mean, std, min_sample, max_sample).
    """
    if seed is not None:
        np.random.seed(seed)
    
    samples = np.random.uniform(1.0 - delta, 1.0 + delta, size=n_samples)
    return float(np.mean(samples)), float(np.std(samples)), float(np.min(samples)), float(np.max(samples))
