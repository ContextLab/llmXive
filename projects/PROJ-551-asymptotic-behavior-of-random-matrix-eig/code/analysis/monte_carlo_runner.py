"""
Monte Carlo runner for User Story 2: Phase Transition Threshold Detection.

Executes a sufficient number of iterations per configuration (N, theta)
with random seed management to empirically determine the critical threshold theta_c.

Output: data/processed/mc_results.csv
Schema: run_id, N, theta, seed, outlier_count, max_eigenvalue
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh

# Project imports (matching API surface)
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import calculate_bbp_threshold, detect_outliers
from utils.config import get_project_paths, load_config, get_seed, get_tolerance
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end

# Configure module logger
logger = logging.getLogger(__name__)


def run_single_mc_iteration(
    N: int,
    theta: float,
    seed: int,
    perturbation_type: str = "rank1",
    sparsity_density: float = 1.0
) -> Dict[str, Any]:
    """
    Run a single Monte Carlo iteration:
    1. Generate Wigner matrix W_N (seeded)
    2. Create perturbation P_N (rank-k, sparse if specified)
    3. Compute H = W_N + P_N
    4. Compute top eigenvalues
    5. Detect outliers vs BBP threshold
    6. Return results dict

    Args:
        N: Matrix dimension
        theta: Perturbation norm (spectral norm of P_N)
        seed: Random seed for reproducibility
        perturbation_type: Type of perturbation ("rank1", "block", "sparse")
        sparsity_density: Fraction of non-zero entries in perturbation mask (0.0 to 1.0)

    Returns:
        Dict with keys: run_id, N, theta, seed, outlier_count, max_eigenvalue, timestamp
    """
    run_id = f"mc_{N}_{theta}_{seed}"
    start_time = datetime.now(timezone.utc)

    try:
        # Set seed for reproducibility
        np.random.seed(seed)

        # 1. Generate Wigner matrix
        logger.debug(f"[{run_id}] Generating {N}x{N} Wigner matrix with seed {seed}")
        W = generate_wigner_matrix(N, seed=seed)

        # 2. Create perturbation
        logger.debug(f"[{run_id}] Creating {perturbation_type} perturbation with theta={theta}, density={sparsity_density}")
        P = create_perturbation(
            N=N,
            theta=theta,
            rank=1,  # Default to rank-1 for BBP threshold analysis
            perturbation_type=perturbation_type,
            sparsity_density=sparsity_density,
            seed=seed
        )

        # 3. Construct Hamiltonian H = W + P
        H = W + P

        # 4. Compute top eigenvalues (use iterative solver for large N)
        # We need at least the top 1 eigenvalue to check for outliers
        num_eigenvalues = min(10, N)
        logger.debug(f"[{run_id}] Computing top {num_eigenvalues} eigenvalues")
        
        try:
            eigenvalues, _ = compute_top_eigenvalues(H, k=num_eigenvalues, which='LM')
            eigenvalues = np.sort(eigenvalues)[::-1]  # Sort descending
        except Exception as e:
            logger.error(f"[{run_id}] Eigenvalue computation failed: {e}")
            raise

        # 5. Validate and detect outliers
        bbp_threshold = calculate_bbp_threshold(theta)
        outlier_result = detect_outliers(eigenvalues, bbp_threshold)

        max_eigenvalue = float(eigenvalues[0]) if len(eigenvalues) > 0 else 0.0
        outlier_count = outlier_result.outlier_count

        end_time = datetime.now(timezone.utc)
        
        result = {
            "run_id": run_id,
            "N": N,
            "theta": float(theta),
            "seed": seed,
            "outlier_count": int(outlier_count),
            "max_eigenvalue": max_eigenvalue,
            "bbp_threshold": float(bbp_threshold),
            "has_outlier": bool(outlier_count > 0),
            "timestamp_start": start_time.isoformat(),
            "timestamp_end": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds()
        }

        logger.info(f"[{run_id}] Completed: max_eig={max_eigenvalue:.4f}, outlier_count={outlier_count}, theta_c={bbp_threshold:.4f}")
        return result

    except Exception as e:
        logger.error(f"[{run_id}] Iteration failed with error: {e}")
        # Re-raise to fail loudly - no synthetic fallback
        raise


def run_monte_carlo_sweep(
    configs: List[Dict[str, Any]],
    num_iterations: int = 100,
    output_path: Optional[str] = None,
    perturbation_type: str = "rank1",
    sparsity_density: float = 1.0
) -> Path:
    """
    Run Monte Carlo sweep over a list of (N, theta) configurations.
    Each configuration is run `num_iterations` times with different seeds.

    Args:
        configs: List of dicts with keys 'N', 'theta'
        num_iterations: Number of Monte Carlo iterations per configuration
        output_path: Path to output CSV file (default: data/processed/mc_results.csv)
        perturbation_type: Type of perturbation to apply
        sparsity_density: Sparsity density for perturbation mask

    Returns:
        Path to the output CSV file
    """
    paths = get_project_paths()
    if output_path is None:
        output_path = str(paths["processed"] / "mc_results.csv")
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Monte Carlo sweep with {len(configs)} configurations, {num_iterations} iterations each")
    logger.info(f"Output will be written to: {output_file}")

    # Check if file exists and has headers
    file_exists = output_file.exists()
    fieldnames = ["run_id", "N", "theta", "seed", "outlier_count", "max_eigenvalue", 
                 "bbp_threshold", "has_outlier", "timestamp_start", "timestamp_end", "duration_seconds"]

    total_runs = len(configs) * num_iterations
    completed_runs = 0

    with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        for config in configs:
            N = config["N"]
            theta = config["theta"]
            
            logger.info(f"Configuration: N={N}, theta={theta}, iterations={num_iterations}")

            for i in range(num_iterations):
                # Generate deterministic seed based on config index and iteration
                base_seed = get_seed()
                iteration_seed = base_seed + hash((N, theta, i)) % (2**31 - 1)
                
                try:
                    result = run_single_mc_iteration(
                        N=N,
                        theta=theta,
                        seed=iteration_seed,
                        perturbation_type=perturbation_type,
                        sparsity_density=sparsity_density
                    )
                    
                    # Only write the required schema columns for the CSV
                    row = {
                        "run_id": result["run_id"],
                        "N": result["N"],
                        "theta": result["theta"],
                        "seed": result["seed"],
                        "outlier_count": result["outlier_count"],
                        "max_eigenvalue": result["max_eigenvalue"]
                    }
                    writer.writerow(row)
                    
                    completed_runs += 1
                    logger.debug(f"Progress: {completed_runs}/{total_runs} ({100*completed_runs/total_runs:.1f}%)")
                    
                except Exception as e:
                    logger.error(f"Failed iteration {i+1}/{num_iterations} for N={N}, theta={theta}: {e}")
                    # Fail loudly - do not skip or use synthetic data
                    raise

    logger.info(f"Monte Carlo sweep completed. {completed_runs} runs written to {output_file}")
    return output_file


def generate_mc_configs(
    N_values: List[int] = [500, 1000, 2000],
    theta_values: List[float] = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
) -> List[Dict[str, Any]]:
    """
    Generate a grid of (N, theta) configurations for the Monte Carlo sweep.

    Args:
        N_values: List of matrix dimensions to test
        theta_values: List of perturbation norms to test

    Returns:
        List of configuration dicts
    """
    configs = []
    for N in N_values:
        for theta in theta_values:
            configs.append({"N": N, "theta": theta})
    return configs


def main():
    """Main entry point for Monte Carlo runner."""
    parser = argparse.ArgumentParser(
        description="Run Monte Carlo simulation to detect phase transition threshold"
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Path to JSON config file with custom N and theta values"
    )
    parser.add_argument(
        "--num-iterations",
        type=int,
        default=50,
        help="Number of Monte Carlo iterations per configuration (default: 50)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output CSV file path (default: data/processed/mc_results.csv)"
    )
    parser.add_argument(
        "--perturbation-type",
        type=str,
        default="rank1",
        choices=["rank1", "block", "sparse"],
        help="Type of perturbation (default: rank1)"
    )
    parser.add_argument(
        "--sparsity-density",
        type=float,
        default=1.0,
        help="Sparsity density for perturbation mask (default: 1.0)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup logging
    log_file = get_project_paths()["logs"] / "monte_carlo_run.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    setup_simulation_logger(log_file, level=getattr(logging, args.log_level.upper()))

    log_simulation_start("Monte Carlo Sweep", {
        "num_iterations": args.num_iterations,
        "perturbation_type": args.perturbation_type,
        "sparsity_density": args.sparsity_density
    })

    try:
        # Load or generate configurations
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")
            
            with open(config_path, 'r') as f:
                custom_config = json.load(f)
            
            N_values = custom_config.get("N_values", [500, 1000, 2000])
            theta_values = custom_config.get("theta_values", [1.0, 1.5, 2.0, 2.5, 3.0])
        else:
            # Default configurations for US2
            N_values = [1000]  # Focus on one N for initial sweep
            theta_values = [1.5, 2.0, 2.5, 3.0]  # Range around expected theta_c = 2.0

        configs = generate_mc_configs(N_values, theta_values)

        if not configs:
            raise ValueError("No configurations provided. Check --config or defaults.")

        logger.info(f"Generated {len(configs)} configurations for Monte Carlo sweep")

        # Run the sweep
        output_path = run_monte_carlo_sweep(
            configs=configs,
            num_iterations=args.num_iterations,
            output_path=args.output,
            perturbation_type=args.perturbation_type,
            sparsity_density=args.sparsity_density
        )

        log_simulation_end("Monte Carlo Sweep", {
            "status": "success",
            "output_file": str(output_path),
            "total_configs": len(configs),
            "iterations_per_config": args.num_iterations
        })

        print(f"Monte Carlo sweep completed successfully.")
        print(f"Results written to: {output_path}")
        return 0

    except Exception as e:
        logger.exception(f"Monte Carlo sweep failed: {e}")
        log_simulation_end("Monte Carlo Sweep", {
            "status": "failed",
            "error": str(e)
        })
        return 1


if __name__ == "__main__":
    sys.exit(main())