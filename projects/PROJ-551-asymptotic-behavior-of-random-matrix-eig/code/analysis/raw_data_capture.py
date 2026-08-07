"""
Raw Data Capture Module for Constitution Principle III (Data Hygiene).

This module generates raw matrix instances (Wigner + Perturbation) and
intermediate states, saving them to `data/raw/` and computing checksums
to ensure traceability and integrity.
"""
import os
import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy import sparse

# Import from existing API surface
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from utils.config import get_project_paths, get_seed, get_matrix_size, get_perturbation_norm, get_sparsity_density
from utils.checksum import compute_file_checksum, save_checksum_manifest
from utils.logging_config import setup_simulation_logger

logger = logging.getLogger(__name__)


def save_dense_matrix_to_npy(matrix: np.ndarray, filepath: Path) -> str:
    """
    Saves a dense numpy matrix to .npy format and returns the checksum.
    """
    np.save(str(filepath), matrix)
    checksum = compute_file_checksum(filepath)
    logger.info(f"Saved dense matrix to {filepath} (Checksum: {checksum[:16]}...)")
    return checksum


def save_sparse_matrix_to_npz(matrix: sparse.csr_matrix, filepath: Path) -> str:
    """
    Saves a sparse matrix to .npz format and returns the checksum.
    """
    sparse.save_npz(str(filepath), matrix)
    checksum = compute_file_checksum(filepath)
    logger.info(f"Saved sparse matrix to {filepath} (Checksum: {checksum[:16]}...)")
    return checksum


def capture_and_checksum_raw_instance(
    n: int,
    theta: float,
    sparsity: float,
    seed: int,
    output_dir: Optional[Path] = None,
    run_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a single raw matrix instance (Wigner + Perturbation),
    saves it to disk in `data/raw/`, computes checksums, and returns metadata.

    This satisfies Constitution Principle III: Data Hygiene.

    Args:
        n: Matrix dimension.
        theta: Perturbation norm.
        sparsity: Sparsity density of the perturbation.
        seed: Random seed for reproducibility.
        output_dir: Directory to save raw data (defaults to project data/raw).
        run_id: Unique identifier for this run (optional, generated if None).

    Returns:
        Dictionary containing file paths, checksums, and parameters.
    """
    if output_dir is None:
        paths = get_project_paths()
        output_dir = paths["raw_data"]

    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    if run_id is None:
        run_id = f"run_{int(time.time())}_{seed}"

    logger.info(f"Capturing raw instance: N={n}, theta={theta}, sparsity={sparsity}, seed={seed}")

    # 1. Generate Wigner Matrix
    # Set seed explicitly for this specific generation step
    np.random.seed(seed)
    wigner_matrix = generate_wigner_matrix(n)

    # Save Wigner Matrix
    wigner_path = output_dir / f"{run_id}_wigner.npy"
    wigner_checksum = save_dense_matrix_to_npy(wigner_matrix, wigner_path)

    # 2. Generate Perturbation Matrix
    # Continue random state or re-seed? Task implies a single seed for the instance.
    # We use the same seed context or a derived one to ensure reproducibility.
    # For strict reproducibility, we re-seed the perturbation generation if needed,
    # but typically the generator handles internal state.
    # Here we pass the seed to ensure deterministic perturbation if the generator supports it.
    perturbation_matrix = create_perturbation(n, theta, sparsity, seed=seed)

    # Save Perturbation Matrix (sparse)
    # Convert to sparse if dense for storage efficiency if it is sparse
    if sparse.issparse(perturbation_matrix):
        pert_path = output_dir / f"{run_id}_perturbation.npz"
        pert_checksum = save_sparse_matrix_to_npz(perturbation_matrix, pert_path)
        is_sparse = True
    else:
        pert_path = output_dir / f"{run_id}_perturbation.npy"
        pert_checksum = save_dense_matrix_to_npy(perturbation_matrix, pert_path)
        is_sparse = False

    # 3. Save Intermediate State: The Sum (H = W + P)
    # We compute the sum explicitly for the "intermediate state" before eigenvalue computation
    # to ensure we are checksumming the exact input to the solver.
    # If both are sparse, sum is sparse. If one is dense, sum is dense.
    if sparse.issparse(wigner_matrix) and sparse.issparse(perturbation_matrix):
        total_matrix = wigner_matrix + perturbation_matrix
        total_path = output_dir / f"{run_id}_total.npz"
        total_checksum = save_sparse_matrix_to_npz(total_matrix, total_path)
    else:
        # Ensure dense for sum if any component is dense
        w_dense = wigner_matrix.toarray() if sparse.issparse(wigner_matrix) else wigner_matrix
        p_dense = perturbation_matrix.toarray() if sparse.issparse(perturbation_matrix) else perturbation_matrix
        total_matrix = w_dense + p_dense
        total_path = output_dir / f"{run_id}_total.npy"
        total_checksum = save_dense_matrix_to_npy(total_matrix, total_path)

    # 4. Construct Metadata Manifest Entry
    manifest_entry = {
        "run_id": run_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "parameters": {
            "n": n,
            "theta": theta,
            "sparsity": sparsity,
            "seed": seed
        },
        "files": {
            "wigner": {
                "path": str(wigner_path.relative_to(output_dir.parent)),
                "checksum": wigner_checksum,
                "format": "npy"
            },
            "perturbation": {
                "path": str(pert_path.relative_to(output_dir.parent)),
                "checksum": pert_checksum,
                "format": "npz" if is_sparse else "npy"
            },
            "total": {
                "path": str(total_path.relative_to(output_dir.parent)),
                "checksum": total_checksum,
                "format": "npz" if sparse.issparse(total_matrix) else "npy"
            }
        }
    }

    logger.info(f"Raw instance captured and checksummed: {run_id}")
    return manifest_entry


def run_hygiene_capture(
    n: Optional[int] = None,
    theta: Optional[float] = None,
    sparsity: Optional[float] = None,
    seed: Optional[int] = None,
    output_dir: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Orchestrates the capture of a single raw data instance.
    Falls back to config defaults if parameters are not provided.
    """
    # Resolve parameters
    if n is None:
        n = get_matrix_size()
    if theta is None:
        theta = get_perturbation_norm()
    if sparsity is None:
        sparsity = get_sparsity_density()
    if seed is None:
        seed = get_seed()

    if output_dir is None:
        paths = get_project_paths()
        output_dir = paths["raw_data"]

    # Setup logger
    log_path = output_dir.parent / "logs" / "raw_capture.log"
    setup_simulation_logger("raw_capture", log_file=str(log_path))

    # Capture
    manifest_entry = capture_and_checksum_raw_instance(
        n=n,
        theta=theta,
        sparsity=sparsity,
        seed=seed,
        output_dir=output_dir
    )

    # Save manifest for this run
    manifest_path = output_dir / f"{manifest_entry['run_id']}_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest_entry, f, indent=2)

    # Update global checksum manifest if it exists or create new
    global_manifest_path = output_dir.parent / "checksums" / "raw_manifest.json"
    save_checksum_manifest(manifest_entry, global_manifest_path)

    return manifest_entry


def main():
    """
    Entry point for CLI execution.
    Usage: python -m code.analysis.raw_data_capture
    """
    import argparse

    parser = argparse.ArgumentParser(description="Capture and checksum raw matrix instances.")
    parser.add_argument("--n", type=int, help="Matrix size (N)")
    parser.add_argument("--theta", type=float, help="Perturbation norm")
    parser.add_argument("--sparsity", type=float, help="Sparsity density")
    parser.add_argument("--seed", type=int, help="Random seed")
    args = parser.parse_args()

    try:
        result = run_hygiene_capture(
            n=args.n,
            theta=args.theta,
            sparsity=args.sparsity,
            seed=args.seed
        )
        print(f"Success. Manifest saved to: {result['run_id']}_manifest.json")
        print(f"Checksums: Wigner={result['files']['wigner']['checksum'][:16]}... "
              f"Pert={result['files']['perturbation']['checksum'][:16]}... "
              f"Total={result['files']['total']['checksum'][:16]}...")
    except Exception as e:
        logger.exception("Failed to capture raw data")
        raise


if __name__ == "__main__":
    main()