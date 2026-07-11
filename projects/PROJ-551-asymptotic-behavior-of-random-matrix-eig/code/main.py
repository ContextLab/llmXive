"""
Main entry point for the random matrix eigenvalue simulation.
Implements single-run mode with structured logging for reproducibility.
"""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from data_models import PerturbationConfig, SimulationRun
from generators.perturbation import create_perturbation
from generators.wigner import generate_wigner_matrix
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import detect_outliers
from utils.config import get_project_paths, load_config, get_seed
from utils.logging_config import (
    setup_simulation_logger,
    log_simulation_start,
    log_simulation_end,
    log_eigenvalue_results,
)
from utils.results_logger import record_simulation_result


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run random matrix eigenvalue simulation with sparse perturbations"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility (overrides config)",
    )
    parser.add_argument(
        "--matrix-size",
        type=int,
        default=None,
        help="Matrix size N (overrides config)",
    )
    parser.add_argument(
        "--perturbation-norm",
        type=float,
        default=None,
        help="Perturbation norm theta (overrides config)",
    )
    parser.add_argument(
        "--sparsity-density",
        type=float,
        default=None,
        help="Sparsity density p (overrides config)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override with command line arguments if provided
    seed = args.seed if args.seed is not None else config.get("seed", 42)
    matrix_size = args.matrix_size if args.matrix_size is not None else config.get("matrix_size", 1000)
    perturbation_norm = args.perturbation_norm if args.perturbation_norm is not None else config.get("perturbation_norm", 2.5)
    sparsity_density = args.sparsity_density if args.sparsity_density is not None else config.get("sparsity_density", 0.1)

    # Set random seeds for reproducibility
    np.random.seed(seed)
    random_state = np.random.RandomState(seed)

    seed_state = {
        "numpy": seed,
        "python": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Setup structured logging
    log_level = getattr(logging, args.log_level.upper())
    logger = setup_simulation_logger(seed_state=seed_state, log_level=log_level)

    # Generate unique run ID
    run_id = f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{seed}"

    # Log simulation start
    params = {
        "matrix_size": matrix_size,
        "perturbation_norm": perturbation_norm,
        "sparsity_density": sparsity_density,
        "seed": seed,
        "run_id": run_id,
    }
    log_simulation_start(logger, params, seed_state, run_id)

    start_time = time.time()

    try:
        # Generate Wigner matrix
        logging.info(f"Generating {matrix_size}x{matrix_size} Wigner matrix with seed {seed}")
        wigner_matrix = generate_wigner_matrix(matrix_size, seed=seed)

        # Create perturbation matrix
        perturbation_config = PerturbationConfig(
            norm=perturbation_norm,
            sparsity_density=sparsity_density,
            rank=1,
            pattern="diagonal",
        )
        perturbation_matrix = create_perturbation(
            matrix_size, perturbation_config, random_state=random_state
        )

        # Combine matrices
        perturbed_matrix = wigner_matrix + perturbation_matrix

        # Compute top eigenvalues
        num_eigenvalues = min(10, matrix_size)
        eigenvalues, eigenvectors = compute_top_eigenvalues(
            perturbed_matrix, k=num_eigenvalues, which="LA"
        )

        # Validate eigenvalues
        validation_result = validate_eigenvalues(eigenvalues, matrix_size)
        if not validation_result["is_valid"]:
            logger.warning(f"Eigenvalue validation failed: {validation_result['message']}")

        # Detect outliers
        outlier_result = detect_outliers(
            eigenvalues, perturbation_norm, matrix_size
        )

        # Log eigenvalue results
        log_eigenvalue_results(
            logger,
            eigenvalues.tolist(),
            outlier_result["outlier_indices"].tolist(),
            perturbation_norm,
            matrix_size,
            run_id,
        )

        # Record results
        simulation_run = SimulationRun(
            run_id=run_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            matrix_size=matrix_size,
            perturbation_norm=perturbation_norm,
            sparsity_density=sparsity_density,
            seed=seed,
            eigenvalues=eigenvalues.tolist(),
            outlier_indices=outlier_result["outlier_indices"].tolist(),
            has_outlier=outlier_result["has_outlier"],
            bbp_threshold=outlier_result["bbp_threshold"],
            validation_passed=validation_result["is_valid"],
        )

        record_simulation_result(simulation_run)

        duration = time.time() - start_time
        log_simulation_end(logger, "success", duration, run_id)

        print(f"Simulation completed successfully. Run ID: {run_id}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Top eigenvalue: {eigenvalues[0]:.6f}")
        print(f"Has outlier: {outlier_result['has_outlier']}")
        print(f"Log file: data/logs/simulation_run.log")

        return 0

    except Exception as e:
        duration = time.time() - start_time
        log_simulation_end(logger, "failed", duration, run_id)
        logger.error(f"Simulation failed: {str(e)}", exc_info=True)
        print(f"Simulation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())