import logging
import os
import sys
from pathlib import Path
from typing import Tuple, Dict, Any, List
import healpy as hp
import numpy as np
import json

from logging_config import get_logger
from config import ensure_directories, PROCESSED_MAP_FILENAME, HEMISPHERE_CL_FILENAME

logger = get_logger(__name__)

def compute_alm(map_data: np.ndarray, l_max: int = 128, m_max: int = None, iter: int = 3) -> np.ndarray:
    """
    Compute spherical harmonic coefficients (a_lm) from a CMB map.
    
    Args:
        map_data: Healpix map data (Npix,).
        l_max: Maximum l value.
        m_max: Maximum m value (defaults to l_max).
        iter: Number of iterations for iterative cleaning.
        
    Returns:
        Array of a_lm coefficients.
    """
    if map_data is None or len(map_data) == 0:
        raise ValueError("Map data cannot be empty")
        
    nside = hp.get_nside(map_data)
    logger.info(f"Computing a_lm for Nside={nside}, l_max={l_max}, iter={iter}")
    
    alm = hp.map2alm(map_data, lmax=l_max, mmax=m_max, iter=iter, use_pixel_weights=True)
    logger.info(f"Computed a_lm with {len(alm)} coefficients")
    return alm

def compute_full_sky_cl(alm: np.ndarray, lmax: int = 128) -> np.ndarray:
    """
    Compute angular power spectrum C_l from a_lm coefficients.
    
    Args:
        alm: Spherical harmonic coefficients.
        lmax: Maximum l value.
        
    Returns:
        Array of C_l values for l in [0, lmax].
    """
    if alm is None:
        raise ValueError("a_lm data cannot be empty")
        
    logger.info(f"Computing full-sky C_l up to l={lmax}")
    cl = hp.alm2cl(alm, lmax=lmax)
    logger.info(f"Computed C_l with {len(cl)} values")
    return cl

def split_hemispheres(nside: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate pixel masks for North/South and East/West hemispheres.
    
    Args:
        nside: Healpix Nside resolution.
        
    Returns:
        Tuple of (north_mask, south_mask, east_mask, west_mask) as boolean arrays.
    """
    n_pix = hp.nside2npix(nside)
    theta, phi = hp.pix2ang(nside, np.arange(n_pix))
    
    # North/South split (based on theta, where 0 is North Pole)
    north_mask = theta < np.pi / 2
    south_mask = theta >= np.pi / 2
    
    # East/West split (based on phi)
    east_mask = phi < np.pi
    west_mask = phi >= np.pi
    
    logger.info(f"Generated hemispherical masks for Nside={nside}")
    logger.info(f"North: {np.sum(north_mask)}, South: {np.sum(south_mask)}, East: {np.sum(east_mask)}, West: {np.sum(west_mask)}")
    
    return north_mask, south_mask, east_mask, west_mask

def compute_hemisphere_cl(map_data: np.ndarray, alm: np.ndarray, mask: np.ndarray, lmax: int = 128) -> np.ndarray:
    """
    Compute pseudo-C_l for a masked hemisphere using MASTER-like correction.
    
    Args:
        map_data: Full map data.
        alm: Full map a_lm coefficients (for window function correction).
        mask: Boolean mask for the hemisphere.
        lmax: Maximum l value.
        
    Returns:
        Array of C_l values for the masked region.
    """
    if mask is None or len(mask) == 0:
        raise ValueError("Mask cannot be empty")
        
    logger.info(f"Computing hemisphere C_l with {np.sum(mask)} pixels")
    
    # Apply mask
    masked_map = map_data.copy()
    masked_map[~mask] = 0.0
    
    # Compute a_lm for masked map
    alm_masked = hp.map2alm(masked_map, lmax=lmax, iter=0)
    
    # Compute pseudo-C_l
    cl_pseudo = hp.alm2cl(alm_masked, lmax=lmax)
    
    # Simple correction: normalize by sky fraction squared
    f_sky = np.sum(mask) / len(mask)
    if f_sky > 0:
        cl_corrected = cl_pseudo / (f_sky ** 2)
    else:
        raise ValueError("Sky fraction is zero, cannot correct")
        
    logger.info(f"Computed hemisphere C_l with sky fraction {f_sky:.4f}")
    return cl_corrected

def compute_per_axis_power_spectra(map_data: np.ndarray, lmax: int = 128) -> Dict[str, np.ndarray]:
    """
    Integrate hemispherical masks and compute per-axis power spectra.
    
    This function:
    1. Generates North/South and East/West hemispherical masks.
    2. Computes a_lm for the full map.
    3. Computes pseudo-C_l for each hemisphere with MASTER correction.
    4. Returns a dictionary of spectra for each axis.
    
    Args:
        map_data: Processed CMB map (Nside=128).
        lmax: Maximum l value.
        
    Returns:
        Dictionary with keys 'north', 'south', 'east', 'west' mapping to C_l arrays.
    """
    if map_data is None or len(map_data) == 0:
        raise ValueError("Map data cannot be empty")
        
    logger.info("Starting per-axis power spectrum computation")
    
    nside = hp.get_nside(map_data)
    logger.info(f"Map Nside: {nside}")
    
    # Compute full-sky a_lm
    alm = compute_alm(map_data, l_max=lmax, iter=3)
    
    # Generate hemispherical masks
    north_mask, south_mask, east_mask, west_mask = split_hemispheres(nside)
    
    # Compute spectra for each hemisphere
    cl_north = compute_hemisphere_cl(map_data, alm, north_mask, lmax)
    cl_south = compute_hemisphere_cl(map_data, alm, south_mask, lmax)
    cl_east = compute_hemisphere_cl(map_data, alm, east_mask, lmax)
    cl_west = compute_hemisphere_cl(map_data, alm, west_mask, lmax)
    
    logger.info("Completed per-axis power spectrum computation")
    
    return {
        'north': cl_north,
        'south': cl_south,
        'east': cl_east,
        'west': cl_west
    }

def save_hemisphere_spectra(spectra: Dict[str, np.ndarray], output_path: str) -> None:
    """
    Save hemispherical power spectra to a numpy file.
    
    Args:
        spectra: Dictionary of spectra.
        output_path: Path to save the .npy file.
    """
    if not spectra:
        raise ValueError("Spectra dictionary cannot be empty")
        
    logger.info(f"Saving hemispherical spectra to {output_path}")
    
    # Save as structured dictionary
    np.save(output_path, spectra, allow_pickle=True)
    
    logger.info(f"Saved spectra with keys: {list(spectra.keys())}")

def main() -> None:
    """
    Main entry point for computing per-axis power spectra.
    
    Reads the processed map, computes hemispherical spectra, and saves results.
    """
    ensure_directories()
    
    # Load processed map
    map_path = str(Path("data/processed") / PROCESSED_MAP_FILENAME)
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"Processed map not found at {map_path}")
        
    logger.info(f"Loading processed map from {map_path}")
    map_data = hp.read_map(map_path)
    
    # Compute per-axis power spectra
    spectra = compute_per_axis_power_spectra(map_data, lmax=128)
    
    # Save results
    output_dir = Path("data/reports")
    output_path = str(output_dir / HEMISPHERE_CL_FILENAME)
    save_hemisphere_spectra(spectra, output_path)
    
    logger.info(f"Per-axis power spectra saved to {output_path}")
    
    # Print summary
    print("Per-axis power spectra computed:")
    for axis, cl in spectra.items():
        print(f"  {axis}: l=2..128, mean C_l = {np.mean(cl[2:]):.6e}, std = {np.std(cl[2:]):.6e}")

if __name__ == "__main__":
    main()