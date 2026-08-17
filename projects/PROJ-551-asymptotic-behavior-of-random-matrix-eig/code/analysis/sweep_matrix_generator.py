"""
Sweep Matrix Generator for T040a.

Generates raw matrix instances for the full parameter sweep.
Saves matrices to data/raw/sweep/matrix_N{N}_theta{theta}_seed{seed}.npy.
"""
import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from generators.wigner import generate_wigner_matrix
from generators.perturbation import create_perturbation
from utils.config import get_project_paths, ensure_directories, load_config
from utils.logging_config import setup_simulation_logger

logger = logging.getLogger(__name__)

def generate_sweep_configs(
    N_values: List[int],
    theta_values: List[float],
    seeds: List[int],
    perturbation_type: str = "diagonal"
) -> List[Dict[str, Any]]:
    """
    Generate a list of configuration dictionaries for the sweep.
    
    Args:
        N_values: List of matrix sizes.
        theta_values: List of perturbation strengths.
        seeds: List of random seeds.
        perturbation_type: Type of perturbation (diagonal, block-sparse, random-sparse).
    
    Returns:
        List of dicts with keys: N, theta, seed, perturbation_type.
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
    N: int,
    theta: float,
    seed: int,
    perturbation_type: str,
    output_dir: Path
) -> Path:
    """
    Generate a Wigner matrix, apply perturbation, and save the result.
    
    The saved matrix is the perturbed matrix (W + P).
    
    Args:
        N: Matrix dimension.
        theta: Perturbation norm.
        seed: Random seed for reproducibility.
        perturbation_type: Type of perturbation to apply.
        output_dir: Directory to save the .npy file.
    
    Returns:
        Path to the saved .npy file.
    """
    # Set seed for reproducibility
    np.random.seed(seed)
    
    # Generate Wigner matrix
    # Wigner matrix is symmetric with variance 1/N
    W = generate_wigner_matrix(N)
    
    # Create perturbation
    # Perturbation is a diagonal matrix with rank-1 perturbation of norm theta
    P = create_perturbation(N, theta, perturbation_type)
    
    # Perturbed matrix
    M = W + P
    
    # Construct filename
    filename = f"matrix_N{N}_theta{theta:.1f}_seed{seed}.npy"
    filepath = output_dir / filename
    
    # Save matrix
    np.save(str(filepath), M)
    
    logger.info(f"Saved perturbed matrix to {filepath}")
    return filepath

def run_sweep_generation(
    N_values: List[int],
    theta_values: List[float],
    seeds: List[int],
    perturbation_type: str = "diagonal",
    output_dir: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Run the full sweep generation.
    
    Args:
        N_values: List of matrix sizes.
        theta_values: List of perturbation strengths.
        seeds: List of random seeds.
        perturbation_type: Type of perturbation.
        output_dir: Directory to save matrices. Defaults to data/raw/sweep.
    
    Returns:
        List of dicts with metadata about generated files.
    """
    if output_dir is None:
        paths = get_project_paths()
        output_dir = paths["data_raw"] / "sweep"
    
    ensure_directories([output_dir])
    
    configs = generate_sweep_configs(N_values, theta_values, seeds, perturbation_type)
    results = []
    
    logger.info(f"Starting sweep generation for {len(configs)} configurations")
    
    for config in configs:
        try:
            filepath = save_raw_sweep_matrix(
                config["N"],
                config["theta"],
                config["seed"],
                config["perturbation_type"],
                output_dir
            )
            
            results.append({
                "N": config["N"],
                "theta": config["theta"],
                "seed": config["seed"],
                "perturbation_type": config["perturbation_type"],
                "filepath": str(filepath),
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Failed to generate matrix for N={config['N']}, theta={config['theta']}, seed={config['seed']}: {e}")
            results.append({
                "N": config["N"],
                "theta": config["theta"],
                "seed": config["seed"],
                "perturbation_type": config["perturbation_type"],
                "status": "failed",
                "error": str(e)
            })
    
    logger.info(f"Sweep generation complete. {len([r for r in results if r['status'] == 'success'])} successful, {len([r for r in results if r['status'] == 'failed'])} failed")
    return results

def main():
    """Main entry point for the sweep matrix generator."""
    parser = argparse.ArgumentParser(description="Generate raw matrix instances for parameter sweep")
    parser.add_argument("--N", type=int, nargs="+", default=[500, 1000, 1500, 2000],
                      help="List of matrix sizes")
    parser.add_argument("--theta", type=float, nargs="+", default=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
                      help="List of perturbation strengths")
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 456],
                      help="List of random seeds")
    parser.add_argument("--perturbation_type", type=str, default="diagonal",
                      choices=["diagonal", "block-sparse", "random-sparse"],
                      help="Type of perturbation")
    parser.add_argument("--config", type=str, default=None,
                      help="Path to config file (optional)")
    
    args = parser.parse_args()
    
    # Setup logging
    log_dir = get_project_paths()["data_logs"]
    ensure_directories([log_dir])
    log_file = log_dir / "sweep_matrix_generation.log"
    setup_simulation_logger("sweep_matrix_generator", log_file)
    
    logger.info("Starting sweep matrix generation")
    logger.info(f"N values: {args.N}")
    logger.info(f"Theta values: {args.theta}")
    logger.info(f"Seeds: {args.seeds}")
    logger.info(f"Perturbation type: {args.perturbation_type}")
    
    # Load config if provided
    if args.config:
        try:
            config = load_config(args.config)
            logger.info(f"Loaded config from {args.config}")
        except Exception as e:
            logger.warning(f"Failed to load config: {e}")
    
    # Run generation
    results = run_sweep_generation(
        args.N,
        args.theta,
        args.seeds,
        args.perturbation_type
    )
    
    # Log summary
    success_count = len([r for r in results if r['status'] == 'success'])
    fail_count = len([r for r in results if r['status'] == 'failed'])
    logger.info(f"Generation complete: {success_count} successful, {fail_count} failed")
    
    # Return results for potential downstream processing
    return results

if __name__ == "__main__":
    main()