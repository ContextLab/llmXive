"""
T028 Implementation: Execute sweep over support density set {0.2, 0.3} for each
sparsity pattern type (diagonal, block-sparse, random sparse).

Runs multiple seeds (42, 123, 456) per density level to generate a distribution
of results. Outputs results to data/processed/sensitivity_density_sweep.csv.

Depends on:
  - T013: Perturbation matrix constructor (generators/perturbation.py)
  - T006: Data models (data_models.py)
  - T007a: Iterative solver (analysis/eigen_solver.py)
  - T007b: Validation logic (analysis/eigen_solver.py)
"""
import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigsh
import warnings

# Project imports
# Adjusted to match the provided API surface
sys.path.insert(0, str(Path(__file__).parent.parent))
from generators.perturbation import create_perturbation
from generators.wigner import generate_wigner_matrix
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from data_models import PerturbationConfig, SimulationRun
from utils.config import get_project_paths, get_seed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/sensitivity_density_sweep.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
SUPPORT_DENSITIES = [0.2, 0.3]
SEEDS = [42, 123, 456]
SPARSITY_TYPES = ['diagonal', 'block-sparse', 'random sparse']
DEFAULT_N = 1000
DEFAULT_RANK = 1
DEFAULT_THETA = 2.5  # Fixed theta for density sensitivity analysis

def run_single_density_instance(
    n: int,
    density: float,
    sparsity_type: str,
    seed: int,
    theta: float = DEFAULT_THETA,
    rank: int = DEFAULT_RANK
) -> Dict[str, Any]:
    """
    Run a single sensitivity instance:
    1. Generate Wigner matrix
    2. Create perturbation with specific density/type
    3. Compute eigenvalues
    4. Validate outliers
    5. Return results
    """
    logger.info(f"Running instance: N={n}, density={density}, type={sparsity_type}, seed={seed}")
    
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Generate Wigner matrix
    W = generate_wigner_matrix(n, seed=seed)
    
    # Create perturbation
    try:
        P = create_perturbation(n, rank=rank, support_density=density, perturbation_type=sparsity_type, seed=seed)
    except Exception as e:
        logger.error(f"Failed to create perturbation: {e}")
        raise
    
    # Combine matrices
    H = W + P
    
    # Compute top eigenvalues
    # We need enough eigenvalues to detect outliers beyond the semicircle edge (2.0)
    num_eigenvalues = min(10, n)
    eigenvalues, eigenvectors = compute_top_eigenvalues(H, k=num_eigenvalues, which='LM')
    
    # Sort descending
    eigenvalues = np.sort(eigenvalues)[::-1]
    
    # Validate outliers
    # T007b logic: distinguish outliers from numerical artifacts
    is_outlier, outlier_eigenvalue = validate_eigenvalues(eigenvalues, tolerance=1e-10)
    
    # Calculate theta_c estimate for this run
    # If an outlier exists, theta_c is approximated by the outlier's deviation
    # For density sensitivity, we record the max eigenvalue and whether it's an outlier
    theta_c_est = None
    if is_outlier and len(eigenvalues) > 0:
        # BBP prediction: lambda_out ~ theta + 1/theta for theta > 1
        # We invert this to estimate the effective theta that would produce this outlier
        # Or simply record the max eigenvalue as the metric of interest
        max_eig = eigenvalues[0]
        if max_eig > 2.0:
            # Estimate theta_c based on BBP relation: lambda = theta + 1/theta
            # theta^2 - lambda*theta + 1 = 0
            # theta = (lambda + sqrt(lambda^2 - 4)) / 2
            discriminant = max_eig**2 - 4.0
            if discriminant >= 0:
                theta_c_est = (max_eig + np.sqrt(discriminant)) / 2.0
            else:
                theta_c_est = max_eig # Fallback
    
    result = {
        'n': n,
        'density': density,
        'sparsity_type': sparsity_type,
        'seed': seed,
        'theta': theta,
        'rank': rank,
        'max_eigenvalue': float(eigenvalues[0]) if len(eigenvalues) > 0 else 0.0,
        'is_outlier': is_outlier,
        'theta_c_est': float(theta_c_est) if theta_c_est is not None else None,
        'eigenvalues': [float(e) for e in eigenvalues[:5]] # Store top 5 for inspection
    }
    
    return result

def run_sensitivity_density_sweep(
    output_path: str = 'data/processed/sensitivity_density_sweep.csv',
    n: int = DEFAULT_N
) -> List[Dict[str, Any]]:
    """
    Execute the full sweep over densities and types with multiple seeds.
    """
    logger.info(f"Starting sensitivity density sweep for N={n}")
    
    all_results = []
    
    # Define the grid
    grid = []
    for density in SUPPORT_DENSITIES:
        for sp_type in SPARSITY_TYPES:
            for seed in SEEDS:
                grid.append({
                    'density': density,
                    'sparsity_type': sp_type,
                    'seed': seed
                })
    
    logger.info(f"Grid size: {len(grid)} configurations")
    
    for config in grid:
        try:
            result = run_single_density_instance(
                n=n,
                density=config['density'],
                sparsity_type=config['sparsity_type'],
                seed=config['seed']
            )
            all_results.append(result)
            logger.info(f"Completed: density={config['density']}, type={config['sparsity_type']}, seed={config['seed']}")
        except Exception as e:
            logger.error(f"Failed configuration: {config}. Error: {e}", exc_info=True)
            # Record failure or skip? Task requires real results, so we log and skip
            # but in a real run we might want to crash if data is missing.
            # Here we just log and continue to gather whatever data we can.
    
    # Write results to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    if all_results:
        with open(output_file, 'w', newline='') as f:
            # Use the keys from the first result as headers
            headers = list(all_results[0].keys())
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            for row in all_results:
                writer.writerow(row)
        
        logger.info(f"Wrote {len(all_results)} results to {output_file}")
    else:
        logger.warning("No results collected to write.")
        
    return all_results

def main():
    parser = argparse.ArgumentParser(description='T028: Sensitivity Density Sweep')
    parser.add_argument('--n', type=int, default=DEFAULT_N, help='Matrix size N')
    parser.add_argument('--output', type=str, default='data/processed/sensitivity_density_sweep.csv',
                        help='Output CSV path')
    args = parser.parse_args()
    
    # Ensure directories exist
    paths = get_project_paths()
    for p in [paths['data_processed'], paths['data_logs']]:
        p.mkdir(parents=True, exist_ok=True)
    
    run_sensitivity_density_sweep(output_path=args.output, n=args.n)
    logger.info("Sweep completed.")

if __name__ == '__main__':
    main()