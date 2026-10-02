"""
Test runner for T014: Core Simulation Loop.
Executes a single run with N=1000, rank-1 diagonal perturbation (theta=2.5)
and verifies an eigenvalue > 2.0 exists.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add code directory to path
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.simulation_loop import run_single_simulation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Define test parameters per the task description
    # We assume T019 has produced a matrix at a known path
    # For this test, we generate the matrix on the fly to ensure the test is self-contained
    # In a real CI/CD environment, this would load from data/raw/
    import numpy as np
    from generators.wigner import generate_wigner_matrix

    N = 1000
    seed = 42
    theta = 2.5
    perturbation_type = 'diagonal'
    rank = 1

    # Generate raw matrix (simulating T019 output)
    logger.info(f"Generating test Wigner matrix N={N}, seed={seed}")
    W = generate_wigner_matrix(N, seed=seed)
    matrix_path = 'data/raw/matrix_N1000_seed42_test.npy'
    os.makedirs(os.path.dirname(matrix_path), exist_ok=True)
    np.save(matrix_path, W)

    # Prepare parameters
    params = {
        'matrix_path': matrix_path,
        'perturbation_type': perturbation_type,
        'theta': theta,
        'rank': rank,
        'support_density': 1.0,
        'seed': seed,
        'N': N
    }

    # Run simulation
    logger.info("Running single simulation...")
    result = run_single_simulation(params)

    # Validate
    eigenvalues = result['eigenvalues']
    outlier_flag = result['outlier_flag']

    logger.info(f"Top eigenvalue: {eigenvalues[0]}")
    logger.info(f"Outlier flag: {outlier_flag}")

    # Check condition: eigenvalue > 2.0
    if eigenvalues[0] > 2.0:
        logger.info("SUCCESS: Top eigenvalue > 2.0. Outlier detected as expected.")
        return 0
    else:
        logger.error("FAILURE: Top eigenvalue <= 2.0. Expected outlier not found.")
        return 1

if __name__ == "__main__":
    sys.exit(main())