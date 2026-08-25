"""
Task T028: Execute sensitivity analysis sweep over support density.

Executes a sweep over support density set {0.1, 0.2, 0.3} for each sparsity
pattern type (diagonal, block-sparse, random sparse).

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
from scipy import sparse

# Project imports based on provided API surface
# Note: We assume these are available in the code/ directory context
# Importing from the root of the project's code directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from analysis.eigen_solver import compute_top_eigenvalues
from analysis.outlier_detect import detect_outliers, calculate_bbp_threshold
from utils.config import get_project_paths, get_seed, get_tolerance
from utils.logging_config import setup_simulation_logger, log_simulation_start, log_simulation_end

# Configure logging
logger = setup_simulation_logger("sensitivity_density_sweep")

def run_single_density_instance(
    N: int,
    density: float,
    pattern_type: str,
    theta: float,
    rank: int,
    seed: int,
    tolerance: float = 1e-10
) -> Dict[str, Any]:
    """
    Run a single instance of the sensitivity analysis for a given density and pattern.
    
    Args:
        N: Matrix dimension
        density: Support density (0.1, 0.2, 0.3)
        pattern_type: 'diagonal', 'block-sparse', or 'random sparse'
        theta: Perturbation norm
        rank: Rank of the perturbation
        seed: Random seed for reproducibility
        tolerance: Convergence tolerance for eigen solver
    
    Returns:
        Dictionary with results for this instance.
    """
    start_time = time.time()
    
    # Set seed for reproducibility
    np.random.seed(seed)
    
    try:
        # 1. Generate Wigner Matrix
        W = generate_wigner_matrix(N, seed=seed)
        
        # 2. Generate Perturbation
        # Pattern type mapping
        if pattern_type == 'diagonal':
            p_type = 'diagonal'
        elif pattern_type == 'block-sparse':
            p_type = 'block-sparse'
        elif pattern_type == 'random sparse':
            p_type = 'random sparse'
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
        
        P = create_perturbation(
            N=N,
            rank=rank,
            norm=theta,
            pattern_type=p_type,
            density=density,
            seed=seed + 1  # Offset seed for perturbation
        )
        
        # 3. Construct Perturbed Matrix
        H = W + P
        
        # 4. Compute Eigenvalues
        # We need top eigenvalues to check for outliers
        num_eigenvalues = min(10, N)
        eigenvalues = compute_top_eigenvalues(H, k=num_eigenvalues, which='LA', tol=tolerance)
        
        # 5. Detect Outliers
        bbp_edge = calculate_bbp_threshold(theta)
        outlier_result = detect_outliers(eigenvalues, bbp_edge, tolerance=tolerance)
        
        # 6. Record Metrics
        end_time = time.time()
        execution_time = end_time - start_time
        
        result = {
            "N": N,
            "density": density,
            "pattern_type": pattern_type,
            "theta": theta,
            "rank": rank,
            "seed": seed,
            "execution_time_sec": execution_time,
            "max_eigenvalue": float(eigenvalues[0]) if len(eigenvalues) > 0 else None,
            "second_eigenvalue": float(eigenvalues[1]) if len(eigenvalues) > 1 else None,
            "bbp_edge": bbp_edge,
            "is_outlier": outlier_result.get("has_outlier", False),
            "outlier_value": outlier_result.get("outlier_value", None),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Completed instance: N={N}, density={density}, pattern={pattern_type}, theta={theta}, outlier={result['is_outlier']}")
        return result
        
    except Exception as e:
        logger.error(f"Error in instance N={N}, density={density}, pattern={pattern_type}: {str(e)}", exc_info=True)
        raise

def run_sensitivity_density_sweep(
    densities: List[float],
    patterns: List[str],
    N: int,
    theta: float,
    rank: int,
    num_seeds: int,
    base_seed: int,
    output_path: str
) -> List[Dict[str, Any]]:
    """
    Execute the full sensitivity sweep over densities and patterns.
    
    Args:
        densities: List of support densities to test (e.g., [0.1, 0.2, 0.3])
        patterns: List of sparsity pattern types
        N: Matrix dimension
        theta: Perturbation norm
        rank: Rank of perturbation
        num_seeds: Number of Monte Carlo seeds per configuration
        base_seed: Base seed for random number generation
        output_path: Path to save the CSV results
    
    Returns:
        List of result dictionaries.
    """
    all_results = []
    
    logger.info(f"Starting sensitivity sweep: N={N}, theta={theta}, rank={rank}")
    logger.info(f"Densities: {densities}, Patterns: {patterns}")
    logger.info(f"Seeds per config: {num_seeds}")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    total_configs = len(densities) * len(patterns) * num_seeds
    current = 0
    
    for pattern in patterns:
        for density in densities:
            for i in range(num_seeds):
                current += 1
                seed = base_seed + i
                logger.info(f"Processing {current}/{total_configs}: density={density}, pattern={pattern}, seed={seed}")
                
                try:
                    result = run_single_density_instance(
                        N=N,
                        density=density,
                        pattern_type=pattern,
                        theta=theta,
                        rank=rank,
                        seed=seed
                    )
                    all_results.append(result)
                except Exception as e:
                    logger.error(f"Failed configuration (density={density}, pattern={pattern}, seed={seed}): {e}")
                    # We could choose to skip or fail fast; here we log and continue
                    # but in a strict pipeline, we might want to stop.
                    # For this task, we record the failure and continue if possible.
                    # However, to ensure a clean CSV, we might skip failed entries or record them.
                    # Let's record a failure entry.
                    all_results.append({
                        "N": N,
                        "density": density,
                        "pattern_type": pattern,
                        "theta": theta,
                        "rank": rank,
                        "seed": seed,
                        "execution_time_sec": 0.0,
                        "max_eigenvalue": None,
                        "second_eigenvalue": None,
                        "bbp_edge": None,
                        "is_outlier": None,
                        "outlier_value": None,
                        "error": str(e),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
    
    # Write results to CSV
    if all_results:
        fieldnames = list(all_results[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_results)
        
        logger.info(f"Sweep complete. Results written to {output_path}")
    else:
        logger.warning("No results generated. CSV not created.")
    
    return all_results

def main():
    """Main entry point for the sensitivity density sweep script."""
    parser = argparse.ArgumentParser(description="Execute sensitivity analysis sweep over support density.")
    parser.add_argument("--densities", type=float, nargs='+', default=[0.1, 0.2, 0.3],
                        help="Support densities to sweep (default: 0.1 0.2 0.3)")
    parser.add_argument("--patterns", type=str, nargs='+', 
                        default=['diagonal', 'block-sparse', 'random sparse'],
                        help="Sparsity pattern types (default: diagonal block-sparse random sparse)")
    parser.add_argument("--N", type=int, default=1000, help="Matrix dimension (default: 1000)")
    parser.add_argument("--theta", type=float, default=2.5, help="Perturbation norm (default: 2.5)")
    parser.add_argument("--rank", type=int, default=1, help="Rank of perturbation (default: 1)")
    parser.add_argument("--num-seeds", type=int, default=5, help="Number of seeds per configuration (default: 5)")
    parser.add_argument("--base-seed", type=int, default=42, help="Base seed for random generation (default: 42)")
    parser.add_argument("--output", type=str, default="data/processed/sensitivity_density_sweep.csv",
                        help="Output CSV path (default: data/processed/sensitivity_density_sweep.csv)")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.densities:
        logger.error("At least one density must be specified.")
        sys.exit(1)
    
    try:
        run_sensitivity_density_sweep(
            densities=args.densities,
            patterns=args.patterns,
            N=args.N,
            theta=args.theta,
            rank=args.rank,
            num_seeds=args.num_seeds,
            base_seed=args.base_seed,
            output_path=args.output
        )
        logger.info("Task T028 completed successfully.")
    except Exception as e:
        logger.error(f"Task T028 failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
