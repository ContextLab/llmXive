"""
Module to record simulation results for a single run.
Implements T015: Record results (eigenvalues, perturbation params) to
data/processed/single_run_results.json.
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

# Import from project modules
from utils.config import get_project_paths, ensure_directories
from utils.results_logger import record_simulation_result
from analysis.outlier_detect import detect_outliers
from utils.logging_config import setup_simulation_logger


def run_single_run_recorder(
    N: int,
    theta: float,
    seed: int,
    eigenvalues: List[float],
    output_path: Optional[Path] = None
) -> Path:
    """
    Execute the logic to record a single run's results.

    Args:
        N: Matrix size.
        theta: Perturbation strength.
        seed: Random seed.
        eigenvalues: List of computed eigenvalues.
        output_path: Optional override for output file path.

    Returns:
        Path to the written results file.
    """
    # Generate a run_id based on parameters and timestamp
    run_id = f"run_N{N}_theta{theta}_seed{seed}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    # Determine outlier flag using the project's outlier detection logic
    # We assume a bulk edge of 2.0 for Wigner matrices
    outlier_result = detect_outliers(eigenvalues, bulk_edge=2.0)
    outlier_flag = outlier_result.has_outlier

    # Record the result
    result_path = record_simulation_result(
        run_id=run_id,
        N=N,
        theta=theta,
        seed=seed,
        eigenvalues=eigenvalues,
        outlier_flag=outlier_flag,
        output_path=output_path
    )

    return result_path


def main():
    """
    CLI entry point for recording a single run's results.
    Expected arguments: N, theta, seed, eigenvalues (comma-separated)
    """
    parser = argparse.ArgumentParser(
        description="Record simulation results to data/processed/single_run_results.json"
    )
    parser.add_argument("--N", type=int, required=True, help="Matrix dimension")
    parser.add_argument("--theta", type=float, required=True, help="Perturbation norm")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument(
        "--eigenvalues",
        type=str,
        required=True,
        help="Comma-separated list of eigenvalues (e.g., '2.5, 1.9, 1.8, ...')"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output path for results JSON"
    )

    args = parser.parse_args()

    # Setup logging
    log_path = get_project_paths()["logs"]
    ensure_directories()
    logger = setup_simulation_logger("results_recorder", log_file=log_path / "results_recorder.log")

    logger.info(f"Starting results recording for N={args.N}, theta={args.theta}, seed={args.seed}")

    # Parse eigenvalues
    try:
        eigenvalues = [float(x.strip()) for x in args.eigenvalues.split(",")]
    except ValueError as e:
        logger.error(f"Failed to parse eigenvalues: {e}")
        sys.exit(1)

    # Determine output path
    output_path = None
    if args.output:
        output_path = Path(args.output)

    try:
        result_file = run_single_run_recorder(
            N=args.N,
            theta=args.theta,
            seed=args.seed,
            eigenvalues=eigenvalues,
            output_path=output_path
        )
        logger.info(f"Successfully recorded results to: {result_file}")
        print(f"Results written to: {result_file}")
    except Exception as e:
        logger.error(f"Failed to record results: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
