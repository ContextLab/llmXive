"""
Task T028: Execute sweep over support density set {0.1, 0.2, 0.3} for each sparsity pattern type.
Output: data/processed/sensitivity_density_sweep.csv
"""
import argparse
import csv
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np

# Project imports based on API surface
# Note: We import from the package root relative to code/
# Assuming this file is run from code/ or python path includes code/
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold
from utils.config import get_project_paths, ensure_directories
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end

# Configure logging for this module
logger = logging.getLogger(__name__)

def run_single_density_instance(
    N: int,
    theta: float,
    density: float,
    sparsity_type: str,
    seed: int
) -> Dict[str, Any]:
    """
    Run a single sensitivity analysis instance for a specific density.
    
    Returns a dictionary with results.
    """
    # 1. Generate Wigner Matrix
    W = generate_wigner_matrix(N, seed=seed)
    
    # 2. Create Perturbation
    # create_perturbation signature: (N, theta, sparsity_type, density, seed)
    # Based on T013 implementation expectations
    P = create_perturbation(N, theta, sparsity_type, density, seed)
    
    # 3. Construct Perturbed Matrix
    H = W + P
    
    # 4. Compute Top Eigenvalues
    # We need enough eigenvalues to detect outliers near the edge (2.0)
    k = min(10, N)
    eigenvalues = compute_top_eigenvalues(H, k=k)
    
    # 5. Detect Outliers
    bbp_threshold = calculate_bbp_threshold(theta)
    outlier_result = detect_outliers(eigenvalues, bbp_threshold)
    
    return {
        "N": N,
        "theta": theta,
        "density": density,
        "sparsity_type": sparsity_type,
        "seed": seed,
        "max_eigenvalue": float(eigenvalues[0]) if len(eigenvalues) > 0 else 0.0,
        "outlier_detected": outlier_result.has_outlier,
        "outlier_value": float(outlier_result.outlier_value) if outlier_result.has_outlier else None,
        "bbp_threshold": float(bbp_threshold),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def run_sensitivity_density_sweep(
    densities: List[float],
    sparsity_types: List[str],
    N: int = 1000,
    theta: float = 2.5,
    iterations: int = 50,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Execute the full sweep over densities and sparsity types.
    
    Args:
        densities: List of support densities to test (e.g., [0.1, 0.2, 0.3])
        sparsity_types: List of sparsity pattern types (e.g., ['diagonal', 'block', 'random'])
        N: Matrix size
        theta: Perturbation norm
        iterations: Number of Monte Carlo iterations per configuration
        output_path: Path to write CSV results (optional)
        
    Returns:
        List of result dictionaries
    """
    if output_path is None:
        paths = get_project_paths()
        output_path = str(paths["processed"] / "sensitivity_density_sweep.csv")
        
    ensure_directories([os.path.dirname(output_path)])
    
    results = []
    start_time = time.time()
    
    logger.info(f"Starting sensitivity density sweep. Densities: {densities}, Types: {sparsity_types}")
    logger.info(f"Configuration: N={N}, theta={theta}, iterations={iterations}")
    
    for sparsity_type in sparsity_types:
        for density in densities:
            logger.info(f"Running sweep for type={sparsity_type}, density={density}")
            
            for i in range(iterations):
                seed = int(np.random.randint(0, 2**31))
                try:
                    res = run_single_density_instance(N, theta, density, sparsity_type, seed)
                    results.append(res)
                    logger.debug(f"  Iteration {i+1}/{iterations}: max_eig={res['max_eigenvalue']:.4f}, outlier={res['outlier_detected']}")
                except Exception as e:
                    logger.error(f"  Iteration {i+1}/{iterations} failed: {e}")
                    # Log failure but continue
                    results.append({
                        "N": N,
                        "theta": theta,
                        "density": density,
                        "sparsity_type": sparsity_type,
                        "seed": seed,
                        "max_eigenvalue": None,
                        "outlier_detected": False,
                        "outlier_value": None,
                        "bbp_threshold": None,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "error": str(e)
                    })
    
    elapsed = time.time() - start_time
    logger.info(f"Sweep completed in {elapsed:.2f} seconds. Total results: {len(results)}")
    
    # Write results to CSV
    if results:
        fieldnames = list(results[0].keys())
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Results written to {output_path}")
    
    return results

def main():
    """Main entry point for the sensitivity density sweep."""
    parser = argparse.ArgumentParser(description="Execute sensitivity analysis density sweep (Task T028)")
    parser.add_argument("--densities", type=float, nargs="+", default=[0.1, 0.2, 0.3],
                        help="Support densities to sweep (default: 0.1 0.2 0.3)")
    parser.add_argument("--types", type=str, nargs="+", default=["diagonal", "block", "random"],
                        help="Sparsity pattern types (default: diagonal block random)")
    parser.add_argument("--N", type=int, default=1000, help="Matrix size")
    parser.add_argument("--theta", type=float, default=2.5, help="Perturbation norm")
    parser.add_argument("--iterations", type=int, default=50, help="MC iterations per config")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    parser.add_argument("--log", type=str, default="data/logs/sensitivity_density_sweep.log",
                        help="Log file path")
    
    args = parser.parse_args()
    
    # Setup logging
    ensure_directories([os.path.dirname(args.log)])
    log_file = Path(args.log)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logger
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    log_simulation_start("Sensitivity Density Sweep", vars(args))
    
    try:
        results = run_sensitivity_density_sweep(
            densities=args.densities,
            sparsity_types=args.types,
            N=args.N,
            theta=args.theta,
            iterations=args.iterations,
            output_path=args.output
        )
        log_simulation_end("Sensitivity Density Sweep", success=True, count=len(results))
    except Exception as e:
        logger.exception("Sensitivity density sweep failed")
        log_simulation_end("Sensitivity Density Sweep", success=False, error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()