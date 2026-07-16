"""
Functions to compute angular power spectra (C_l) from HEALPix maps.
Optimized for memory by using float32 where precision allows.
"""
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import numpy as np
import healpy as hp
from config import N_SIDE, MAX_L, DATA_DERIVED_DIR, DATA_RESULTS_DIR, get_dtype, FORCE_FLOAT32

logger = logging.getLogger(__name__)

def compute_power_spectrum(map_data: np.ndarray, mask_data: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Computes the angular power spectrum C_l for a given map.
    Uses healpy.anafast.
    
    Args:
        map_data: HEALPix map (temperature or polarization).
        mask_data: Optional mask to apply.
    
    Returns:
        Array of C_l values up to l=MAX_L.
    """
    nside = hp.get_nside(map_data)
    lmax = min(MAX_L, 3 * nside - 1)
    
    # Ensure float32 if configured for memory savings
    if FORCE_FLOAT32 and map_data.dtype != np.float32:
        map_data = map_data.astype(np.float32)
    
    kwargs = {'lmax': lmax, 'use_pixel_weights': False}
    
    if mask_data is not None:
        kwargs['map1'] = map_data
        kwargs['map2'] = map_data
        kwargs['mask'] = mask_data
        # anafast with mask
        cl = hp.anafast(map_data, mask=mask_data, lmax=lmax)
    else:
        cl = hp.anafast(map_data, lmax=lmax)
    
    # Ensure output is float32 to save memory in downstream steps
    if FORCE_FLOAT32 and cl.dtype != np.float32:
        cl = cl.astype(np.float32)
        
    return cl

def save_power_spectrum_metadata(cl: np.ndarray, realization_id: str, algo_name: str, filepath: Path):
    """
    Saves metadata about the power spectrum computation.
    """
    metadata = {
        "realization_id": realization_id,
        "algorithm": algo_name,
        "nside": int(hp.get_nside(cl)), # Note: cl doesn't have nside, using default N_SIDE
        "lmax": int(len(cl) - 1),
        "timestamp": datetime.now().isoformat(),
        "dtype": str(cl.dtype),
        "force_float32": FORCE_FLOAT32
    }
    
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"Saved power spectrum metadata to {filepath}")

def process_realization_power_spectrum(map_path: Path, mask_path: Optional[Path], realization_id: str, algo_name: str) -> np.ndarray:
    """
    Loads a map and mask, computes the power spectrum, and saves metadata.
    """
    from data_io import load_map_from_fits, load_mask_from_fits
    
    logger.info(f"Processing power spectrum for {realization_id} using {algo_name}")
    
    # Load data
    map_data = load_map_from_fits(map_path)
    
    mask_data = None
    if mask_path and mask_path.exists():
        mask_data = load_mask_from_fits(mask_path)
    
    # Compute spectrum
    cl = compute_power_spectrum(map_data, mask_data)
    
    # Save metadata
    meta_path = DATA_RESULTS_DIR / f"ps_{realization_id}_{algo_name}_meta.json"
    save_power_spectrum_metadata(cl, realization_id, algo_name, meta_path)
    
    # Save spectrum to disk (as numpy array for efficiency)
    cl_path = DATA_RESULTS_DIR / f"ps_{realization_id}_{algo_name}.npy"
    np.save(cl_path, cl)
    
    logger.info(f"Power spectrum computed and saved to {cl_path}")
    return cl

def main():
    """
    Main entry point for testing power spectrum computation.
    """
    logging.basicConfig(level=logging.INFO)
    # Example usage would require actual files
    logger.info("Power spectra module loaded. Ready to process maps.")

if __name__ == "__main__":
    main()
