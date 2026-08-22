"""
Sweep Matrix Generator for Parameter Sweep (T040a)

Generates raw Wigner matrix instances for the full parameter sweep
and saves them to data/raw/sweep/ directory.

This task satisfies Constitution Principle III (Data Hygiene) by
preserving raw data before checksumming (T040b) and processing (T020).
"""
import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Project imports based on provided API surface
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from utils.config import get_project_paths, ensure_directories, get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sweep_configs(
    N_values: List[int],
    theta_values: List[float],
    seeds: List[int],
    perturbation_type: str = "diagonal"
) -> List[Dict[str, Any]]:
    """
    Generate a list of configuration dictionaries for the parameter sweep.

    Args:
        N_values: List of matrix sizes (N)
        theta_values: List of perturbation norms (theta)
        seeds: List of random seeds
        perturbation_type: Type of perturbation ("diagonal", "block-sparse", "random-sparse")

    Returns:
        List of configuration dictionaries with keys: N, theta, seed, perturbation_type
    """
    configs = []
    for N in N_values:
        for theta in theta_values:
            for seed in seeds:
                configs.append({
                    "N": N,
                    "theta": theta,
                    "seed": seed,
                    "perturbation_type": perturbation_type
                })
    return configs


def save_raw_sweep_matrix(
    config: Dict[str, Any],
    output_dir: Path
) -> str:
    """
    Generate a single Wigner matrix with perturbation for a given configuration
    and save it to the output directory.

    Args:
        config: Dictionary with keys N, theta, seed, perturbation_type
        output_dir: Directory to save the .npy file

    Returns:
        Path to the saved file as a string
    """
    N = config["N"]
    theta = config["theta"]
    seed = config["seed"]
    perturbation_type = config["perturbation_type"]

    # Set random seed for reproducibility
    np.random.seed(seed)

    logger.info(f"Generating matrix: N={N}, theta={theta}, seed={seed}, type={perturbation_type}")

    # Generate Wigner matrix
    W = generate_wigner_matrix(N, seed=seed)

    # Generate perturbation matrix
    P = create_perturbation(N, theta, perturbation_type, seed=seed)

    # Combined matrix
    A = W + P

    # Construct filename
    filename = f"matrix_N{N}_theta{theta}_seed{seed}.npy"
    filepath = output_dir / filename

    # Save to .npy
    np.save(str(filepath), A)

    logger.info(f"Saved matrix to {filepath}")

    return str(filepath)


def run_sweep_generation(
    N_values: Optional[List[int]] = None,
    theta_values: Optional[List[float]] = None,
    seeds: Optional[List[int]] = None,
    perturbation_type: str = "diagonal",
    output_dir: Optional[Path] = None
) -> List[str]:
    """
    Run the full parameter sweep generation.

    Args:
        N_values: List of matrix sizes (defaults to [1000])
        theta_values: List of perturbation norms (defaults to [1.0, 1.5, 2.0, 2.5, 3.0])
        seeds: List of random seeds (defaults to [42])
        perturbation_type: Type of perturbation (default: "diagonal")
        output_dir: Output directory (defaults to data/raw/sweep)

    Returns:
        List of paths to generated .npy files
    """
    # Default values
    if N_values is None:
        N_values = [1000]
    if theta_values is None:
        theta_values = [1.0, 1.5, 2.0, 2.5, 3.0]
    if seeds is None:
        seeds = [42]

    # Get project paths and ensure directories exist
    paths = get_project_paths()
    if output_dir is None:
        output_dir = paths["data_raw"] / "sweep"

    ensure_directories([output_dir])

    # Generate configurations
    configs = generate_sweep_configs(N_values, theta_values, seeds, perturbation_type)

    logger.info(f"Starting sweep generation with {len(configs)} configurations")

    generated_files = []
    for i, config in enumerate(configs):
        try:
            filepath = save_raw_sweep_matrix(config, output_dir)
            generated_files.append(filepath)
            logger.info(f"Completed {i+1}/{len(configs)}: {filepath}")
        except Exception as e:
            logger.error(f"Failed to generate matrix for config {config}: {e}")
            raise

    logger.info(f"Sweep generation complete. Generated {len(generated_files)} files.")
    return generated_files


def main():
    """
    Command-line entry point for the sweep matrix generator.
    """
    parser = argparse.ArgumentParser(
        description="Generate raw matrix instances for the parameter sweep (T040a)"
    )
    parser.add_argument(
        "--N",
        type=int,
        nargs="+",
        default=[1000],
        help="Matrix sizes (default: 1000)"
    )
    parser.add_argument(
        "--theta",
        type=float,
        nargs="+",
        default=[1.0, 1.5, 2.0, 2.5, 3.0],
        help="Perturbation norms (default: 1.0, 1.5, 2.0, 2.5, 3.0)"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[42],
        help="Random seeds (default: 42)"
    )
    parser.add_argument(
        "--perturbation-type",
        type=str,
        choices=["diagonal", "block-sparse", "random-sparse"],
        default="diagonal",
        help="Type of perturbation (default: diagonal)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (default: data/raw/sweep)"
    )

    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else None

    run_sweep_generation(
        N_values=args.N,
        theta_values=args.theta,
        seeds=args.seeds,
        perturbation_type=args.perturbation_type,
        output_dir=output_dir
    )


if __name__ == "__main__":
    main()
