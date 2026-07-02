import numpy as np
import healpy as hp
import logging
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import json
import os

from code.config import DATA_DERIVED_DIR, DATA_RESULTS_DIR, LOGS_DIR
from code.data_io import save_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def iterative_harmonic_synthesis(
    map_data: np.ndarray,
    mask: np.ndarray,
    n_iter: int = 20,
    tol: float = 1e-4,
    damping: float = 0.5
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Iterative Harmonic Synthesis for gap filling.
    
    This method iteratively fills gaps by transforming to harmonic space,
    applying a constraint, and transforming back.
    
    Args:
        map_data: Observed map.
        mask: Boolean mask (True = valid data).
        n_iter: Maximum iterations.
        tol: Convergence tolerance.
        damping: Damping factor for stability (0 < damping <= 1).
        
    Returns:
        Tuple of (filled_map, stats_dict).
    """
    nside = hp.get_nside(map_data)
    valid_mask = mask.astype(bool)
    invalid_mask = ~valid_mask
    
    filled_map = map_data.copy()
    # Initialize gaps with zeros or mean of valid data
    if np.any(invalid_mask):
        filled_map[invalid_mask] = np.mean(filled_map[valid_mask])
        
    prev_diff = np.inf
    converged = False
    final_iter = 0
    
    l_max = 2 * nside - 1
    
    for i in range(n_iter):
        # Transform to harmonic space
        alm = hp.map2alm(filled_map, lmax=l_max)
        
        # Transform back to pixel space
        reconstructed = hp.alm2map(alm, nside)
        
        # Update only the gap regions with a damping factor
        # new_value = old_value + damping * (reconstructed - old_value) in gaps
        diff = reconstructed - filled_map
        filled_map[invalid_mask] += damping * diff[invalid_mask]
        
        # Check convergence in the gap region
        gap_diff = np.abs(diff[invalid_mask])
        max_diff = np.max(gap_diff) if len(gap_diff) > 0 else 0.0
        
        final_iter = i + 1
        if max_diff < tol:
            converged = True
            break
            
        prev_diff = max_diff
        
    stats = {
        "algorithm": "iterative_synthesis",
        "converged": converged,
        "iterations": final_iter,
        "final_error": float(prev_diff),
        "tolerance": tol,
        "damping": damping
    }
    
    if not converged:
        logger.warning(f"Iterative synthesis did not converge after {n_iter} iterations. Final error: {prev_diff:.4e}")
        
    return filled_map, stats

def apply_iterative_filling(
    map_path: str,
    mask_path: str,
    output_path: str,
    metadata_path: str,
    n_iter: int = 50,
    tol: float = 1e-5,
    damping: float = 0.5
) -> bool:
    """
    Wrapper to load map, apply iterative synthesis, and save results.
    
    Returns:
        True if successful, False if convergence failed.
    """
    start_time = time.time()
    
    logger.info(f"Loading map from {map_path}")
    map_data = hp.read_map(map_path, field=0)
    
    logger.info(f"Loading mask from {mask_path}")
    mask_data = hp.read_map(mask_path, field=0)
    
    filled_map, stats = iterative_harmonic_synthesis(
        map_data, mask_data, n_iter=n_iter, tol=tol, damping=damping
    )
    
    exec_time = time.time() - start_time
    
    # Save filled map
    hp.write_map(output_path, filled_map, overwrite=True)
    logger.info(f"Filled map saved to {output_path}")
    
    # Record metadata
    metadata = {
        "algo_name": "iterative_harmonic_synthesis",
        "algo_version": "1.0.0",
        "exec_time_sec": exec_time,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "convergence": {
            "converged": stats["converged"],
            "iterations": stats["iterations"],
            "final_error": stats["final_error"],
            "tolerance": tol,
            "max_iterations": n_iter,
            "damping": damping
        },
        "input_map": map_path,
        "input_mask": mask_path,
        "output_map": output_path
    }
    
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Metadata saved to {metadata_path}")
    
    # FR-008: Handle convergence failure
    if not stats["converged"]:
        logger.error(f"Convergence failure detected for {map_path} (Iterative Synthesis). Gap config recorded in metadata. Excluding from analysis.")
        return False
        
    # Check for NaNs
    if np.any(np.isnan(filled_map)) or np.any(np.isinf(filled_map)):
        logger.error(f"Iterative synthesis produced NaN/Inf values for {map_path}. Excluding from analysis.")
        return False
        
    return True

def main():
    """
    Entry point for standalone execution.
    """
    logger.info("Iterative Synthesis Module - Main Entry")
    print("Iterative Synthesis module loaded. Ready for pipeline integration.")

if __name__ == "__main__":
    main()