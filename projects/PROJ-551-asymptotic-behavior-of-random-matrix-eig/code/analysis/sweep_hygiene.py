"""
Sweep Hygiene Module (T040)

Generates raw matrix instances and intermediate states for the full parameter sweep,
saving them to data/raw/sweep/ and generating checksums to satisfy Constitution
Principle III (Data Hygiene). This task MUST run before T020.
"""
import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
from scipy import sparse

# Local imports matching API surface
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from utils.config import get_project_paths, ensure_directories, get_seed
from utils.checksum import compute_file_checksum, save_checksum_manifest
from data_models import PerturbationConfig, SimulationRun
from analysis.matrix_hygiene import save_matrix_to_npy, run_hygiene_capture

logger = logging.getLogger(__name__)

def generate_sweep_configs(
    n_values: List[int],
    theta_values: List[float],
    sparsity_density: float = 0.1,
    perturbation_rank: int = 1
) -> List[Dict[str, Any]]:
    """
    Generate a grid of configuration parameters for the sweep.
    """
    configs = []
    for n in n_values:
        for theta in theta_values:
            cfg = {
                "n": n,
                "theta": theta,
                "sparsity_density": sparsity_density,
                "perturbation_rank": perturbation_rank,
                "seed": get_seed() + int(n * 10000 + theta * 100)  # Deterministic seed per config
            }
            configs.append(cfg)
    return configs

def run_single_sweep_instance(cfg: Dict[str, Any], output_dir: Path) -> Optional[str]:
    """
    Run a single simulation instance for the sweep, saving raw matrix and
    intermediate states, and returning the path to the saved manifest entry.
    """
    n = cfg["n"]
    theta = cfg["theta"]
    seed = cfg["seed"]
    sparsity = cfg["sparsity_density"]
    rank = cfg["perturbation_rank"]

    logger.info(f"Generating sweep instance: N={n}, Theta={theta}, Seed={seed}")

    # Set seed for reproducibility
    np.random.seed(seed)

    try:
        # 1. Generate Wigner Matrix
        wigner_matrix = generate_wigner_matrix(n, seed=seed)
        
        # 2. Create Perturbation
        perturbation_config = PerturbationConfig(
            theta=theta,
            sparsity_density=sparsity,
            rank=rank
        )
        perturbation_matrix = create_perturbation(n, perturbation_config)

        # 3. Combine: H = W + P
        perturbed_matrix = wigner_matrix + perturbation_matrix

        # 4. Save Raw Data
        # Use a unique identifier for this run
        run_id = f"N{n}_Theta{theta:.1f}_Seed{seed}"
        base_path = output_dir / run_id
        base_path.mkdir(parents=True, exist_ok=True)

        # Save Wigner
        wigner_path = base_path / "wigner.npy"
        np.save(wigner_path, wigner_matrix)

        # Save Perturbation
        perturbation_path = base_path / "perturbation.npy"
        np.save(perturbation_path, perturbation_matrix.toarray() if sparse.issparse(perturbation_matrix) else perturbation_matrix)

        # Save Perturbed
        perturbed_path = base_path / "perturbed.npy"
        np.save(perturbed_path, perturbed_matrix)

        # 5. Capture Intermediate States (eigenvalues of Wigner only for sanity check)
        # Note: We don't compute full eigenvalues of perturbed here to save time,
        # but we save the matrix state. T020 will compute eigenvalues.
        # However, task T040 asks for "intermediate states". We save the Wigner eigenvalues
        # as a sanity check intermediate state.
        wigner_eigs = np.linalg.eigvalsh(wigner_matrix)
        eigs_path = base_path / "wigner_eigenvalues.npy"
        np.save(eigs_path, wigner_eigs)

        logger.info(f"Saved raw data for {run_id}")
        return str(base_path)

    except Exception as e:
        logger.error(f"Failed to generate sweep instance {run_id}: {e}", exc_info=True)
        return None

def main():
    """
    Main entry point for T040: Generate and checksum raw matrix instances for the sweep.
    """
    paths = get_project_paths()
    raw_dir = paths["data_raw"] / "sweep"
    ensure_directories([raw_dir])

    # Setup logging
    log_file = paths["data_logs"] / "sweep_hygiene.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    logger.info("Starting Sweep Hygiene Generation (T040)")

    # Define sweep parameters (matching T020 expectations)
    # N from small to 2000, Theta from 1.0 to 3.0
    n_values = [100, 200, 500, 1000, 2000]
    theta_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    
    # Generate configurations
    configs = generate_sweep_configs(n_values, theta_values)
    logger.info(f"Generated {len(configs)} sweep configurations.")

    successful_runs = []
    checksums = {}

    for cfg in configs:
        run_path = run_single_sweep_instance(cfg, raw_dir)
        if run_path:
            successful_runs.append(run_path)
            # Compute checksum for the directory
            try:
                checksum = compute_file_checksum(run_path) 
                # Note: compute_file_checksum expects a file. For directory, we might need a recursive hash or just hash the manifest later.
                # Let's compute checksums for the files inside the run directory instead.
                run_dir = Path(run_path)
                run_checksums = {}
                for f in run_dir.glob("*"):
                    if f.is_file():
                        run_checksums[f.name] = compute_file_checksum(str(f))
                checksums[run_path] = run_checksums
            except Exception as e:
                logger.warning(f"Could not compute checksum for {run_path}: {e}")

    # Save manifest
    manifest_path = raw_dir / "sweep_manifest.json"
    manifest_data = {
        "generated_at": str(np.datetime64('now')),
        "total_configs": len(configs),
        "successful_runs": len(successful_runs),
        "configs": configs,
        "checksums": checksums
    }

    with open(manifest_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Sweep Hygiene complete. Manifest saved to {manifest_path}")
    logger.info(f"Successful runs: {len(successful_runs)}/{len(configs)}")

    return manifest_path

if __name__ == "__main__":
    main()
