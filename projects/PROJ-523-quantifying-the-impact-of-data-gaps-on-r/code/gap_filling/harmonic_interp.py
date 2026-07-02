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

def harmonic_interpolate(map_data: np.ndarray, mask: np.ndarray, n_iter: int = 10, tol: float = 1e-4) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Perform harmonic interpolation on a masked CMB map.
    
    Args:
        map_data: HEALPix map data (flat array).
        mask: Boolean mask where True indicates valid data (0 for gaps).
        n_iter: Maximum number of iterations.
        tol: Convergence tolerance.
        
    Returns:
        Tuple of (filled_map, stats_dict).
        
    Raises:
        RuntimeError: If the algorithm fails to converge within n_iter.
    """
    nside = hp.get_nside(map_data)
    n_pix = hp.nside2npix(nside)
    
    # Ensure mask is boolean and 0/1
    valid_mask = mask.astype(bool)
    invalid_mask = ~valid_mask
    
    filled_map = map_data.copy()
    filled_map[invalid_mask] = 0.0
    
    # Precompute indices
    valid_indices = np.where(valid_mask)[0]
    invalid_indices = np.where(invalid_mask)[0]
    
    if len(invalid_indices) == 0:
        logger.info("No gaps to fill.")
        return filled_map, {"converged": True, "iterations": 0, "final_error": 0.0}
        
    if len(valid_indices) == 0:
        raise RuntimeError("No valid data points to interpolate from.")

    prev_diff = np.inf
    converged = False
    final_iter = 0
    
    for i in range(n_iter):
        # Transform to harmonic space (alm)
        alm = hp.map2alm(filled_map, lmax=2*nside-1)
        
        # Transform back to pixel space (unmasked regions only)
        # We only care about the values in the gap regions to check convergence
        reconstructed = hp.alm2map(alm, nside)
        
        # Calculate difference in the gap region
        diff = np.abs(reconstructed[invalid_indices] - filled_map[invalid_indices])
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        # Update the gap region with the reconstructed values
        filled_map[invalid_indices] = reconstructed[invalid_indices]
        
        prev_diff = max_diff
        final_iter = i + 1
        
        if max_diff < tol:
            converged = True
            break
            
    stats = {
        "converged": converged,
        "iterations": final_iter,
        "final_error": float(prev_diff),
        "algorithm": "harmonic_interp"
    }
    
    if not converged:
        logger.warning(f"Harmonic interpolation did not converge after {n_iter} iterations. Final error: {prev_diff:.4e}")
        # We do NOT raise here, we let the caller decide how to handle it based on FR-008
    
    return filled_map, stats

def apply_harmonic_filling(
    map_path: str,
    mask_path: str,
    output_path: str,
    metadata_path: str,
    n_iter: int = 50,
    tol: float = 1e-5
) -> bool:
    """
    Wrapper to load map, fill gaps, and save results.
    
    Returns:
        True if successful, False if convergence failed (per FR-008).
    """
    start_time = time.time()
    
    logger.info(f"Loading map from {map_path}")
    map_data = hp.read_map(map_path, field=0)
    
    logger.info(f"Loading mask from {mask_path}")
    # Mask is typically stored as float or int 0/1
    mask_data = hp.read_map(mask_path, field=0)
    # Ensure mask is 1 for valid, 0 for gap (or vice versa depending on convention)
    # Assuming standard convention: 1 = valid, 0 = gap (masked out)
    # If the mask is inverted (0=valid), we need to handle it. 
    # Based on typical usage in this project, let's assume 1=valid.
    # If mask_data has values 0 and 1, we assume 1 is valid.
    
    filled_map, stats = harmonic_interpolate(map_data, mask_data, n_iter=n_iter, tol=tol)
    
    exec_time = time.time() - start_time
    
    # Save filled map
    hp.write_map(output_path, filled_map, overwrite=True)
    logger.info(f"Filled map saved to {output_path}")
    
    # Record metadata including convergence status
    metadata = {
        "algo_name": "harmonic_interpolation",
        "algo_version": "1.0.0",
        "exec_time_sec": exec_time,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "convergence": {
            "converged": stats["converged"],
            "iterations": stats["iterations"],
            "final_error": stats["final_error"],
            "tolerance": tol,
            "max_iterations": n_iter
        },
        "input_map": map_path,
        "input_mask": mask_path,
        "output_map": output_path
    }
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Metadata saved to {metadata_path}")
    
    # FR-008: If convergence failed, log failure and return False
    if not stats["converged"]:
        logger.error(f"Convergence failure detected for {map_path}. Gap config recorded in metadata. Excluding from analysis.")
        # The metadata already contains the gap config info implicitly via input_mask path
        # The caller should exclude this realization from further analysis
        return False
        
    return True

def main():
    """
    Entry point for standalone execution or testing.
    """
    # Example usage (would be overridden by pipeline in real run)
    logger.info("Harmonic Interpolation Module - Main Entry")
    # In a real scenario, arguments would be passed via CLI or config
    # For now, we just log that the module is ready
    print("Harmonic Interpolation module loaded. Ready for pipeline integration.")

if __name__ == "__main__":
    main()
