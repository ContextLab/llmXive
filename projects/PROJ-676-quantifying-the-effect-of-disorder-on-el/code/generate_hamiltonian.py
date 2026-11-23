"""
Generate 1D tight-binding Hamiltonians with disorder.
Implements FR-001.
"""
import numpy as np
from typing import Tuple, Dict, Any, List
from code.config import get_config
from scipy.sparse import diags
from code.logger import get_logger
import logging
from code.storage_utils import save_hamiltonian_to_hdf5

logger = logging.getLogger(__name__)
# Global numerical logger for residuals (used elsewhere)
numerical_logger = get_logger("data/metadata/residuals.json")

def generate_hamiltonian(L: int, W: float, seed: int, realization_index: int) -> np.ndarray:
    """
    Generate a 1D tight-binding Hamiltonian matrix, store it to HDF5,
    and log provenance and checksum.

    Args:
        L: System size (number of sites).
        W: Disorder strength.
        seed: Random seed for reproducibility.
        realization_index: Index of this realization.

    Returns:
        The Hamiltonian matrix (numpy.ndarray, shape (L, L)).
    """
    # Set seed for reproducibility
    rng = np.random.default_rng(seed)

    # On-site disorder: uniform distribution in [-W/2, W/2]
    eps = rng.uniform(-W / 2, W / 2, size=L)

    # Hopping term t = 1 (nearest‑neighbour)
    t = 1.0

    # Construct Hamiltonian using sparse diagonal format then convert to dense
    H = diags(
        [np.full(L - 1, -t), eps, np.full(L - 1, -t)],
        offsets=[-1, 0, 1],
        format='csr'
    ).toarray()

    # Log basic metadata for debugging / provenance if needed
    logger.debug(
        "Generated Hamiltonian (L=%d, W=%.3f, seed=%d, idx=%d) with Frobenius norm %.5f",
        L, W, seed, realization_index, np.linalg.norm(H, ord='fro')
    )

    # Persist Hamiltonian to HDF5 and record provenance/checksum
    # This satisfies the T002 requirement of storage with provenance.
    try:
        save_hamiltonian_to_hdf5(
            H=H,
            W=W,
            L=L,
            realization_index=realization_index,
            seed=seed
        )
    except Exception as e:
        logger.error("Failed to save Hamiltonian to HDF5: %s", e)
        # Propagate the exception so that upstream code is aware of the failure.
        raise

    return H

def generate_hamiltonian_batch(
    L: int, W: float, num_realizations: int, base_seed: int
) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
    """
    Generate multiple disorder realizations, storing each Hamiltonian to HDF5.

    Args:
        L: System size.
        W: Disorder strength.
        num_realizations: Number of realizations to generate.
        base_seed: Base seed for the batch (each realization adds its index).

    Returns:
        List of (Hamiltonian, metadata) tuples. Metadata contains the same fields
        that were previously returned by the original implementation for backward
        compatibility with any downstream code that may still expect it.
    """
    results: List[Tuple[np.ndarray, Dict[str, Any]]] = []
    for i in range(num_realizations):
        seed = base_seed + i
        H = generate_hamiltonian(L, W, seed, i)
        meta = {
            "L": L,
            "W": W,
            "seed": seed,
            "realization_index": i,
            "norm": np.linalg.norm(H, ord='fro')
        }
        results.append((H, meta))
    return results

def main():
    """CLI entry point for testing."""
    import argparse
    parser = argparse.ArgumentParser(description="Generate Hamiltonians")
    parser.add_argument("--L", type=int, default=100)
    parser.add_argument("--W", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n", type=int, default=1)
    args = parser.parse_args()

    configs = generate_hamiltonian_batch(args.L, args.W, args.n, args.seed)
    for i, (H, meta) in enumerate(configs):
        logger.info(
            "Generated H_%d with norm %.4f (L=%d, W=%.3f, seed=%d)",
            i, meta['norm'], meta['L'], meta['W'], meta['seed']
        )

if __name__ == "__main__":
    main()
