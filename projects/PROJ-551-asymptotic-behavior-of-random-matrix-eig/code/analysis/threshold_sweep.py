"""
Threshold Sweep Orchestrator for User Story 2.

This module implements the parameter sweep orchestrator that:
1. Defines the parameter grid (N, theta)
2. Executes the loop calling T040a/T040b logic to generate and checksum data
3. Ingests the checksummed raw data
4. Manages iterations and aggregates results
"""
import os
import sys
import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
from scipy import sparse

# Project imports
from utils.config import get_project_paths, get_seed, get_tolerance
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end
from utils.checksum import compute_file_checksum, save_checksum_manifest
from data_models import PerturbationConfig, SimulationRun

# Generators
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation

# Analysis helpers (referenced from API surface)
# Note: We call the specific functions that implement T040a/T040b logic
# Since T040a/T040b are marked complete, we assume the helper functions exist
# or we implement the inline logic here to ensure robustness.
# Based on API surface, we have `analysis.sweep_matrix_generator` and `analysis.sweep_checksums`.
# We will import the specific logic to ensure we are using the real implementations.

try:
    from analysis.sweep_matrix_generator import save_raw_sweep_matrix
    from analysis.sweep_checksums import checksum_sweep_matrices, find_sweep_matrices
except ImportError:
    # Fallback if specific module paths differ, but per API surface they should exist.
    # We will implement the inline logic to ensure T020 is self-contained and runnable
    # if the specific helpers were not fully fleshed out in previous steps.
    save_raw_sweep_matrix = None
    checksum_sweep_matrices = None
    find_sweep_matrices = None

logger = logging.getLogger(__name__)

def generate_sweep_grid(
    N_values: List[int],
    theta_values: List[float],
    seeds: List[int],
    sparsity_densities: List[float] = None
) -> List[Dict[str, Any]]:
    """
    Generate the parameter grid for the sweep.
    
    Args:
        N_values: List of matrix dimensions (e.g., [1000, 2000])
        theta_values: List of perturbation norms (e.g., [1.5, 2.0, 2.5, 3.0])
        seeds: List of random seeds for reproducibility
        sparsity_densities: Optional list of sparsity densities for sensitivity analysis
    
    Returns:
        List of configuration dictionaries
    """
    configs = []
    for N in N_values:
        for theta in theta_values:
            for seed in seeds:
                config = {
                    "N": N,
                    "theta": theta,
                    "seed": seed,
                    "sparsity_density": 1.0, # Default to dense unless specified
                    "perturbation_type": "diagonal"
                }
                if sparsity_densities:
                    for p in sparsity_densities:
                        config_copy = config.copy()
                        config_copy["sparsity_density"] = p
                        configs.append(config_copy)
                else:
                    configs.append(config)
    return configs

def run_single_sweep_instance(config: Dict[str, Any], paths: Dict[str, Path]) -> Dict[str, Any]:
    """
    Execute a single sweep iteration:
    1. Generate Wigner matrix
    2. Create perturbation
    3. Save raw matrix (T040a logic)
    4. Compute checksum (T040b logic)
    5. Compute eigenvalues
    6. Record results
    
    Args:
        config: Parameter configuration
        paths: Project path dictionary
    
    Returns:
        Result dictionary with metadata and eigenvalues
    """
    N = config["N"]
    theta = config["theta"]
    seed = config["seed"]
    sparsity = config.get("sparsity_density", 1.0)
    
    # Set seed for reproducibility
    np.random.seed(seed)
    
    log_simulation_start(logger, config, "sweep_instance")
    
    try:
        # 1. Generate Wigner Matrix
        W = generate_wigner_matrix(N, seed=seed)
        
        # 2. Create Perturbation
        # Perturbation is rank-1 diagonal with norm theta
        # We use the create_perturbation function from generators.perturbation
        P = create_perturbation(N, theta=theta, sparsity_density=sparsity, seed=seed)
        
        # 3. Combine: H = W + P
        H = W + P
        
        # 4. Save Raw Matrix (T040a logic)
        # Path: data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy
        raw_dir = paths["data_raw"] / "sweep"
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"matrix_N{N}_theta{theta:.1f}_seed{seed}.npy"
        raw_path = raw_dir / filename
        
        np.save(str(raw_path), H)
        logger.info(f"Saved raw matrix to {raw_path}")
        
        # 5. Compute Checksum (T040b logic)
        checksum = compute_file_checksum(raw_path)
        logger.info(f"Computed checksum for {filename}: {checksum}")
        
        # 6. Compute Eigenvalues
        # We need the top eigenvalues to check for outliers
        # Using scipy.sparse.linalg.eigsh for efficiency if sparse, or numpy for dense
        # Since W is dense, H is dense. For N=2000, numpy.linalg.eig is feasible.
        eigenvalues = np.linalg.eigvalsh(H)
        eigenvalues = np.sort(eigenvalues)[::-1] # Descending order
        
        # 7. Record Results
        result = {
            "run_id": f"sweep_{N}_{theta:.1f}_{seed}",
            "N": N,
            "theta": theta,
            "seed": seed,
            "sparsity_density": sparsity,
            "checksum": checksum,
            "max_eigenvalue": float(eigenvalues[0]),
            "second_eigenvalue": float(eigenvalues[1]) if len(eigenvalues) > 1 else None,
            "eigenvalues_top_10": [float(e) for e in eigenvalues[:10]],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        log_simulation_end(logger, result)
        return result
        
    except Exception as e:
        logger.error(f"Error in sweep instance {config}: {e}", exc_info=True)
        raise

def aggregate_sweep_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Aggregate all sweep results into a single JSON file.
    
    Args:
        results: List of result dictionaries
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Aggregated {len(results)} results to {output_path}")

def main():
    """
    Main orchestrator for the parameter sweep.
    """
    # Setup logging
    paths = get_project_paths()
    logger = setup_simulation_logger(paths["data_logs"] / "threshold_sweep.log")
    
    # Define parameter grid
    # N: 1000, 2000 (as per plan)
    # theta: range around the theoretical BBP threshold (theta_c = 1.0 for Wigner, but we look for outliers > 2.0)
    # For Wigner matrices, the edge is at 2.0. The BBP transition for a rank-1 perturbation of norm theta
    # occurs when theta > 1.0 (in the limit N->inf, for Wigner scaled by 1/sqrt(N)).
    # However, the task asks for "plausible values" and verification of outliers > 2.0.
    # We sweep theta from 0.5 to 3.0.
    N_values = [1000, 2000]
    theta_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    seeds = list(range(10)) # 10 iterations per config
    
    configs = generate_sweep_grid(N_values, theta_values, seeds)
    logger.info(f"Generated {len(configs)} sweep configurations")
    
    results = []
    start_time = time.time()
    
    for i, config in enumerate(configs):
        logger.info(f"Running iteration {i+1}/{len(configs)}: N={config['N']}, theta={config['theta']}, seed={config['seed']}")
        try:
            result = run_single_sweep_instance(config, paths)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed iteration {i+1}: {e}")
            # Continue to next iteration
            continue
    
    elapsed = time.time() - start_time
    logger.info(f"Sweep completed in {elapsed:.2f} seconds. Processed {len(results)} successful runs.")
    
    # Save aggregated results
    output_file = paths["data_processed"] / "threshold_sweep_results.json"
    aggregate_sweep_results(results, output_file)
    
    # Save checksum manifest if needed (T040b ensures individual checksums, this is a summary)
    # We can also create a summary CSV for easy plotting later
    if results:
        import csv
        csv_path = paths["data_processed"] / "threshold_sweep_results.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["run_id", "N", "theta", "seed", "max_eigenvalue", "checksum"])
            writer.writeheader()
            for r in results:
                writer.writerow({
                    "run_id": r["run_id"],
                    "N": r["N"],
                    "theta": r["theta"],
                    "seed": r["seed"],
                    "max_eigenvalue": r["max_eigenvalue"],
                    "checksum": r["checksum"]
                })
        logger.info(f"Saved CSV results to {csv_path}")

if __name__ == "__main__":
    main()