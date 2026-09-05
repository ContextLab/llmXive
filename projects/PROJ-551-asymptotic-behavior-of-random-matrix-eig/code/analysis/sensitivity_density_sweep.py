"""
Task T028: Execute sensitivity analysis sweep over support density.

Sweeps support density {0.1, 0.2, 0.3} for each sparsity pattern type
(diagonal, block-sparse, random sparse) and outputs results to
data/processed/sensitivity_density_sweep.csv.
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import numpy as np
from scipy import sparse

# Project imports
from utils.config import get_project_paths, get_seed, get_matrix_size, get_tolerance
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end

# Constants
DENSITIES = [0.1, 0.2, 0.3]
SPARSITY_PATTERNS = ["diagonal", "block-sparse", "random-sparse"]
# Fixed perturbation strength for sensitivity analysis of density
THETA_FIXED = 2.5
RANK_FIXED = 1

def run_single_density_instance(
    density: float,
    pattern: str,
    N: int,
    theta: float,
    seed: int,
    rank: int = 1,
    tol: float = 1e-10
) -> Dict[str, Any]:
    """
    Run a single simulation instance for a given density and pattern.

    Returns a dictionary with the results.
    """
    # 1. Generate Wigner Matrix
    np.random.seed(seed)
    W = generate_wigner_matrix(N)

    # 2. Create Perturbation
    # Perturbation config: rank, density (sparsity), pattern
    perturbation = create_perturbation(
        N=N,
        rank=rank,
        pattern=pattern,
        density=density,
        theta=theta
    )

    # 3. Construct Perturbed Matrix
    H = W + perturbation

    # 4. Compute Eigenvalues
    # We need the top eigenvalues to check for outliers
    try:
        eigenvalues = compute_top_eigenvalues(H, k=10, which='LM')
        # Sort descending
        eigenvalues = sorted(eigenvalues, reverse=True)
    except Exception as e:
        logging.error(f"Eigenvalue computation failed: {e}")
        return {
            "density": density,
            "pattern": pattern,
            "theta": theta,
            "N": N,
            "seed": seed,
            "rank": rank,
            "success": False,
            "error": str(e),
            "outlier_detected": False,
            "max_eigenvalue": None,
            "bbp_threshold": None,
            "transition_candidate": False
        }

    # 5. Detect Outliers
    bbp_edge = 2.0 # Theoretical edge for Wigner
    bbp_threshold_val = calculate_bbp_threshold(theta, rank=rank)
    
    outlier_result = detect_outliers(
        eigenvalues=eigenvalues,
        theta=theta,
        rank=rank,
        tol=tol
    )

    return {
        "density": density,
        "pattern": pattern,
        "theta": theta,
        "N": N,
        "seed": seed,
        "rank": rank,
        "success": True,
        "outlier_detected": outlier_result.outlier_detected,
        "max_eigenvalue": float(eigenvalues[0]) if eigenvalues else None,
        "bbp_threshold": float(bbp_threshold_val),
        "transition_candidate": outlier_result.transition_candidate
    }

def run_sensitivity_density_sweep(
    densities: List[float],
    patterns: List[str],
    N: int,
    theta: float,
    base_seed: int,
    rank: int = 1,
    tol: float = 1e-10,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Execute the full sensitivity sweep.
    """
    if output_path is None:
        paths = get_project_paths()
        output_path = paths / "data" / "processed" / "sensitivity_density_sweep.csv"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)

    results = []
    seed_counter = base_seed

    logging.info(f"Starting sensitivity density sweep for N={N}, theta={theta}")
    logging.info(f"Densities: {densities}, Patterns: {patterns}")

    for density in densities:
        for pattern in patterns:
            # Run multiple seeds for statistical robustness? 
            # Task description implies a sweep, usually one run per config or a few.
            # We will run 3 seeds per configuration to get a sense of variance, 
            # but the primary output is the CSV of these runs.
            # Or strictly one per config as per "Execute sweep over...". 
            # Let's do 3 seeds to make it a real study, but record all.
            num_seeds = 3 
            for i in range(num_seeds):
                seed = seed_counter + i
                logging.info(f"Running: density={density}, pattern={pattern}, seed={seed}")
                
                try:
                    res = run_single_density_instance(
                        density=density,
                        pattern=pattern,
                        N=N,
                        theta=theta,
                        seed=seed,
                        rank=rank,
                        tol=tol
                    )
                    results.append(res)
                except Exception as e:
                    logging.error(f"Failed instance (d={density}, p={pattern}, s={seed}): {e}")
                    results.append({
                        "density": density,
                        "pattern": pattern,
                        "theta": theta,
                        "N": N,
                        "seed": seed,
                        "rank": rank,
                        "success": False,
                        "error": str(e),
                        "outlier_detected": False,
                        "max_eigenvalue": None,
                        "bbp_threshold": None,
                        "transition_candidate": False
                    })
            
            seed_counter += num_seeds

    # Write to CSV
    fieldnames = [
        "density", "pattern", "theta", "N", "seed", "rank", "success",
        "outlier_detected", "max_eigenvalue", "bbp_threshold", "transition_candidate", "error"
    ]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

    logging.info(f"Sweep complete. Results written to {output_path}")
    return results

def main():
    parser = argparse.ArgumentParser(description="Task T028: Sensitivity Density Sweep")
    parser.add_argument("--N", type=int, help="Matrix size N")
    parser.add_argument("--theta", type=float, default=2.5, help="Perturbation strength")
    parser.add_argument("--seed", type=int, default=42, help="Base seed")
    parser.add_argument("--rank", type=int, default=1, help="Perturbation rank")
    parser.add_argument("--output", type=str, help="Output CSV path")
    parser.add_argument("--tol", type=float, default=1e-10, help="Tolerance")
    
    args = parser.parse_args()

    # Load config or use defaults
    N = args.N if args.N else get_matrix_size()
    theta = args.theta
    seed = args.seed
    rank = args.rank
    tol = args.tol
    output_path = Path(args.output) if args.output else None

    # Setup logging
    log_path = Path("data/logs/sensitivity_density_sweep.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    setup_simulation_logger("sensitivity_density_sweep", log_file=log_path)

    log_simulation_start(
        task="T028",
        parameters={"N": N, "theta": theta, "densities": DENSITIES, "patterns": SPARSITY_PATTERNS}
    )

    try:
        results = run_sensitivity_density_sweep(
            densities=DENSITIES,
            patterns=SPARSITY_PATTERNS,
            N=N,
            theta=theta,
            base_seed=seed,
            rank=rank,
            tol=tol,
            output_path=output_path
        )
        log_simulation_end(success=True, results_count=len(results))
    except Exception as e:
        logging.critical(f"Sweep failed: {e}")
        log_simulation_end(success=False, error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
