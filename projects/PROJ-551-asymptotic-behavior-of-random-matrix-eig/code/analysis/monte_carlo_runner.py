import argparse
import logging
import os
import sys
import time
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Project imports
from utils.config import get_project_paths, get_num_mc_iterations, get_seed
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold

# Setup logger
logger = logging.getLogger(__name__)

def run_single_mc_iteration(
    N: int,
    theta: float,
    seed: int,
    rank: int = 1,
    sparsity_density: float = 1.0,
    num_eigenvalues: int = 10
) -> Dict[str, Any]:
    """
    Execute a single Monte Carlo iteration.
    
    Returns a dictionary with:
      - run_id: str
      - N: int
      - theta: float
      - seed: int
      - outlier_count: int
      - max_eigenvalue: float
    """
    run_id = f"mc_N{N}_t{theta}_s{seed}"
    logger.info(f"Starting iteration: {run_id}")

    try:
        # 1. Generate Wigner matrix
        W = generate_wigner_matrix(N, seed=seed)
        
        # 2. Create perturbation
        P = create_perturbation(N, theta, rank=rank, sparsity_density=sparsity_density)
        
        # 3. Construct perturbed matrix H = W + P
        H = W + P
        
        # 4. Compute top eigenvalues
        # We need enough eigenvalues to detect outliers if they exist.
        # BBP theory suggests outliers appear near theta + 1/theta for theta > 1.
        # For theta ~ 2.5, outlier ~ 2.9. Bulk edge is 2.0.
        # We compute top 10 to be safe.
        eigenvalues, _ = compute_top_eigenvalues(H, k=num_eigenvalues)
        
        if len(eigenvalues) == 0:
            logger.warning(f"No eigenvalues computed for {run_id}. Skipping.")
            return {
                "run_id": run_id,
                "N": N,
                "theta": theta,
                "seed": seed,
                "outlier_count": 0,
                "max_eigenvalue": 0.0
            }

        # 5. Validate eigenvalues
        # Validate against semicircle edge (2.0)
        is_valid, issues = validate_eigenvalues(eigenvalues)
        if not is_valid:
            logger.warning(f"Validation issues for {run_id}: {issues}")
            # Continue anyway, but log

        # 6. Detect outliers
        # BBP threshold for theta
        bbp_edge = calculate_bbp_threshold(theta)
        outlier_result = detect_outliers(eigenvalues, bbp_threshold=bbp_edge)
        
        outlier_count = len(outlier_result.outliers)
        max_eig = float(eigenvalues[0]) if len(eigenvalues) > 0 else 0.0

        logger.info(
            f"Completed {run_id}: max_eig={max_eig:.4f}, "
            f"bbp_edge={bbp_edge:.4f}, outliers={outlier_count}"
        )

        return {
            "run_id": run_id,
            "N": N,
            "theta": theta,
            "seed": seed,
            "outlier_count": outlier_count,
            "max_eigenvalue": max_eig
        }

    except Exception as e:
        logger.error(f"Error in iteration {run_id}: {e}", exc_info=True)
        # Return failure record
        return {
            "run_id": run_id,
            "N": N,
            "theta": theta,
            "seed": seed,
            "outlier_count": -1,  # Error marker
            "max_eigenvalue": 0.0
        }

def run_monte_carlo_sweep(
    N_values: List[int],
    theta_values: List[float],
    num_iterations_per_config: int,
    output_path: str,
    rank: int = 1,
    sparsity_density: float = 1.0,
    num_eigenvalues: int = 10,
    base_seed: int = 42
) -> List[Dict[str, Any]]:
    """
    Run Monte Carlo sweep over N and theta.
    
    Args:
        N_values: List of matrix sizes
        theta_values: List of perturbation strengths
        num_iterations_per_config: Number of MC iterations per (N, theta) pair
        output_path: Path to write results CSV
        rank: Rank of perturbation
        sparsity_density: Density of perturbation support
        num_eigenvalues: Number of top eigenvalues to compute
        base_seed: Base seed for random seed generation
    
    Returns:
        List of result dictionaries
    """
    paths = get_project_paths()
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    results = []
    start_time = time.time()
    iteration = 0

    logger.info(f"Starting Monte Carlo sweep: {len(N_values)} N values, "
                f"{len(theta_values)} theta values, "
                f"{num_iterations_per_config} iterations/config")

    # Prepare CSV header
    header = ["run_id", "N", "theta", "seed", "outlier_count", "max_eigenvalue"]

    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

        for N in N_values:
            for theta in theta_values:
                logger.info(f"Processing config: N={N}, theta={theta}")
                
                for i in range(num_iterations_per_config):
                    # Generate deterministic seed for this iteration
                    # Use a hash-like combination to ensure uniqueness and reproducibility
                    seed = base_seed + iteration * 1000 + i
                    
                    result = run_single_mc_iteration(
                        N=N,
                        theta=theta,
                        seed=seed,
                        rank=rank,
                        sparsity_density=sparsity_density,
                        num_eigenvalues=num_eigenvalues
                    )
                    
                    results.append(result)
                    writer.writerow([
                        result["run_id"],
                        result["N"],
                        result["theta"],
                        result["seed"],
                        result["outlier_count"],
                        result["max_eigenvalue"]
                    ])
                    
                    iteration += 1

    elapsed = time.time() - start_time
    logger.info(f"Monte Carlo sweep completed in {elapsed:.2f}s. "
                f"Total iterations: {iteration}")
    logger.info(f"Results written to {output_file}")

    return results

def main():
    """Main entry point for Monte Carlo runner."""
    parser = argparse.ArgumentParser(
        description="Monte Carlo runner for random matrix eigenvalue analysis"
    )
    parser.add_argument(
        "--n-values",
        type=int,
        nargs="+",
        default=[500, 1000, 2000],
        help="Matrix sizes to test"
    )
    parser.add_argument(
        "--theta-values",
        type=float,
        nargs="+",
        default=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
        help="Perturbation strengths to test"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of Monte Carlo iterations per configuration"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV path (default: data/processed/mc_results.csv)"
    )
    parser.add_argument(
        "--rank",
        type=int,
        default=1,
        help="Rank of perturbation"
    )
    parser.add_argument(
        "--sparsity",
        type=float,
        default=1.0,
        help="Sparsity density of perturbation"
    )
    parser.add_argument(
        "--num-eigenvalues",
        type=int,
        default=10,
        help="Number of top eigenvalues to compute"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Base random seed"
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="data/logs/monte_carlo_runner.log",
        help="Log file path"
    )

    args = parser.parse_args()

    # Setup logging
    log_path = Path(args.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger.info("Starting Monte Carlo Runner")
    logger.info(f"Args: {vars(args)}")

    # Determine output path
    if args.output is None:
        paths = get_project_paths()
        output_path = str(paths["processed"] / "mc_results.csv")
    else:
        output_path = args.output

    # Run sweep
    results = run_monte_carlo_sweep(
        N_values=args.n_values,
        theta_values=args.theta_values,
        num_iterations_per_config=args.iterations,
        output_path=output_path,
        rank=args.rank,
        sparsity_density=args.sparsity,
        num_eigenvalues=args.num_eigenvalues,
        base_seed=args.seed
    )

    logger.info(f"Completed. Total results: {len(results)}")
    return results

if __name__ == "__main__":
    main()
