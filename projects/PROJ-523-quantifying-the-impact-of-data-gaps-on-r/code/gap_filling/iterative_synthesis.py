"""
Iterative Harmonic Synthesis Gap Filling Algorithm.

Implements an iterative synthesis approach to fill gaps.
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

def iterative_harmonic_synthesis(
    input_map: np.ndarray,
    mask: np.ndarray,
    n_iter: int = 20,
    tolerance: float = 1e-4
) -> np.ndarray:
    """
    Performs iterative harmonic synthesis to fill gaps.
    
    This method iteratively:
    1. Fills gaps with current estimate.
    2. Transforms to harmonic space.
    3. Transforms back.
    4. Replaces gap values with the synthesized values.
    5. Checks convergence.
    
    Args:
        input_map: Input map with gaps (NaNs).
        mask: Boolean mask (True=valid, False=gap).
        n_iter: Maximum iterations.
        tolerance: Convergence tolerance.
    
    Returns:
        Filled map.
    """
    nside = hp.get_nside(input_map)
    lmax = 3 * nside - 1
    
    # Initialize
    current_map = input_map.copy()
    nan_mask = np.isnan(current_map)
    current_map[nan_mask] = 0.0 # Zero fill initially
    
    prev_map = current_map.copy()
    
    for i in range(n_iter):
        # Transform to alm
        alm = hp.map2alm(current_map, lmax=lmax, use_weights=True)
        
        # Transform back
        synthesized = hp.alm2map(alm, nside, lmax=lmax)
        
        # Update only the gap regions
        # We take the synthesized value where mask is False (gap)
        # We keep the original value where mask is True
        current_map = np.where(mask, current_map, synthesized)
        
        # Check convergence in the gap region
        diff = np.abs(current_map[~mask] - prev_map[~mask])
        max_diff = np.max(diff)
        
        if max_diff < tolerance:
            logger.debug(f"Converged at iteration {i} with diff {max_diff}")
            break
        
        prev_map = current_map.copy()
    
    return current_map

def apply_iterative_filling(
    input_map: np.ndarray,
    mask: np.ndarray,
    realization_id: str,
    algo_name: str = "iterative_synthesis",
    n_iter: int = 20
) -> np.ndarray:
    """
    Wrapper for Iterative Synthesis with NaN Guarding.
    
    Args:
        input_map: Input map.
        mask: Valid pixel mask.
        realization_id: ID for logging.
        algo_name: Algorithm name.
        n_iter: Number of iterations.
    
    Returns:
        Filled map.
    
    Raises:
        NaNPropagationError: If output contains NaNs.
    """
    logger.info(f"Applying Iterative Synthesis for {realization_id}")
    start_time = time.time()
    
    try:
        filled_map = iterative_harmonic_synthesis(input_map, mask, n_iter=n_iter)
        
        # T043: Explicit NaN check
        scan_for_nans(filled_map, realization_id, algo_name)
        
        exec_time = time.time() - start_time
        logger.info(f"Iterative synthesis completed for {realization_id} in {exec_time:.2f}s")
        
        return filled_map
        
    except NaNPropagationError:
        raise
    except Exception as e:
        logger.error(f"Iterative synthesis failed for {realization_id}: {e}")
        log_convergence_failure(realization_id, algo_name, str(e))
        raise

def main():
    """
    Minimal execution test for Iterative Synthesis.
    """
    logging.basicConfig(level=logging.INFO)
    
    nside = 16
    npix = hp.nside2npix(nside)
    test_map = np.random.randn(npix)
    
    mask = np.ones(npix, dtype=bool)
    mask[0:10] = False
    test_map[0:10] = np.nan
    
    try:
        result = apply_iterative_filling(test_map, mask, "test_003", "iterative_synthesis", n_iter=10)
        print(f"Success: Map filled. Shape: {result.shape}, Has NaNs: {np.any(np.isnan(result))}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()