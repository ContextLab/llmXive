"""
Hamiltonian Generator for 1D Tight-Binding Chains with Disorder.

Implements FR-001: Generate 1D tight-binding matrices L x L with hopping t=1
and on-site energies epsilon_i ~ U(-W/2, W/2).

This module produces the fundamental input for the localization length analysis.
"""

import numpy as np
from typing import Tuple, Dict, Any

from code.config import get_config


def generate_hamiltonian(
    L: int,
    W: float,
    seed: int,
    t: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a 1D tight-binding Hamiltonian matrix with random on-site disorder.

    The Hamiltonian is defined as:
    H = -t * sum_{i} (|i><i+1| + |i+1><i|) + sum_{i} epsilon_i |i><i|

    where:
    - t is the hopping parameter (default 1.0)
    - epsilon_i are on-site energies drawn from Uniform(-W/2, W/2)

    Parameters
    ----------
    L : int
        System size (number of sites). The matrix will be L x L.
    W : float
        Disorder strength. On-site energies are uniformly distributed in [-W/2, W/2].
    seed : int
        Random seed for reproducibility.
    t : float, optional
        Hopping parameter. Default is 1.0.

    Returns
    -------
    H : np.ndarray
        The L x L Hamiltonian matrix.
    epsilons : np.ndarray
        The array of on-site energies used, shape (L,).

    Raises
    ------
    ValueError
        If L <= 0 or W < 0.
    """
    if L <= 0:
        raise ValueError(f"System size L must be positive, got {L}")
    if W < 0:
        raise ValueError(f"Disorder strength W must be non-negative, got {W}")

    # Initialize random state with specific seed
    rng = np.random.default_rng(seed)

    # Generate on-site disorder: epsilon_i ~ U(-W/2, W/2)
    # Using the newer Generator API for better statistical properties
    if W == 0.0:
        epsilons = np.zeros(L, dtype=np.float64)
    else:
        epsilons = rng.uniform(-W / 2.0, W / 2.0, size=L)

    # Construct the Hamiltonian
    # Diagonal: on-site energies
    # Off-diagonal: hopping -t (nearest neighbors)
    # We use scipy.sparse for large L to save memory, but for L <= 1600 dense is fine
    # and often faster for the eigenvalue solvers we'll use next (eigh).
    # Given the constraints (L up to 1600), dense is acceptable and simpler.

    H = np.diag(epsilons)

    # Add hopping terms
    # H[i, i+1] = H[i+1, i] = -t
    if L > 1:
        off_diag = -t * np.ones(L - 1, dtype=np.float64)
        H += np.diag(off_diag, k=1)
        H += np.diag(off_diag, k=-1)

    return H, epsilons


def generate_hamiltonian_batch(
    L: int,
    W: float,
    num_realizations: int,
    base_seed: int,
    t: float = 1.0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a batch of Hamiltonians for a given (L, W) configuration.

    This is a convenience wrapper for running multiple realizations.

    Parameters
    ----------
    L : int
        System size.
    W : float
        Disorder strength.
    num_realizations : int
        Number of disorder realizations to generate.
    base_seed : int
        Base random seed. Each realization gets seed = base_seed + i.
    t : float, optional
        Hopping parameter. Default 1.0.

    Returns
    -------
    H_batch : np.ndarray
        Array of shape (num_realizations, L, L) containing the Hamiltonians.
    epsilons_batch : np.ndarray
        Array of shape (num_realizations, L) containing the on-site energies.
    """
    H_batch = np.empty((num_realizations, L, L), dtype=np.float64)
    epsilons_batch = np.empty((num_realizations, L), dtype=np.float64)

    for i in range(num_realizations):
        seed = base_seed + i
        H, epsilons = generate_hamiltonian(L, W, seed, t)
        H_batch[i] = H
        epsilons_batch[i] = epsilons

    return H_batch, epsilons_batch


def main():
    """
    CLI entry point to generate a single Hamiltonian and save to data/raw/.
    Demonstrates the core functionality of T005.
    """
    config = get_config()

    # Use a small system for demonstration if running standalone
    # In the full pipeline, these values come from config
    L_demo = config.L_MIN  # Smallest L for testing
    W_demo = 1.0
    seed_demo = 42

    print(f"Generating Hamiltonian: L={L_demo}, W={W_demo}, seed={seed_demo}")

    H, epsilons = generate_hamiltonian(L_demo, W_demo, seed_demo)

    # Save to data/raw
    output_dir = config.DATA_RAW_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    filepath = output_dir / f"hamiltonian_L{L_demo}_W{W_demo}_seed{seed_demo}.npz"

    np.savez_compressed(
        filepath,
        H=H,
        epsilons=epsilons,
        L=L_demo,
        W=W_demo,
        seed=seed_demo,
        t=1.0
    )

    print(f"Saved Hamiltonian to {filepath}")
    print(f"Matrix shape: {H.shape}")
    print(f"Energy range: [{epsilons.min():.4f}, {epsilons.max():.4f}]")

    # Verify symmetry
    if not np.allclose(H, H.T):
        raise RuntimeError("Generated Hamiltonian is not symmetric!")


if __name__ == "__main__":
    main()
