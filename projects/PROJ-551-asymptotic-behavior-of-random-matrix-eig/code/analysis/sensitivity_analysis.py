"""
Sparsity Sensitivity Analysis Runner (US3 - T027)

Implements a sensitivity analysis runner that varies support density (sparsity)
while keeping rank fixed, to verify robustness of the critical threshold theta_c.

This script:
1. Generates perturbation matrices with fixed rank but variable support density.
2. Computes eigenvalues and detects outliers.
3. Aggregates results to `data/processed/sensitivity_density_sweep.csv`.
"""

import argparse
import logging
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh
from scipy.optimize import curve_fit

# Import project modules based on provided API surface
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold
from utils.config import get_project_paths, ensure_directories, get_seed
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end

# Configure logging
logger = logging.getLogger(__name__)

# Sigmoid function for threshold fitting (reused from fit_utils logic)
def sigmoid_function(x, a, b, c):
    """Logistic sigmoid for threshold transition."""
    return 1.0 / (1.0 + np.exp(-a * (x - b)))

def run_single_sensitivity_instance(
    N: int,
    rank: int,
    support_density: float,
    theta: float,
    seed: int,
    num_eigenvalues: int = 10
) -> Dict[str, Any]:
    """
    Run a single sensitivity analysis instance.

    Args:
        N: Matrix dimension
        rank: Rank of the perturbation
        support_density: Fraction of non-zero entries in the perturbation support
        theta: Perturbation norm
        seed: Random seed for reproducibility
        num_eigenvalues: Number of top eigenvalues to compute

    Returns:
        Dictionary containing run results.
    """
    np.random.seed(seed)

    # 1. Generate Wigner Matrix
    try:
        W = generate_wigner_matrix(N, seed=seed)
    except Exception as e:
        logger.error(f"Failed to generate Wigner matrix: {e}")
        raise

    # 2. Create Perturbation with specific sparsity
    # The perturbation is rank-k, but we apply a mask to reduce support density
    # We create a dense rank-k perturbation first, then mask it.
    # Note: Masking a low-rank matrix generally increases its rank.
    # To strictly maintain "fixed rank" while varying "support density" as per FR-009,
    # we construct the perturbation such that the non-zero pattern is sparse,
    # but the mathematical rank is preserved via the construction method (e.g., outer products of sparse vectors).
    # However, standard `create_perturbation` might not support density masking directly.
    # We will implement a custom perturbation generator here to ensure rank preservation.

    # Custom sparse rank-k perturbation generation:
    # P = sum_{i=1}^rank (theta_i * u_i * u_i^T) where u_i are sparse vectors
    perturbation = np.zeros((N, N))
    for i in range(rank):
        # Generate a sparse vector with `support_density` non-zeros
        # We want the vector to have exactly k non-zeros where k = N * density
        num_nonzeros = max(1, int(N * support_density))
        indices = np.random.choice(N, size=num_nonzeros, replace=False)
        values = np.random.randn(num_nonzeros)
        values = values / np.linalg.norm(values)  # Normalize

        u = np.zeros(N)
        u[indices] = values

        # Outer product contribution
        perturbation += theta * np.outer(u, u)

    # Symmetrize to ensure numerical stability (should be symmetric by construction)
    perturbation = (perturbation + perturbation.T) / 2.0

    # 3. Form Perturbed Matrix
    H = W + perturbation

    # 4. Compute Top Eigenvalues
    try:
        eigenvalues = compute_top_eigenvalues(H, k=num_eigenvalues, which='LM')
        eigenvalues = np.sort(eigenvalues)[::-1]  # Descending order
    except Exception as e:
        logger.error(f"Eigenvalue computation failed: {e}")
        # Fallback to dense if sparse solver fails (rare for N=2000)
        try:
            eigenvalues = np.linalg.eigvalsh(H)
            eigenvalues = np.sort(eigenvalues)[::-1][:num_eigenvalues]
        except Exception as e2:
            logger.critical(f"Eigenvalue computation failed completely: {e2}")
            raise

    # 5. Validate and Detect Outliers
    bbp_threshold = calculate_bbp_threshold(theta) # Theoretical edge
    # Note: BBP threshold is typically 2 + theta^2/2 or similar depending on normalization.
    # Our `calculate_bbp_threshold` likely returns the theoretical edge.
    # We check if the max eigenvalue exceeds the theoretical bulk edge (2.0) significantly.
    
    outlier_result = detect_outliers(eigenvalues, perturbation_norm=theta)
    
    # 6. Record Results
    result = {
        "N": N,
        "rank": rank,
        "support_density": support_density,
        "theta": theta,
        "seed": seed,
        "max_eigenvalue": float(eigenvalues[0]),
        "eigenvalues": [float(e) for e in eigenvalues],
        "outlier_detected": outlier_result.get("outlier_detected", False),
        "outlier_count": outlier_result.get("count", 0),
        "theoretical_edge": float(bbp_threshold),
        "timestamp": time.time()
    }

    return result

def run_sensitivity_sweep(
    N: int = 2000,
    rank: int = 1,
    densities: List[float] = None,
    theta_values: List[float] = None,
    num_iterations: int = 100,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Run the full sensitivity analysis sweep.

    Args:
        N: Matrix size
        rank: Fixed rank of perturbation
        densities: List of support densities to test (e.g., [0.1, 0.2, 0.3])
        theta_values: List of theta values to test (for phase transition)
        num_iterations: Monte Carlo iterations per configuration
        output_path: Path to save the CSV results

    Returns:
        List of result dictionaries.
    """
    if densities is None:
        densities = [0.1, 0.2, 0.3]
    if theta_values is None:
        # Standard range for BBP transition (theta_c approx 1.0 for rank-1)
        theta_values = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    results = []
    start_time = time.time()

    logger.info(f"Starting Sensitivity Analysis Sweep: N={N}, Rank={rank}")
    logger.info(f"Densities: {densities}, Theta values: {theta_values}")
    logger.info(f"Iterations per config: {num_iterations}")

    for density in densities:
        for theta in theta_values:
            logger.info(f"Running config: density={density}, theta={theta}")
            config_results = []
            
            for i in range(num_iterations):
                seed = get_seed() + int(density * 10000) + int(theta * 1000) + i
                try:
                    res = run_single_sensitivity_instance(
                        N=N,
                        rank=rank,
                        support_density=density,
                        theta=theta,
                        seed=seed
                    )
                    config_results.append(res)
                    results.append(res)
                except Exception as e:
                    logger.warning(f"Iteration {i} failed for density={density}, theta={theta}: {e}")
                    continue

            # Log summary for this config
            if config_results:
                outlier_rate = sum(1 for r in config_results if r["outlier_detected"]) / len(config_results)
                avg_max_eig = np.mean([r["max_eigenvalue"] for r in config_results])
                logger.info(f"  Config ({density}, {theta}): Outlier Rate={outlier_rate:.2f}, Avg Max Eig={avg_max_eig:.4f}")

    elapsed = time.time() - start_time
    logger.info(f"Sensitivity sweep completed in {elapsed:.2f} seconds. Total results: {len(results)}")

    # Save results to CSV
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import csv
        if results:
            with open(output_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)
            logger.info(f"Results saved to {output_path}")
        else:
            logger.warning("No results to save.")

    return results

def main():
    """Main entry point for the sensitivity analysis runner."""
    parser = argparse.ArgumentParser(description="Sparsity Sensitivity Analysis Runner")
    parser.add_argument("--N", type=int, default=2000, help="Matrix dimension")
    parser.add_argument("--rank", type=int, default=1, help="Rank of perturbation")
    parser.add_argument("--densities", type=str, nargs="+", default=["0.1", "0.2", "0.3"],
                        help="Support densities (space separated)")
    parser.add_argument("--thetas", type=str, nargs="+", default=["0.5", "1.0", "1.5", "2.0", "2.5", "3.0"],
                        help="Theta values (space separated)")
    parser.add_argument("--iterations", type=int, default=100, help="Iterations per config")
    parser.add_argument("--output", type=str, default="data/processed/sensitivity_density_sweep.csv",
                        help="Output CSV path")
    
    args = parser.parse_args()

    # Setup
    paths = get_project_paths()
    ensure_directories()
    
    log_file = paths["data_logs"] / "sensitivity_analysis.log"
    setup_simulation_logger("sensitivity_analysis", log_file=str(log_file))
    
    log_simulation_start(
        task_id="T027",
        parameters={
            "N": args.N,
            "rank": args.rank,
            "densities": args.densities,
            "thetas": args.thetas,
            "iterations": args.iterations
        }
    )

    try:
        densities = [float(d) for d in args.densities]
        thetas = [float(t) for t in args.thetas]
        output_path = Path(args.output)

        results = run_sensitivity_sweep(
            N=args.N,
            rank=args.rank,
            densities=densities,
            theta_values=thetas,
            num_iterations=args.iterations,
            output_path=output_path
        )

        log_simulation_end(
            task_id="T027",
            status="success",
            summary={
                "total_runs": len(results),
                "output_file": str(output_path)
            }
        )

    except Exception as e:
        logger.exception("Sensitivity analysis failed")
        log_simulation_end(
            task_id="T027",
            status="failed",
            error=str(e)
        )
        raise

if __name__ == "__main__":
    main()