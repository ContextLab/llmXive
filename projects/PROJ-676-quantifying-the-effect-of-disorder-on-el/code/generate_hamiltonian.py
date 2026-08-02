"""
Generate 1D tight-binding Hamiltonians with disorder.
Implements FR-001.
"""
import numpy as np
from typing import Tuple, Dict, Any, List
from code.config import get_config
from scipy import linalg
from scipy import sparse
from scipy.sparse import diags
from code.logger import get_logger, inject_log_residual
import logging

logger = logging.getLogger(__name__)
numerical_logger = get_logger("data/metadata/residuals.json")

def generate_hamiltonian(L: int, W: float, seed: int, realization_index: int) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Generate a 1D tight-binding Hamiltonian matrix.

    Args:
        L: System size (number of sites).
        W: Disorder strength.
        seed: Random seed for reproducibility.
        realization_index: Index of this realization.

    Returns:
        Tuple of (Hamiltonian matrix, metadata dict).
    """
    # Set seed
    rng = np.random.default_rng(seed)

    # On-site disorder: uniform distribution in [-W/2, W/2]
    eps = rng.uniform(-W/2, W/2, size=L)

    # Hopping term t=1
    t = 1.0

    # Construct Hamiltonian
    # Diagonal: on-site energies
    diagonal = eps
    # Off-diagonal: hopping
    off_diagonal = np.full(L - 1, -t)

    H = diags(
        [off_diagonal, diagonal, off_diagonal],
        offsets=[-1, 0, 1],
        format='csr'
    ).toarray()

    # Log metadata
    meta = {
        "L": L,
        "W": W,
        "seed": seed,
        "realization_index": realization_index,
        "norm": np.linalg.norm(H, ord='fro')
    }

    return H, meta

def generate_hamiltonian_batch(
    L: int, W: float, num_realizations: int, base_seed: int
) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
    """
    Generate multiple disorder realizations.

    Args:
        L: System size.
        W: Disorder strength.
        num_realizations: Number of realizations to generate.
        base_seed: Base seed for the batch.

    Returns:
        List of (Hamiltonian, metadata) tuples.
    """
    results = []
    for i in range(num_realizations):
        seed = base_seed + i
        H, meta = generate_hamiltonian(L, W, seed, i)
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
        logger.info(f"Generated H_{i} with norm {meta['norm']:.4f}")

    if __name__ == "__main__":
        main()
