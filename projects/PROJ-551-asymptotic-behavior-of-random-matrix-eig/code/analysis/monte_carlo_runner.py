"""
Monte Carlo runner for User Story 2.
Executes a sufficient number of iterations per configuration to statistically
determine the probability of outlier emergence as a function of perturbation norm.

Output: data/processed/mc_results.csv
"""
import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import sparse

# Project imports based on API surface
from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues, validate_eigenvalues
from analysis.outlier_detect import detect_outliers, OutlierResult
from utils.config import get_project_paths, ensure_directories, get_seed
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end
from utils.results_logger import append_to_aggregated_results
from utils.checksum import compute_file_checksum

logger = logging.getLogger(__name__)

def run_single_mc_iteration(
    n: int,
    theta: float,
    seed: int,
    sparsity_density: float = 1.0,
    perturbation_type: str = "diagonal"
) -> Dict[str, Any]:
    """
    Run a single Monte Carlo iteration for a given configuration.
    
    Returns a dictionary with the results of this specific run.
    """
    # Set seed for reproducibility of this specific run
    np.random.seed(seed)
    
    # 1. Generate Wigner Matrix
    # W_N is symmetric with entries ~ N(0, 1/N)
    W = generate_wigner_matrix(n)
    
    # 2. Create Perturbation
    # P_N is a sparse perturbation with norm theta
    P = create_perturbation(
        n, 
        theta, 
        sparsity_density=sparsity_density, 
        perturbation_type=perturbation_type
    )
    
    # 3. Construct Perturbed Matrix H = W + P
    H = W + P
    
    # 4. Compute Top Eigenvalues
    # We need enough eigenvalues to detect outliers near the edge (approx 2.0)
    num_eigenvalues = min(10, n)
    try:
        eigenvalues, eigenvectors = compute_top_eigenvalues(H, k=num_eigenvalues, which='LA')
    except Exception as e:
        logger.error(f"Eigenvalue computation failed for N={n}, theta={theta}, seed={seed}: {e}")
        return {
            "n": n,
            "theta": theta,
            "seed": seed,
            "sparsity_density": sparsity_density,
            "perturbation_type": perturbation_type,
            "success": False,
            "error": str(e),
            "outlier_detected": False,
            "max_eigenvalue": None,
            "eigenvalues": None
        }
    
    # 5. Validate Eigenvalues against theoretical edge
    # Theoretical edge for Wigner is 2.0. Outliers should be > 2.0 + tolerance
    is_valid = validate_eigenvalues(eigenvalues, tol=1e-6)
    if not is_valid:
        logger.warning(f"Eigenvalues failed validation for N={n}, theta={theta}. "
                     f"Max eigenvalue: {np.max(eigenvalues):.6f}")
    
    # 6. Detect Outliers
    # Check if any eigenvalue exceeds the bulk edge (approx 2.0) significantly
    # The outlier_detect module handles the logic of comparing against BBP or bulk edge
    outlier_result: OutlierResult = detect_outliers(
        eigenvalues, 
        theta, 
        n,
        perturbation_type=perturbation_type
    )
    
    return {
        "n": n,
        "theta": theta,
        "seed": seed,
        "sparsity_density": sparsity_density,
        "perturbation_type": perturbation_type,
        "success": True,
        "error": None,
        "outlier_detected": outlier_result.is_outlier,
        "max_eigenvalue": float(eigenvalues[0]) if len(eigenvalues) > 0 else None,
        "eigenvalues": eigenvalues.tolist() if len(eigenvalues) > 0 else [],
        "bbp_threshold": outlier_result.bbp_threshold,
        "bulk_edge": 2.0
    }

def run_monte_carlo_sweep(
    configs: List[Dict[str, Any]],
    num_iterations: int,
    output_path: str
) -> pd.DataFrame:
    """
    Run Monte Carlo simulations for a list of configurations.
    
    Args:
        configs: List of dicts with keys: n, theta, sparsity_density, perturbation_type
        num_iterations: Number of iterations per configuration
        output_path: Path to save the CSV results
        
    Returns:
        DataFrame with all results
    """
    results = []
    
    for config in configs:
        n = config["n"]
        theta = config["theta"]
        sparsity_density = config.get("sparsity_density", 1.0)
        perturbation_type = config.get("perturbation_type", "diagonal")
        
        logger.info(f"Starting Monte Carlo sweep: N={n}, theta={theta:.2f}, "
                  f"density={sparsity_density:.2f}, type={perturbation_type}, "
                  f"iters={num_iterations}")
        
        start_time = time.time()
        
        for i in range(num_iterations):
            # Generate a unique seed for this iteration based on a base seed and index
            base_seed = get_seed()
            run_seed = base_seed + hash((n, theta, sparsity_density, perturbation_type, i)) % (2**31)
            
            try:
                result = run_single_mc_iteration(
                    n=n,
                    theta=theta,
                    seed=run_seed,
                    sparsity_density=sparsity_density,
                    perturbation_type=perturbation_type
                )
                results.append(result)
                
                if (i + 1) % 10 == 0:
                    logger.debug(f"Completed {i+1}/{num_iterations} iterations for N={n}, theta={theta}")
                    
            except Exception as e:
                logger.error(f"Unexpected error in iteration {i}: {e}")
                # Record failure to ensure we don't silently skip
                results.append({
                    "n": n,
                    "theta": theta,
                    "seed": run_seed,
                    "sparsity_density": sparsity_density,
                    "perturbation_type": perturbation_type,
                    "success": False,
                    "error": str(e),
                    "outlier_detected": False,
                    "max_eigenvalue": None,
                    "eigenvalues": [],
                    "bbp_threshold": None,
                    "bulk_edge": 2.0
                })
        
        elapsed = time.time() - start_time
        logger.info(f"Completed sweep for N={n}, theta={theta} in {elapsed:.2f}s. "
                  f"Total results: {len(results)}")
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Save to CSV
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved Monte Carlo results to {output_path}")
    
    return df

def main():
    """
    Main entry point for the Monte Carlo runner.
    """
    parser = argparse.ArgumentParser(description="Monte Carlo runner for outlier detection")
    parser.add_argument("--config", type=str, default=None, 
                      help="Path to JSON config file with sweep parameters")
    parser.add_argument("--iterations", type=int, default=100,
                      help="Number of Monte Carlo iterations per configuration")
    parser.add_argument("--output", type=str, default="data/processed/mc_results.csv",
                      help="Output CSV file path")
    parser.add_argument("--n", type=int, default=1000,
                      help="Matrix size (if not using config)")
    parser.add_argument("--theta", type=float, default=2.5,
                      help="Perturbation norm (if not using config)")
    
    args = parser.parse_args()
    
    # Setup logging
    paths = get_project_paths()
    ensure_directories(paths)
    logger = setup_simulation_logger("monte_carlo_runner")
    
    log_simulation_start("monte_carlo_runner", args)
    
    try:
        # Determine configurations
        if args.config:
            import json
            with open(args.config, 'r') as f:
                config_data = json.load(f)
            configs = config_data.get("configs", [])
            num_iterations = config_data.get("num_iterations", args.iterations)
        else:
            # Default single configuration if no config file provided
            configs = [{
                "n": args.n,
                "theta": args.theta,
                "sparsity_density": 1.0,
                "perturbation_type": "diagonal"
            }]
            num_iterations = args.iterations
        
        if not configs:
            logger.error("No configurations provided.")
            sys.exit(1)
        
        logger.info(f"Running Monte Carlo with {num_iterations} iterations per configuration.")
        logger.info(f"Configurations: {configs}")
        
        # Run the sweep
        df = run_monte_carlo_sweep(configs, num_iterations, args.output)
        
        # Log summary
        if not df.empty:
            summary = df.groupby(["n", "theta", "sparsity_density", "perturbation_type"]).agg({
                "success": "sum",
                "outlier_detected": "sum"
            }).reset_index()
            summary["outlier_rate"] = summary["outlier_detected"] / summary["success"]
            logger.info(f"Summary:\n{summary.to_string(index=False)}")
            
            # Append to aggregated results if needed
            append_to_aggregated_results(df, "monte_carlo")
        
        log_simulation_end("monte_carlo_runner", success=True)
        
    except Exception as e:
        logger.exception(f"Monte Carlo runner failed: {e}")
        log_simulation_end("monte_carlo_runner", success=False, error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()