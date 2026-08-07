import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime

from utils.config import (
    get_project_paths,
    get_seed,
    get_tolerance,
    get_matrix_size,
    get_num_eigenvalues,
    get_perturbation_norm,
    get_sparsity_density,
)
from utils.logging_config import (
    setup_simulation_logger,
    log_simulation_start,
    log_simulation_end,
    log_eigenvalue_results,
)
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues
from analysis.outlier_detect import detect_outliers
from utils.results_logger import record_simulation_result

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a single simulation of perturbed Wigner matrices."
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--size", type=int, default=None, help="Matrix dimension N"
    )
    parser.add_argument(
        "--theta", type=float, default=None, help="Perturbation norm"
    )
    parser.add_argument(
        "--perturbation-type",
        type=str,
        default="diagonal",
        choices=["diagonal", "block_sparse", "random_sparse"],
        help="Type of perturbation",
    )
    parser.add_argument(
        "--sparsity-density",
        type=float,
        default=None,
        help="Sparsity density for sparse perturbations",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Path to structured JSON log file",
    )
    return parser.parse_args()

def main():
    args = parse_args()

    # Initialize configuration
    paths = get_project_paths()
    seed = args.seed if args.seed is not None else get_seed()
    matrix_size = args.size if args.size is not None else get_matrix_size()
    perturbation_norm = (
        args.theta if args.theta is not None else get_perturbation_norm()
    )
    num_eigenvalues = get_num_eigenvalues()
    sparsity_density = (
        args.sparsity_density
        if args.sparsity_density is not None
        else get_sparsity_density()
    )

    # Setup structured logging
    logger = setup_simulation_logger(log_file_path=args.log_file)

    start_time = time.time()

    # Log simulation start with full reproducibility context
    log_simulation_start(
        logger=logger,
        seed=seed,
        matrix_size=matrix_size,
        perturbation_norm=perturbation_norm,
        perturbation_type=args.perturbation_type,
        sparsity_density=sparsity_density,
        num_eigenvalues=num_eigenvalues,
        config_path=str(paths["config"]),
    )

    try:
        # Generate Wigner matrix
        wigner_matrix = generate_wigner_matrix(matrix_size, seed=seed)

        # Create perturbation
        perturbation_matrix = create_perturbation(
            matrix_size,
            perturbation_norm,
            perturbation_type=args.perturbation_type,
            sparsity_density=sparsity_density,
            seed=seed + 1,
        )

        # Combine matrices
        perturbed_matrix = wigner_matrix + perturbation_matrix

        # Compute top eigenvalues
        eigenvalues = compute_top_eigenvalues(
            perturbed_matrix, k=num_eigenvalues, tol=get_tolerance()
        )

        # Detect outliers
        outlier_result = detect_outliers(
            eigenvalues, perturbation_norm, perturbation_type=args.perturbation_type
        )

        # Log eigenvalue results
        log_eigenvalue_results(
            logger=logger,
            eigenvalues=eigenvalues,
            outlier_indices=outlier_result.outlier_indices,
            theoretical_edge=outlier_result.theoretical_edge,
        )

        # Record results to data/processed
        record_simulation_result(
            seed=seed,
            matrix_size=matrix_size,
            perturbation_norm=perturbation_norm,
            perturbation_type=args.perturbation_type,
            sparsity_density=sparsity_density,
            eigenvalues=eigenvalues,
            outlier_indices=outlier_result.outlier_indices,
            theoretical_edge=outlier_result.theoretical_edge,
            is_outlier_present=outlier_result.is_outlier_present,
        )

        execution_time = time.time() - start_time

        # Log simulation end
        log_simulation_end(
            logger=logger,
            execution_time_seconds=execution_time,
            status="success",
        )

        print(f"Simulation completed successfully in {execution_time:.2f}s")
        print(f"Top eigenvalues: {eigenvalues}")
        print(f"Outliers detected: {outlier_result.outlier_indices}")

    except Exception as e:
        execution_time = time.time() - start_time
        log_simulation_end(
            logger=logger,
            execution_time_seconds=execution_time,
            status="failed",
            error_message=str(e),
        )
        logger.error(f"Simulation failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
