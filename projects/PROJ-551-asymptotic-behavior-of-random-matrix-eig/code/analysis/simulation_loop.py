"""
Core simulation loop for User Story 1.
Loads raw Wigner matrices, applies sparse perturbations, computes eigenvalues,
and validates for outliers.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data_models import SimulationRun, PerturbationConfig
from utils.config import get_outlier_tolerance, get_project_paths
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues

logger = logging.getLogger(__name__)

def load_raw_matrix(matrix_path: str) -> np.ndarray:
    """
    Load a raw Wigner matrix from a .npy file.

    Args:
        matrix_path: Path to the .npy file.

    Returns:
        The loaded matrix as a numpy array.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be loaded as a numpy array.
    """
    if not os.path.exists(matrix_path):
        raise FileNotFoundError(f"Raw matrix file not found: {matrix_path}")

    try:
        matrix = np.load(matrix_path)
        logger.info(f"Loaded raw matrix from {matrix_path} with shape {matrix.shape}")
        return matrix
    except Exception as e:
        logger.error(f"Failed to load matrix from {matrix_path}: {e}")
        raise

def run_single_simulation(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a single simulation run.

    This function:
    1. Loads a raw Wigner matrix from disk (produced by T019).
    2. Constructs a sparse perturbation matrix P_N in memory using T013 logic.
    3. Computes the top eigenvalues of (W + P_N).
    4. Validates the results against the theoretical semicircle edge to determine
       the outlier_flag.
    5. Returns a dictionary containing the results and metadata.

    Args:
        params: A dictionary containing simulation parameters. Expected keys:
            - 'matrix_path': str, path to the raw .npy matrix file.
            - 'perturbation_type': str, type of perturbation ('diagonal', 'block-sparse', 'random sparse').
            - 'theta': float, perturbation strength.
            - 'rank': int, rank of the perturbation.
            - 'support_density': float, density for sparse perturbations (0.0 to 1.0).
            - 'seed': int, random seed for perturbation generation (if applicable).
            - 'N': int, matrix dimension (optional, inferred from matrix if not provided).

    Returns:
        A dictionary with the following structure:
        {
            "run_id": str,
            "N": int,
            "seed": int,
            "theta": float,
            "perturbation_type": str,
            "eigenvalues": List[float],
            "outlier_flag": bool,
            "validation_details": Dict[str, Any]
        }

    Raises:
        FileNotFoundError: If the raw matrix file is missing.
        Exception: If eigenvalue computation or validation fails.
    """
    # Extract parameters
    matrix_path = params.get('matrix_path')
    perturbation_type = params.get('perturbation_type', 'diagonal')
    theta = params.get('theta', 2.5)
    rank = params.get('rank', 1)
    support_density = params.get('support_density', 1.0)
    seed = params.get('seed', 42)
    N = params.get('N')

    if not matrix_path:
        raise ValueError("Parameter 'matrix_path' is required.")

    logger.info(f"Starting simulation with matrix: {matrix_path}, theta: {theta}, type: {perturbation_type}")

    # 1. Load raw matrix
    W = load_raw_matrix(matrix_path)
    if N is None:
        N = W.shape[0]
        params['N'] = N

    # 2. Construct perturbation matrix P_N
    # Set random seed for perturbation generation to ensure reproducibility
    np.random.seed(seed)
    try:
        P = create_perturbation(
            N=N,
            rank=rank,
            theta=theta,
            p_type=perturbation_type,
            support_density=support_density
        )
        logger.info(f"Constructed perturbation matrix of type '{perturbation_type}' with rank {rank} and theta {theta}")
    except Exception as e:
        logger.error(f"Failed to create perturbation matrix: {e}")
        raise

    # 3. Compute perturbed matrix
    H = W + P

    # 4. Compute top eigenvalues
    # We need the top eigenvalues to check for outliers > 2.0
    # Using iterative solver for efficiency with large N
    try:
        # Compute top 5 eigenvalues to ensure we capture potential outliers
        k = min(5, N - 1)
        eigenvalues, _ = compute_top_eigenvalues_iterative(H, k=k, which='LA')
        eigenvalues = sorted(eigenvalues, reverse=True)
        logger.info(f"Computed top {len(eigenvalues)} eigenvalues: {eigenvalues}")
    except Exception as e:
        logger.error(f"Eigenvalue computation failed: {e}")
        raise

    # 5. Validate for outliers
    # Use the validation function from T007b
    # This function returns a boolean indicating if an outlier is detected
    # and details about the validation
    outlier_flag, validation_details = validate_eigenvalues(eigenvalues, theta=theta)

    logger.info(f"Validation result: outlier_flag = {outlier_flag}")

    # Construct result dictionary
    run_id = f"run_N{N}_theta{theta}_seed{seed}"
    result = {
        "run_id": run_id,
        "N": N,
        "seed": seed,
        "theta": theta,
        "perturbation_type": perturbation_type,
        "rank": rank,
        "support_density": support_density,
        "eigenvalues": [float(ev) for ev in eigenvalues],
        "outlier_flag": outlier_flag,
        "validation_details": validation_details
    }

    return result

def main():
    """
    Command-line interface for running a single simulation.
    This is primarily for testing and manual runs.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run a single simulation instance")
    parser.add_argument('--matrix-path', type=str, required=True, help='Path to the raw Wigner matrix .npy file')
    parser.add_argument('--perturbation-type', type=str, default='diagonal', choices=['diagonal', 'block-sparse', 'random sparse'], help='Type of perturbation')
    parser.add_argument('--theta', type=float, default=2.5, help='Perturbation strength')
    parser.add_argument('--rank', type=int, default=1, help='Rank of the perturbation')
    parser.add_argument('--support-density', type=float, default=1.0, help='Support density for sparse perturbations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for perturbation generation')
    parser.add_argument('--output', type=str, default='data/processed/single_run_results.json', help='Output JSON file path')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/simulation_run.log')
        ]
    )

    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        params = {
            'matrix_path': args.matrix_path,
            'perturbation_type': args.perturbation_type,
            'theta': args.theta,
            'rank': args.rank,
            'support_density': args.support_density,
            'seed': args.seed
        }

        result = run_single_simulation(params)

        # Save results
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Simulation completed successfully. Results saved to {output_path}")
        print(f"Results saved to {output_path}")
        print(json.dumps(result, indent=2))

        return 0

    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
