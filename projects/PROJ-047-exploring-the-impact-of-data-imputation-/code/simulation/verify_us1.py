"""
Verification logic for User Story 1 (T014).
Ensures MNAR mechanism correlates with outcome variable.
"""
import json
import hashlib
import os
from typing import Tuple, Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats
import logging
from .config import get_run_seed, get_simulation_grid

logger = logging.getLogger(__name__)

OUTPUT_PATH = "data/results/us1_verification.json"


def compute_run_id(seed: int, beta: float) -> str:
    """Compute SHA-256 hash of seed_beta string"""
    return hashlib.sha256(f"{seed}_{beta}".encode()).hexdigest()


def verify_mnar_correlation(
    mask: np.ndarray, 
    y_complete: np.ndarray, 
    seed: int, 
    beta: float
) -> Tuple[str, float, float, str]:
    """
    Calculate Spearman correlation between mask and complete Y.
    
    # Remove pairs where mask is NaN if any (should not happen if mask is boolean/0-1)
    valid_indices = ~np.isnan(mask_flat) & ~np.isnan(y_flat)
    if np.sum(valid_indices) < 10:
        return 0.0, 1.0 # Not enough data
            
    rho, p_value = stats.spearmanr(mask_flat[valid_indices], y_flat[valid_indices])
    return rho, p_value

def run_verification_and_save(seed: int, beta: float, mask_data: np.ndarray, 
                              complete_y: np.ndarray, output_path: str) -> Dict[str, Any]:
    """
    Run verification and save results to JSON.
    If multiple runs are called, this function appends or overwrites.
    For T014 requirement: Process all runs. If rho > 0.5 and p < 0.01 -> passed, else failed.
    """
    run_id = compute_run_id(seed, beta)
    
    # Calculate Spearman correlation
    rho, p_value = stats.spearmanr(mask, y_complete)
    
    # Determine status
    if rho > 0.5 and p_value < 0.01:
        status = "passed"
    else:
        status = "failed"
        logger.warning(f"Run {run_id}: MNAR correlation check failed (rho={rho:.4f}, p={p_value:.4f})")
    
    return run_id, float(rho), float(p_value), status


def run_verification_and_save(
    runs_data: List[Dict[str, Any]], 
    output_path: str = OUTPUT_PATH
):
    """
    Run verification for all runs and save results.
    
    Args:
        runs_data: List of run dictionaries containing mask, y_complete, seed, beta
        output_path: Path to save verification results
    """
    results = []
    
    for run in runs_data:
        try:
            run_id, rho, p_value, status = verify_mnar_correlation(
                run['mask'],
                run['y_complete'],
                run['seed'],
                run['beta']
            )
            
            results.append({
                "run_id": run_id,
                "correlation": rho,
                "p_value": p_value,
                "status": status
            })
        except Exception as e:
            logger.error(f"Verification failed for run {run.get('seed', 'unknown')}: {e}")
            # Still record the failure
            results.append({
                "run_id": compute_run_id(run.get('seed', 0), run.get('beta', 0.0)),
                "correlation": 0.0,
                "p_value": 1.0,
                "status": "failed"
            })
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results_list, f, indent=2)
            
    return result

def main():
    """CLI entry point for verification (optional, mostly used internally)."""
    import argparse
    parser = argparse.ArgumentParser(description='Verify MNAR correlation')
    parser.add_argument('--seed', type=int, required=True)
    parser.add_argument('--beta', type=float, required=True)
    parser.add_argument('--mask-file', type=str, required=True)
    parser.add_argument('--y-file', type=str, required=True)
    parser.add_argument('--output', type=str, default='data/results/us1_verification.json')
    
    args = parser.parse_args()
    
    mask_data = np.load(args.mask_file)
    complete_y = np.load(args.y_file)
    
    run_verification_and_save(
        seed=args.seed,
        beta=args.beta,
        mask_data=mask_data,
        complete_y=complete_y,
        output_path=args.output
    )
    print(f"Verification saved to {args.output}")


if __name__ == "__main__":
    main()
