import json
import hashlib
import os
from typing import Tuple, Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats
import logging

# Configure logging for warnings about failed correlations
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ensure the output directory exists
OUTPUT_DIR = "data/results"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "us1_verification.json")

def compute_run_id(seed: int, beta: float) -> str:
    """
    Define run_id as a SHA-256 hash of the string f"{seed}_{beta}".
    """
    input_str = f"{seed}_{beta}"
    return hashlib.sha256(input_str.encode('utf-8')).hexdigest()

def verify_mnar_correlation(
    mask: np.ndarray,
    complete_y: np.ndarray,
    seed: int,
    beta: float
) -> Dict[str, Any]:
    """
    Calculate Spearman rho between M (mask) and the generated complete Y (before masking).
    
    Args:
        mask: Binary numpy array (0/1) indicating missingness.
        complete_y: The original outcome variable before masking.
        seed: Random seed used for generation.
        beta: The MNAR parameter used.
    
    Returns:
        Dictionary with run_id, correlation, p_value, and status.
    """
    run_id = compute_run_id(seed, beta)
    
    # Filter out cases where mask is all 0 or all 1 to avoid undefined correlation
    if len(np.unique(mask)) < 2:
        logger.warning(f"Run {run_id}: Mask is constant (all 0 or all 1). Cannot compute correlation.")
        return {
            "run_id": run_id,
            "correlation": 0.0,
            "p_value": 1.0,
            "status": "failed",
            "seed": seed,
            "beta": beta,
            "reason": "constant_mask"
        }

    # Calculate Spearman correlation
    try:
        rho, p_value = stats.spearmanr(mask, complete_y)
        
        # Handle NaN results (e.g., if variance is zero despite check above)
        if np.isnan(rho):
            rho = 0.0
            p_value = 1.0
            
    except Exception as e:
        logger.error(f"Run {run_id}: Error calculating correlation: {e}")
        rho = 0.0
        p_value = 1.0

    # Determine status based on thresholds
    # Passed: rho > 0.5 AND p < 0.01
    # Failed: otherwise (but DO NOT discard the run)
    if rho > 0.5 and p_value < 0.01:
        status = "passed"
    else:
        status = "failed"
        logger.warning(
            f"Run {run_id}: MNAR verification failed. "
            f"Spearman rho={rho:.4f}, p-value={p_value:.4f}. "
            f"Thresholds: rho > 0.5, p < 0.01. "
            f"Proceeding with run despite failure."
        )

    return {
        "run_id": run_id,
        "correlation": float(rho),
        "p_value": float(p_value),
        "status": status,
        "seed": seed,
        "beta": beta
    }

def run_verification_and_save(
    runs_data: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process multiple runs, calculate correlations, and save results to JSON.
    
    Args:
        runs_data: List of dictionaries, each containing 'mask', 'complete_y', 'seed', 'beta'.
        output_path: Path to save the results JSON. Defaults to data/results/us1_verification.json.
    
    Returns:
        List of verification result dictionaries.
    """
    if output_path is None:
        output_path = OUTPUT_FILE
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results = []
    
    for run_data in runs_data:
        mask = run_data.get('mask')
        complete_y = run_data.get('complete_y')
        seed = run_data.get('seed')
        beta = run_data.get('beta')
        
        if mask is None or complete_y is None or seed is None or beta is None:
            logger.error(f"Missing required fields in run data. Skipping run.")
            continue
        
        result = verify_mnar_correlation(mask, complete_y, seed, beta)
        results.append(result)
    
    # Save results to JSON
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Verification results saved to {output_path}")
    return results

def main():
    """
    Entry point for verification script.
    This function is intended to be called by the main orchestration loop (T029a).
    It expects to receive data from the simulation runs.
    For standalone testing, it can generate dummy data to verify the logic.
    """
    # This function is primarily a wrapper for the orchestration loop.
    # The actual data population happens in T029a (main.py).
    # If run standalone for testing purposes:
    print("Verify US1 script loaded. Call run_verification_and_save() with simulation data.")
    pass

if __name__ == "__main__":
    main()