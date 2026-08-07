import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

from utils.config import get_project_paths, ensure_directories, get_seed
from utils.checksum import compute_file_checksum, save_checksum_manifest
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.raw_data_capture import capture_and_checksum_raw_instance

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_sweep_configs(
    n_values: List[int],
    theta_values: List[float],
    sparsity_values: List[float],
    num_repeats: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate a grid of configurations for the parameter sweep.
    Returns a list of dicts with keys: N, theta, sparsity, repeat_id, seed.
    """
    configs = []
    base_seed = get_seed()
    for n in n_values:
        for theta in theta_values:
            for sparsity in sparsity_values:
                for r in range(num_repeats):
                    configs.append({
                        "N": n,
                        "theta": theta,
                        "sparsity": sparsity,
                        "repeat_id": r,
                        "seed": base_seed + r
                    })
    return configs

def run_single_sweep_instance(config: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    """
    Execute a single sweep instance:
    1. Generate Wigner matrix.
    2. Generate perturbation.
    3. Save raw matrices to disk (Npy/Npz).
    4. Compute checksums and save manifest.
    5. Return metadata for downstream aggregation.
    """
    N = config["N"]
    theta = config["theta"]
    sparsity = config["sparsity"]
    seed = config["seed"]
    repeat_id = config["repeat_id"]

    # Set seed for reproducibility
    np.random.seed(seed)

    # Generate Wigner Matrix (Dense)
    # Note: generate_wigner_matrix returns a dense numpy array
    wigner_matrix = generate_wigner_matrix(N, seed=seed)

    # Generate Perturbation
    # create_perturbation returns a sparse matrix (scipy.sparse)
    perturbation_matrix = create_perturbation(N, theta, sparsity, seed=seed)

    # Ensure output directory exists
    run_dir = output_dir / f"N{N}_theta{theta:.2f}_sparse{sparsity:.2f}_rep{repeat_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Capture and Save Raw Data
    # We use the hygiene capture function to save and checksum
    # This function handles saving dense matrices to .npy and sparse to .npz
    # and generates a checksum manifest for the run directory.
    
    # Save Wigner (Dense)
    wigner_path = run_dir / "wigner_matrix.npy"
    np.save(wigner_path, wigner_matrix)

    # Save Perturbation (Sparse)
    perturbation_path = run_dir / "perturbation_matrix.npz"
    # scipy.sparse.save_npz expects a sparse matrix
    import scipy.sparse as sp
    if not sp.issparse(perturbation_matrix):
        perturbation_matrix = sp.csr_matrix(perturbation_matrix)
    sp.save_npz(str(perturbation_path), perturbation_matrix)

    # Capture intermediate states (e.g., sum of matrices, though we might compute that later)
    # For now, we just checksum the raw inputs as required by Constitution Principle III
    checksums = {}
    checksums["wigner_matrix.npy"] = compute_file_checksum(wigner_path)
    checksums["perturbation_matrix.npz"] = compute_file_checksum(perturbation_path)

    # Save checksum manifest for this run
    manifest_path = run_dir / "checksums.json"
    with open(manifest_path, "w") as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Completed sweep instance: N={N}, theta={theta}, sparsity={sparsity}, rep={repeat_id}")
    logger.info(f"Saved raw data and checksums to {run_dir}")

    return {
        "N": N,
        "theta": theta,
        "sparsity": sparsity,
        "repeat_id": repeat_id,
        "seed": seed,
        "wigner_checksum": checksums["wigner_matrix.npy"],
        "perturbation_checksum": checksums["perturbation_matrix.npz"],
        "output_dir": str(run_dir)
    }

def main():
    """
    Entry point for generating and checksumming raw matrix instances for the full parameter sweep.
    This script must run before T020 (threshold_sweep.py) to ensure raw data hygiene.
    """
    paths = get_project_paths()
    raw_dir = paths["raw"] / "sweep"
    ensure_directories([raw_dir])

    # Define sweep parameters
    # N ranges from 200 to 2000 (smaller steps for demo, full run would be larger)
    n_values = [200, 500, 1000, 2000]
    # Theta range [1.0, 3.0]
    theta_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    # Sparsity densities
    sparsity_values = [0.1, 0.2, 0.5]
    num_repeats = 2

    logger.info("Generating sweep configurations...")
    configs = generate_sweep_configs(n_values, theta_values, sparsity_values, num_repeats)
    logger.info(f"Total configurations to process: {len(configs)}")

    results = []
    for i, config in enumerate(configs):
        logger.info(f"Processing {i+1}/{len(configs)}: {config}")
        try:
            result = run_single_sweep_instance(config, raw_dir)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process config {config}: {e}")
            raise

    # Save summary of all runs
    summary_path = raw_dir / "sweep_manifest.json"
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Sweep raw data generation complete. Manifest saved to {summary_path}")

if __name__ == "__main__":
    main()
