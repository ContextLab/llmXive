import json
import hashlib
import os
from typing import Tuple, Any, Dict, List, Optional
import numpy as np
import pandas as pd
from scipy import stats

def compute_run_id(seed: int, beta: float) -> str:
    """Compute SHA-256 hash of seed_beta string."""
    data = f"{seed}_{beta}"
    return hashlib.sha256(data.encode()).hexdigest()

def verify_mnar_correlation(mask_data: np.ndarray, complete_y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Spearman correlation between mask and complete Y.
    Returns (rho, p_value).
    """
    # Ensure arrays are 1D
    mask_flat = mask_data.flatten()
    y_flat = complete_y.flatten()
    
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
    rho, p_value = verify_mnar_correlation(mask_data, complete_y)
    
    status = "passed" if (rho > 0.5 and p_value < 0.01) else "failed"
    
    # Log warning if failed but do not discard
    if status == "failed":
        print(f"Warning: Verification failed for run_id={run_id} (rho={rho:.4f}, p={p_value:.4f})")
    
    result = {
        "run_id": run_id,
        "seed": seed,
        "beta": beta,
        "correlation": float(rho),
        "p_value": float(p_value),
        "status": status
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Load existing results if file exists, then append/update
    results_list = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                content = f.read().strip()
                if content:
                    # Assume it's a list of objects or a single object
                    data = json.loads(content)
                    if isinstance(data, list):
                        results_list = data
                    elif isinstance(data, dict):
                        results_list = [data]
        except json.JSONDecodeError:
            results_list = []
    
    # Check if run_id already exists to avoid duplicates
    existing_ids = {r.get('run_id') for r in results_list}
    if run_id not in existing_ids:
        results_list.append(result)
    
    # Write back
    with open(output_path, 'w') as f:
        json.dump(results_list, f, indent=2)
        
    return result

def main():
    """CLI entry point for verification (optional, mostly used internally)."""
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

if __name__ == '__main__':
    import argparse
    main()
