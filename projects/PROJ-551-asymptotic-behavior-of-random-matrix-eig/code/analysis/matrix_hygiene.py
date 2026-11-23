"""
Matrix Hygiene Module for T019.

Generates raw matrix instances and intermediate states for a single simulation run,
saves them to `data/raw/`, and generates a checksum manifest to satisfy
Constitution Principle III (Data Hygiene).

This module is invoked by the main simulation loop (T014) or can be run
standalone for verification.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
from scipy import sparse

# Import from project API surface
from utils.checksum import compute_file_checksum, save_checksum_manifest
from utils.config import get_project_paths, ensure_directories, get_seed
from data_models import SimulationRun, PerturbationConfig
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues

logger = logging.getLogger(__name__)

def save_matrix_to_npy(matrix: np.ndarray, filepath: Path) -> None:
    """Saves a dense numpy array to .npy format."""
    np.save(str(filepath), matrix)
    logger.info(f"Saved matrix to {filepath} (shape: {matrix.shape})")

def save_sparse_matrix_to_npz(matrix: sparse.csr_matrix, filepath: Path) -> None:
    """Saves a sparse matrix to .npz format."""
    sparse.save_npz(str(filepath), matrix)
    logger.info(f"Saved sparse matrix to {filepath} (nnz: {matrix.nnz})")

def run_hygiene_capture(
    sim_run: SimulationRun,
    perturbation_config: PerturbationConfig,
    output_dir: Optional[Path] = None
) -> Dict[str, str]:
    """
    Executes the simulation for a specific configuration, captures the raw
    Wigner matrix, the perturbation matrix, the perturbed matrix, and the
    resulting eigenvalues to disk, then generates a checksum manifest.
    
    Args:
        sim_run: The simulation run configuration (contains N, seed, etc.).
        perturbation_config: The perturbation configuration (theta, rank, sparsity).
        output_dir: Optional override for the output directory. Defaults to data/raw/.
        
    Returns:
        A dictionary mapping file paths to their checksums.
    """
    # 1. Setup Paths
    paths = get_project_paths()
    if output_dir is None:
        output_dir = paths.raw_data_dir / "single_run"
    
    ensure_directories([output_dir])
    
    # Create unique subdirectory for this specific run instance
    run_id = f"N{sim_run.n}_seed{sim_run.seed}_theta{perturbation_config.theta:.2f}"
    run_dir = output_dir / run_id
    ensure_directories([run_dir])
    
    logger.info(f"Starting hygiene capture for run: {run_dir}")
    
    # 2. Generate Raw Matrices
    # Set seed for reproducibility
    np.random.seed(sim_run.seed)
    
    # Generate Wigner Matrix
    wigner_matrix = generate_wigner_matrix(sim_run.n)
    wigner_path = run_dir / "wigner_matrix.npy"
    save_matrix_to_npy(wigner_matrix, wigner_path)
    
    # Generate Perturbation Matrix
    perturbation_matrix = create_perturbation(
        n=sim_run.n,
        theta=perturbation_config.theta,
        rank=perturbation_config.rank,
        sparsity_density=perturbation_config.sparsity_density
    )
    
    # Save perturbation (sparse if applicable)
    if sparse.issparse(perturbation_matrix):
        perturbation_path = run_dir / "perturbation_matrix.npz"
        save_sparse_matrix_to_npz(perturbation_matrix.tocsr(), perturbation_path)
    else:
        perturbation_path = run_dir / "perturbation_matrix.npy"
        save_matrix_to_npy(perturbation_matrix, perturbation_path)
    
    # 3. Compute Perturbed Matrix (Intermediate State)
    perturbed_matrix = wigner_matrix + perturbation_matrix
    perturbed_path = run_dir / "perturbed_matrix.npy"
    save_matrix_to_npy(perturbed_matrix, perturbed_path)
    
    # 4. Compute Eigenvalues (Intermediate State)
    # Using the existing solver from T007
    top_k = min(10, sim_run.n)
    eigenvalues, _ = compute_top_eigenvalues(perturbed_matrix, k=top_k)
    
    # Save eigenvalues
    eigenvalues_path = run_dir / "top_eigenvalues.npy"
    np.save(str(eigenvalues_path), eigenvalues)
    logger.info(f"Saved top {len(eigenvalues)} eigenvalues to {eigenvalues_path}")
    
    # 5. Generate Checksum Manifest
    # Collect all generated files
    generated_files = [
        wigner_path,
        perturbation_path,
        perturbed_path,
        eigenvalues_path
    ]
    
    # Compute checksums
    checksums = {}
    for f_path in generated_files:
        if f_path.exists():
          checksums[str(f_path)] = compute_file_checksum(f_path)
        else:
          raise FileNotFoundError(f"Expected file not found for checksum: {f_path}")
    
    # Save manifest
    manifest_path = run_dir / "checksum_manifest.json"
    save_checksum_manifest(checksums, manifest_path)
    logger.info(f"Saved checksum manifest to {manifest_path}")
    
    return checksums

def main():
    """
    Standalone entry point to run a single hygiene capture.
    Usage: python code/analysis/matrix_hygiene.py
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Matrix Hygiene Capture (T019)")
    parser.add_argument("--n", type=int, default=1000, help="Matrix size N")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--theta", type=float, default=2.5, help="Perturbation norm")
    parser.add_argument("--rank", type=int, default=1, help="Perturbation rank")
    parser.add_argument("--sparsity", type=float, default=1.0, help="Sparsity density (1.0 = dense)")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create config objects
    sim_run = SimulationRun(
        n=args.n,
        seed=args.seed,
        num_eigenvalues=10
    )
    
    perturbation_config = PerturbationConfig(
        theta=args.theta,
        rank=args.rank,
        sparsity_density=args.sparsity
    )
    
    try:
        checksums = run_hygiene_capture(sim_run, perturbation_config)
        print(f"Hygiene capture complete. Manifest saved.")
        print(f"Checksums: {checksums}")
    except Exception as e:
        logger.error(f"Hygiene capture failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
