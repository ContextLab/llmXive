"""
Sensitivity Density Sweep Implementation (Task T028).

Executes a sweep over support density values {0.1, 0.2, 0.3} for each sparsity pattern
type defined in the project. Outputs results to data/processed/sensitivity_density_sweep.csv.

This script generates raw Wigner matrices, applies sparse perturbations with varying
densities, computes eigenvalues, and records the results. It relies on existing
generators and analysis utilities.
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

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.config import get_project_paths, ensure_directories, get_seed
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end

# Constants for the sweep
SUPPORT_DENSITIES = [0.1, 0.2, 0.3]
SPARSITY_PATTERNS = ["diagonal", "block-sparse", "random-sparse"]
MATRIX_SIZE = 1000  # Default N for sensitivity analysis
NUM_EIGENVALUES = 10
PERTURBATION_NORM = 2.5  # Fixed theta for sensitivity to density
NUM_ITERATIONS = 5  # Number of Monte Carlo iterations per configuration

logger = logging.getLogger(__name__)

def run_single_density_instance(
    N: int,
    density: float,
    pattern: str,
    theta: float,
    seed: int,
    num_eigenvalues: int = 10
) -> Dict[str, Any]:
    """
    Run a single instance of the sensitivity analysis.

    Args:
        N: Matrix dimension
        density: Support density (sparsity level)
        pattern: Sparsity pattern type
        theta: Perturbation norm
        seed: Random seed for reproducibility
        num_eigenvalues: Number of top eigenvalues to compute

    Returns:
        Dictionary containing run parameters and results
    """
    run_id = f"sens_N{N}_d{density:.1f}_p{pattern}_s{seed}"
    log_path = get_project_paths()["logs"]
    logger.info(f"Starting run: {run_id}, density={density}, pattern={pattern}, theta={theta}")

    # Generate Wigner matrix
    np.random.seed(seed)
    W = generate_wigner_matrix(N, seed=seed)

    # Create perturbation with specific density and pattern
    P = create_perturbation(
        N=N,
        rank=1,  # Fixed rank for this sensitivity study
        density=density,
        pattern=pattern,
        theta=theta,
        seed=seed + 1000  # Offset seed for perturbation
    )

    # Construct perturbed matrix
    H = W + P

    # Compute top eigenvalues
    try:
        eigenvalues = compute_top_eigenvalues(H, k=num_eigenvalues, which='LM')
    except Exception as e:
        logger.error(f"Eigenvalue computation failed for {run_id}: {e}")
        raise

    # Detect outliers
    bbp_threshold = calculate_bbp_threshold(theta)
    outlier_result = detect_outliers(eigenvalues, bbp_threshold)

    # Record results
    result = {
        "run_id": run_id,
        "N": N,
        "density": density,
        "pattern": pattern,
        "theta": theta,
        "seed": seed,
        "max_eigenvalue": float(eigenvalues[0]) if len(eigenvalues) > 0 else None,
        "outlier_count": outlier_result.outlier_count,
        "outlier_flag": outlier_result.has_outlier,
        "bbp_threshold": float(bbp_threshold),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    logger.info(f"Completed run: {run_id}, max_eigenvalue={result['max_eigenvalue']:.4f}, outlier={result['outlier_flag']}")
    return result

def run_sensitivity_density_sweep(
    output_path: Optional[str] = None,
    N: int = MATRIX_SIZE,
    densities: Optional[List[float]] = None,
    patterns: Optional[List[str]] = None,
    theta: float = PERTURBATION_NORM,
    num_iterations: int = NUM_ITERATIONS,
    base_seed: int = None
) -> List[Dict[str, Any]]:
    """
    Execute the full sensitivity density sweep.

    Args:
        output_path: Path to output CSV file
        N: Matrix dimension
        densities: List of support densities to sweep
        patterns: List of sparsity patterns to test
        theta: Perturbation norm
        num_iterations: Number of iterations per configuration
        base_seed: Base random seed for the sweep

    Returns:
        List of result dictionaries
    """
    if densities is None:
        densities = SUPPORT_DENSITIES
    if patterns is None:
        patterns = SPARSITY_PATTERNS
    if base_seed is None:
        base_seed = get_seed()

    # Ensure output directory exists
    paths = get_project_paths()
    ensure_directories([paths["processed"]])
    if output_path is None:
        output_path = str(paths["processed"] / "sensitivity_density_sweep.csv")

    logger.info(f"Starting sensitivity density sweep: N={N}, densities={densities}, patterns={patterns}, theta={theta}")
    log_simulation_start("sensitivity_density_sweep", {
        "N": N,
        "densities": densities,
        "patterns": patterns,
        "theta": theta,
        "num_iterations": num_iterations,
        "base_seed": base_seed
    })

    all_results = []
    current_seed = base_seed

    for density in densities:
        for pattern in patterns:
            logger.info(f"Sweeping density={density}, pattern={pattern}")
            for i in range(num_iterations):
                try:
                    result = run_single_density_instance(
                        N=N,
                        density=density,
                        pattern=pattern,
                        theta=theta,
                        seed=current_seed,
                        num_eigenvalues=NUM_EIGENVALUES
                    )
                    all_results.append(result)
                    current_seed += 1
                except Exception as e:
                    logger.error(f"Failed iteration {i+1}/{num_iterations} for density={density}, pattern={pattern}: {e}")
                    # Continue with next iteration
                    current_seed += 1
                    continue

    # Write results to CSV
    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        logger.info(f"Wrote {len(all_results)} results to {output_path}")
    else:
        logger.warning("No results were generated for the sweep.")

    log_simulation_end("sensitivity_density_sweep", len(all_results))
    return all_results

def main():
    """Main entry point for the sensitivity density sweep."""
    parser = argparse.ArgumentParser(description="Sensitivity Density Sweep for Sparse Perturbations")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--N", type=int, default=MATRIX_SIZE, help="Matrix dimension")
    parser.add_argument("--theta", type=float, default=PERTURBATION_NORM, help="Perturbation norm")
    parser.add_argument("--iterations", type=int, default=NUM_ITERATIONS, help="Iterations per config")
    parser.add_argument("--seed", type=int, default=None, help="Base random seed")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])

    args = parser.parse_args()

    # Setup logging
    log_path = get_project_paths()["logs"]
    ensure_directories([log_path])
    log_file = str(Path(log_path) / "sensitivity_density_sweep.log")
    setup_simulation_logger("sensitivity_density_sweep", log_file, level=args.log_level)

    try:
        results = run_sensitivity_density_sweep(
            output_path=args.output,
            N=args.N,
            theta=args.theta,
            num_iterations=args.iterations,
            base_seed=args.seed
        )
        print(f"Sensitivity density sweep completed. Results written to: {args.output or get_project_paths()['processed'] / 'sensitivity_density_sweep.csv'}")
    except Exception as e:
        logger.exception(f"Sensitivity density sweep failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
