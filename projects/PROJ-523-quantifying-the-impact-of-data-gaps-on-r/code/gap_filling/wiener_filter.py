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

def compute_noise_power_spectrum(mask: np.ndarray, noise_level: float = 1.0) -> np.ndarray:
    """
    Compute a simplified noise power spectrum based on mask and noise level.
    In a real scenario, this would be derived from instrument specifications.
    """
    nside = hp.get_nside(mask)
    l_max = 2 * nside - 1
    l = np.arange(l_max + 1)
    
    # Simplified: white noise spectrum
    # C_l = noise_variance * (4 * pi) / N_pix
    n_pix = hp.nside2npix(nside)
    noise_var = noise_level ** 2
    cl_noise = (4 * np.pi * noise_var) / n_pix * np.ones_like(l, dtype=float)
    
    return cl_noise

def compute_signal_power_spectrum(nside: int, l_max: int = None) -> np.ndarray:
    """
    Compute theoretical CMB power spectrum using a simple model.
    In production, this should use CAMB or similar.
    """
    if l_max is None:
        l_max = 2 * nside - 1
        
    l = np.arange(l_max + 1)
    # Simple power law approximation for demonstration
    # C_l ~ A * l^(-2) for l > 0
    cl_signal = np.zeros_like(l, dtype=float)
    cl_signal[1:] = 1e-10 * (l[1:] ** -2)
    cl_signal[0] = 1e-9  # Monopole
    
    return cl_signal

def wiener_filter_map(
    map_data: np.ndarray,
    mask: np.ndarray,
    cl_signal: np.ndarray,
    cl_noise: np.ndarray,
    l_max: int = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply Wiener filtering to a masked map.
    
    Args:
        map_data: Observed map (with gaps).
        mask: Boolean mask (True = valid).
        cl_signal: Theoretical signal power spectrum.
        cl_noise: Noise power spectrum.
        l_max: Maximum multipole moment.
        
    Returns:
        Tuple of (filtered_map, stats_dict).
    """
    nside = hp.get_nside(map_data)
    if l_max is None:
        l_max = 2 * nside - 1
        
    l = np.arange(l_max + 1)
    
    # Transform observed map to harmonic space
    # Use only valid pixels for alm calculation (healpy handles masking internally if mask is provided)
    # However, map2alm expects a full map. We will fill gaps with 0 and hope the filter corrects it.
    # A better approach is to use the mask to weight the map.
    
    # Create a weighted map: valid pixels * 1, gaps * 0
    weighted_map = map_data.copy()
    weighted_map[~mask.astype(bool)] = 0.0
    
    # Calculate alm from weighted map
    alm = hp.map2alm(weighted_map, lmax=l_max, use_pixel_weights=False)
    
    # Calculate Wiener filter coefficients
    # W_l = C_l^S / (C_l^S + C_l^N)
    # Handle division by zero
    denom = cl_signal + cl_noise
    denom[denom == 0] = 1e-30
    w_l = cl_signal / denom
    
    # Apply filter in harmonic space
    alm_filtered = hp.almxfl(alm, w_l, lmax=l_max)
    
    # Transform back to pixel space
    filtered_map = hp.alm2map(alm_filtered, nside)
    
    stats = {
        "algorithm": "wiener_filter",
        "l_max": l_max,
        "nside": nside
    }
    
    return filtered_map, stats

def apply_wiener_filling(
    map_path: str,
    mask_path: str,
    output_path: str,
    metadata_path: str,
    noise_level: float = 1.0,
    l_max: int = None
) -> bool:
    """
    Wrapper to load map, apply Wiener filter, and save results.
    
    Returns:
        True if successful, False if any critical failure occurs.
    """
    start_time = time.time()
    
    logger.info(f"Loading map from {map_path}")
    map_data = hp.read_map(map_path, field=0)
    
    logger.info(f"Loading mask from {mask_path}")
    mask_data = hp.read_map(mask_path, field=0)
    
    nside = hp.get_nside(map_data)
    if l_max is None:
        l_max = 2 * nside - 1
        
    logger.info("Computing signal and noise power spectra")
    cl_signal = compute_signal_power_spectrum(nside, l_max)
    cl_noise = compute_noise_power_spectrum(mask_data, noise_level)
    
    logger.info("Applying Wiener filter")
    filtered_map, stats = wiener_filter_map(map_data, mask_data, cl_signal, cl_noise, l_max)
    
    exec_time = time.time() - start_time
    
    # Save filtered map
    hp.write_map(output_path, filtered_map, overwrite=True)
    logger.info(f"Filtered map saved to {output_path}")
    
    # Record metadata
    metadata = {
        "algo_name": "wiener_filter",
        "algo_version": "1.0.0",
        "exec_time_sec": exec_time,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "parameters": {
            "noise_level": noise_level,
            "l_max": l_max
        },
        "input_map": map_path,
        "input_mask": mask_path,
        "output_map": output_path
    }
    
    os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
        
    logger.info(f"Metadata saved to {metadata_path}")
    
    # Wiener filter is generally stable, but we check for NaNs
    if np.any(np.isnan(filtered_map)) or np.any(np.isinf(filtered_map)):
        logger.error(f"Wiener filter produced NaN/Inf values for {map_path}. Excluding from analysis.")
        return False
        
    return True

def main():
    """
    Entry point for standalone execution.
    """
    logger.info("Wiener Filter Module - Main Entry")
    print("Wiener Filter module loaded. Ready for pipeline integration.")

if __name__ == "__main__":
    main()
