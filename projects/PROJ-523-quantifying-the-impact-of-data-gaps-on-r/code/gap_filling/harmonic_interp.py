"""
Harmonic Interpolation Gap Filling Algorithm.

Implements harmonic interpolation to fill gaps in CMB maps.
Integrates with the NaN Guard (T043) to ensure data integrity.
"""
import numpy as np
import healpy as hp
import logging
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from gap_filling.NaN_guard import scan_for_nans, apply_nan_guard_wrapper
from gap_filling.failure_handler import log_convergence_failure, record_excluded_realization

logger = logging.getLogger(__name__)

def harmonic_interpolate(
    input_map: np.ndarray,
    mask: np.ndarray,
    n_iter: int = 10,
    lmax: Optional[int] = None
) -> np.ndarray:
    """
    Performs harmonic interpolation to fill gaps.
    
    This implementation iteratively fills gaps by transforming to harmonic space,
    applying the mask, and transforming back, smoothing the gaps with surrounding
    pixels.
    
    Args:
        input_map: The input map with gaps (NaNs or masked).
        mask: Boolean mask where True indicates valid pixels, False indicates gaps.
        n_iter: Number of iterations for convergence.
        lmax: Maximum multipole moment. Defaults to 3 * Nside - 1.
    
    Returns:
        Filled map (numpy array).
    
    Raises:
        NaNPropagationError: If the output contains NaNs (caught by wrapper).
    """
    if lmax is None:
        nside = hp.get_nside(input_map)
        lmax = 3 * nside - 1
    
    # Ensure mask is boolean
    mask = mask.astype(bool)
    
    # Initialize filled map with input
    filled_map = input_map.copy()
    
    # Replace NaNs in input with zeros for the initial transform (will be overwritten)
    nan_mask = np.isnan(filled_map)
    filled_map[nan_mask] = 0.0
    
    logger.debug(f"Starting harmonic interpolation with {n_iter} iterations")
    
    for i in range(n_iter):
        # Transform to harmonic space
        alm = hp.map2alm(filled_map, lmax=lmax, use_weights=True)
        
        # Transform back to map space
        reconstructed = hp.alm2map(alm, hp.get_nside(input_map), lmax=lmax)
        
        # Update only the gap regions with the reconstructed values
        # (Keep original values where mask is True)
        filled_map = np.where(mask, filled_map, reconstructed)
        
        # Optional: Log progress every few iterations
        if i % 5 == 0 and i > 0:
            logger.debug(f"Iteration {i}: Max gap value diff = {np.max(np.abs(reconstructed - filled_map))}")

    return filled_map

def apply_harmonic_filling(
    input_map: np.ndarray,
    mask: np.ndarray,
    realization_id: str,
    algo_name: str = "harmonic_interp",
    n_iter: int = 10
) -> np.ndarray:
    """
    Wrapper for harmonic interpolation that includes NaN guarding.
    
    This function applies the NaN Guard (T043) immediately after filling.
    If NaNs are detected, it raises NaNPropagationError which triggers
    the exclusion logic in T024.
    
    Args:
        input_map: Input map with gaps.
        mask: Valid pixel mask.
        realization_id: ID of the realization for logging.
        algo_name: Name of the algorithm.
        n_iter: Number of iterations.
    
    Returns:
        Filled map.
    
    Raises:
        NaNPropagationError: If output contains NaNs.
    """
    logger.info(f"Applying Harmonic Interpolation for {realization_id}")
    start_time = time.time()
    
    try:
        # Create the wrapped function to ensure NaN check
        filled_map = harmonic_interpolate(input_map, mask, n_iter=n_iter)
        
        # Explicitly scan for NaNs (T043 requirement)
        scan_for_nans(filled_map, realization_id, algo_name)
        
        exec_time = time.time() - start_time
        logger.info(f"Harmonic interpolation completed for {realization_id} in {exec_time:.2f}s")
        
        return filled_map
        
    except NaNPropagationError:
        # Re-raise to be caught by the pipeline exclusion logic
        raise
    except Exception as e:
        logger.error(f"Harmonic interpolation failed for {realization_id}: {e}")
        # Log failure for T024 exclusion tracking
        log_convergence_failure(realization_id, algo_name, str(e))
        raise

def main():
    """
    Minimal execution test for Harmonic Interpolation.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Create a mock Nside=16 map
    nside = 16
    npix = hp.nside2npix(nside)
    test_map = np.random.randn(npix)
    
    # Create a mask with some gaps (set some pixels to 0)
    mask = np.ones(npix, dtype=bool)
    mask[0:10] = False # Create a small gap
    
    # Introduce NaNs in the gap region of the input map to simulate missing data
    test_map[0:10] = np.nan
    
    try:
        result = apply_harmonic_filling(test_map, mask, "test_001", "harmonic_interp", n_iter=5)
        print(f"Success: Map filled. Shape: {result.shape}, Has NaNs: {np.any(np.isnan(result))}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()
