"""
Parameter sweep orchestrator for US2.

Executes a grid search over matrix sizes (N) and perturbation norms (theta),
consuming checksummed raw data produced by T040/T019 to ensure data hygiene compliance.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np

# Project imports based on provided API surface
from utils.config import get_project_paths, ensure_directories
from utils.checksum import load_checksum_manifest, verify_checksums, compute_file_checksum
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end
from utils.results_logger import append_to_aggregated_results
from data_models import PerturbationConfig, SimulationRun
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold
from analysis.matrix_hygiene import run_hygiene_capture

# Configure logging
logger = logging.getLogger(__name__)

def generate_sweep_grid(
    n_min: int = 200,
    n_max: int = 2000,
    n_step: int = 200,
    theta_min: float = 1.0,
    theta_max: float = 3.0,
    theta_step: float = 0.5,
    sparsity_density: float = 1.0  # 1.0 for diagonal, <1.0 for sparse
) -> List[Dict[str, Any]]:
    """
    Generate a list of configuration dictionaries for the parameter sweep.
    """
    configs = []
    # Ensure n_max is included if it's within step
    n_values = list(range(n_min, n_max + 1, n_step))
    if n_max not in n_values:
        n_values.append(n_max)
    
    theta_values = np.arange(theta_min, theta_max + 0.01, theta_step).tolist()

    for n in n_values:
        for theta in theta_values:
            configs.append({
                "n": n,
                "theta": theta,
                "sparsity_density": sparsity_density,
                "seed": None  # Seed assigned at runtime
            })
    return configs

def run_single_sweep_instance(
    config: Dict[str, Any],
    output_dir: Path,
    raw_data_dir: Path,
    checksum_manifest_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Execute a single point in the parameter sweep.
    
    This function is designed to consume checksummed raw data if available,
    or generate new data and immediately checksum it (hygiene capture).
    """
    n = config["n"]
    theta = config["theta"]
    sparsity_density = config["sparsity_density"]
    seed = config.get("seed")
    
    if seed is None:
        seed = int(np.random.randint(0, 2**31 - 1))
    
    # Setup paths for this specific run
    run_id = f"N{n}_theta{theta:.1f}_seed{seed}"
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = run_dir / "simulation.log"
    logger = setup_simulation_logger(run_id, log_path)
    
    log_simulation_start(logger, config)
    
    try:
        # 1. Load or Generate Raw Data
        # Check if raw data exists and is checksummed (from T040)
        raw_matrix_path = raw_data_dir / run_id / "matrix.npy"
        perturbation_path = raw_data_dir / run_id / "perturbation.npy"
        
        matrix = None
        perturbation = None
        
        if checksum_manifest_path and checksum_manifest_path.exists():
            # Attempt to verify existing checksummed data
            manifest = load_checksum_manifest(checksum_manifest_path)
            # Simplified verification logic for this task context
            # In a full system, we'd map run_id to specific file hashes in manifest
            if raw_matrix_path.exists() and perturbation_path.exists():
                # Verify integrity
                if verify_checksums(raw_matrix_path, perturbation_path, manifest):
                    logger.info(f"Loaded verified raw data for {run_id}")
                    matrix = np.load(raw_matrix_path)
                    perturbation = np.load(perturbation_path)
                else:
                    logger.warning(f"Checksum mismatch for {run_id}, regenerating data.")
                    matrix = None
        
        if matrix is None:
            logger.info(f"Generating raw data for {run_id}")
            # Generate Wigner Matrix
            matrix = generate_wigner_matrix(n, seed=seed)
            
            # Generate Perturbation
            # Perturbation config: rank-1, norm=theta, sparsity=sparsity_density
            pert_config = PerturbationConfig(
                rank=1,
                norm=theta,
                sparsity_density=sparsity_density,
                seed=seed + 1
            )
            perturbation = create_perturbation(n, pert_config)
            
            # Save raw data immediately for hygiene (T040 compliance)
            np.save(raw_matrix_path, matrix)
            np.save(perturbation_path, perturbation)
            
            # Capture hygiene checksums
            run_hygiene_capture(run_dir, [raw_matrix_path, perturbation_path])
            
        # 2. Compute Eigenvalues
        # Add perturbation to Wigner matrix
        H = matrix + perturbation
        
        # Compute top 10 eigenvalues
        eigenvalues, _ = compute_top_eigenvalues(H, k=10, which='LM')
        
        # 3. Validate and Detect Outliers
        # Validate against semicircle edge (2.0) strictly
        is_valid = validate_eigenvalues(eigenvalues, threshold=2.0)
        
        # Calculate theoretical BBP threshold
        # For rank-1 perturbation with norm theta, outlier emerges if theta > 1.0
        # Theoretical outlier position: theta + 1/theta
        bbp_threshold = calculate_bbp_threshold(1.0) # assuming sigma=1 for standard Wigner
        
        # Detect outliers
        outlier_result = detect_outliers(eigenvalues, pert_config, bbp_threshold)
        
        # 4. Record Results
        result = {
            "run_id": run_id,
            "n": n,
            "theta": theta,
            "sparsity_density": sparsity_density,
            "seed": seed,
            "eigenvalues_top_10": eigenvalues.tolist(),
            "outlier_detected": outlier_result.has_outlier,
            "outlier_value": outlier_result.outlier_value if outlier_result.has_outlier else None,
            "theoretical_threshold": bbp_threshold,
            "is_valid": is_valid,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Append to aggregated results
        append_to_aggregated_results(output_dir / "sweep_results.csv", result)
        
        log_simulation_end(logger, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in sweep instance {run_id}: {e}", exc_info=True)
        raise
    finally:
        # Cleanup logger
        import logging
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)

def main():
    """
    Main entry point for the threshold sweep orchestrator.
    """
    paths = get_project_paths()
    output_dir = paths["processed"]
    raw_data_dir = paths["raw"] / "sweep"
    checksum_manifest_path = paths["raw"] / "checksums.json"
    
    ensure_directories([output_dir, raw_data_dir])
    
    # Generate sweep grid
    # N from 200 to 2000, theta from 1.0 to 3.0
    configs = generate_sweep_grid(
        n_min=200, 
        n_max=2000, 
        n_step=200, 
        theta_min=1.0, 
        theta_max=3.0, 
        theta_step=0.5
    )
    
    logger.info(f"Starting sweep with {len(configs)} configurations.")
    
    results = []
    for i, config in enumerate(configs):
        logger.info(f"Processing {i+1}/{len(configs)}: N={config['n']}, theta={config['theta']}")
        try:
            result = run_single_sweep_instance(
                config, 
                output_dir, 
                raw_data_dir, 
                checksum_manifest_path
            )
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Failed to process config {config}: {e}")
            # Continue to next configuration
    
    logger.info(f"Sweep complete. {len(results)} successful runs recorded.")
    print(f"Sweep complete. Results saved to {output_dir / 'sweep_results.csv'}")

if __name__ == "__main__":
    main()
