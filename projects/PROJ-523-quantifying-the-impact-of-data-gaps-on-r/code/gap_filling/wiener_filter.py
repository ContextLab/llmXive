"""
Wiener Filtering Gap Filling Algorithm.

Implements Wiener filtering to reconstruct CMB maps from incomplete data.
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

def compute_noise_power_spectrum(nside: int, noise_level: float = 1e-3) -> np.ndarray:
    """
    Computes a simple white noise power spectrum.
    """
    lmax = 3 * nside - 1
    ell = np.arange(lmax + 1)
    # White noise: constant Cl
    cl_n = np.ones(lmax + 1) * noise_level
    return cl_n

def compute_signal_power_spectrum(nside: int, lmax: Optional[int] = None) -> np.ndarray:
    """
    Computes a theoretical signal power spectrum (simplified CMB).
    In a real run, this would load from CAMB or a file.
    """
    if lmax is None:
        lmax = 3 * nside - 1
    ell = np.arange(lmax + 1)
    # Simple power law approximation
    cl_s = np.zeros(lmax + 1)
    # Avoid division by zero at l=0
    cl_s[1:] = 1.0 / (ell[1:] ** 2) 
    cl_s[0] = 0.0 # Monopole removed
    return cl_s

def wiener_filter_map(
    input_map: np.ndarray,
    mask: np.ndarray,
    cl_signal: np.ndarray,
    cl_noise: np.ndarray,
    lmax: Optional[int] = None
) -> np.ndarray:
    """
    Applies a Wiener filter to the input map.
    
    Args:
        input_map: Input map with gaps (NaNs).
        mask: Boolean mask (True=valid, False=gap).
        cl_signal: Signal power spectrum.
        cl_noise: Noise power spectrum.
        lmax: Maximum multipole.
    
    Returns:
        Filtered map.
    """
    nside = hp.get_nside(input_map)
    if lmax is None:
        lmax = 3 * nside - 1
    
    # Prepare mask map (1 for valid, 0 for gap)
    mask_map = mask.astype(float)
    
    # Initialize the map with zeros in gaps for the transform
    # We assume input_map has NaNs in gaps, replace with 0 temporarily
    clean_map = input_map.copy()
    nan_mask = np.isnan(clean_map)
    clean_map[nan_mask] = 0.0
    
    # Combine signal and noise
    cl_total = cl_signal + cl_noise
    
    # Wiener filter in harmonic space
    # W_l = Cl_signal / (Cl_signal + Cl_noise)
    # Note: This is a simplified diagonal approximation. 
    # Full Wiener filtering involves matrix inversion which is expensive.
    # For this implementation, we use the diagonal approximation which is standard
    # for initial gap filling checks.
    
    alm_in = hp.map2alm(clean_map, lmax=lmax, use_weights=True)
    
    # Apply filter
    alm_filtered = hp.almxfl(alm_in, cl_signal / (cl_total + 1e-10))
    
    # Transform back
    filtered_map = hp.alm2map(alm_filtered, nside, lmax=lmax)
    
    # Blend: Use filtered values in gaps, original values elsewhere
    # Ensure we don't introduce NaNs from the original gaps
    final_map = np.where(mask_map > 0, input_map, filtered_map)
    
    return final_map

def apply_wiener_filling(
    input_map: np.ndarray,
    mask: np.ndarray,
    realization_id: str,
    algo_name: str = "wiener_filter",
    noise_level: float = 1e-3
) -> np.ndarray:
    """
    Wrapper for Wiener filtering with NaN Guarding.
    
    Args:
        input_map: Input map.
        mask: Valid pixel mask.
        realization_id: ID for logging.
        algo_name: Algorithm name.
        noise_level: Assumed noise level.
    
    Returns:
        Filled map.
    
    Raises:
        NaNPropagationError: If output contains NaNs.
    """
    logger.info(f"Applying Wiener Filter for {realization_id}")
    start_time = time.time()
    
    try:
        nside = hp.get_nside(input_map)
        cl_sig = compute_signal_power_spectrum(nside)
        cl_noise = compute_noise_power_spectrum(nside, noise_level)
        
        filled_map = wiener_filter_map(input_map, mask, cl_sig, cl_noise)
        
        # T043: Explicit NaN check
        scan_for_nans(filled_map, realization_id, algo_name)
        
        exec_time = time.time() - start_time
        logger.info(f"Wienner filter completed for {realization_id} in {exec_time:.2f}s")
        
        return filled_map
        
    except NaNPropagationError:
        raise
    except Exception as e:
        logger.error(f"Wiener filter failed for {realization_id}: {e}")
        log_convergence_failure(realization_id, algo_name, str(e))
        raise

def main():
    """
    Minimal execution test for Wiener Filter.
    """
    logging.basicConfig(level=logging.INFO)
    
    nside = 16
    npix = hp.nside2npix(nside)
    test_map = np.random.randn(npix)
    
    mask = np.ones(npix, dtype=bool)
    mask[0:10] = False
    test_map[0:10] = np.nan
    
    try:
        result = apply_wiener_filling(test_map, mask, "test_002", "wiener_filter")
        print(f"Success: Map filled. Shape: {result.shape}, Has NaNs: {np.any(np.isnan(result))}")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    main()
