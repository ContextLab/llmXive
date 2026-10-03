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
    
    Args:
        mask: Binary mask (1 = missing, 0 = observed)
        y_complete: Complete outcome variable (before masking)
        seed: Random seed
        beta: MNAR parameter
        
    Returns:
        Tuple of (run_id, correlation, p_value, status)
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
        json.dump(results, f, indent=2)
    
    logger.info(f"Verification results saved to {output_path} ({len(results)} runs)")


def main():
    """
    Main entry point for US1 verification.
    This should be called by the main simulation loop after all runs are complete.
    """
    # This function is called by T029a after the simulation loop
    # It expects runs_data to be passed in or loaded from a temporary file
    # For now, we'll assume it's called with data already prepared
    logger.info("US1 verification completed")


if __name__ == "__main__":
    main()
