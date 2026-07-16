"""
Utility functions for generating gap masks and handling HEALPix data.
Optimized for memory usage via float32 usage where applicable.
"""
import numpy as np
import healpy as hp
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from config import N_SIDE, DATA_DERIVED_DIR, GAP_FRACTIONS, GAP_MORPHOLOGIES, get_dtype, FORCE_FLOAT32

logger = logging.getLogger(__name__)

def get_available_gap_fractions() -> List[float]:
    """Returns the list of configured gap fractions."""
    return GAP_FRACTIONS

def generate_random_mask(nside: int, gap_fraction: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generates a random gap mask for the given Nside and gap fraction.
    Uses float32 for the mask array if FORCE_FLOAT32 is enabled.
    """
    if seed is not None:
        np.random.seed(seed)

    n_pixels = hp.nside2npix(nside)
    dtype = get_dtype()

    # Generate random values
    mask = np.random.random(n_pixels).astype(dtype)

    # Threshold to get desired fraction
    threshold = np.quantile(mask, 1.0 - gap_fraction)
    mask = (mask < threshold).astype(dtype)

    logger.info(f"Generated random mask: Nside={nside}, target_frac={gap_fraction:.2f}, actual_frac={mask.mean():.4f}")
    return mask

def generate_clustered_mask(nside: int, gap_fraction: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generates a clustered gap mask by creating a smooth field and thresholding.
    Uses float32 for intermediate fields if FORCE_FLOAT32 is enabled.
    """
    if seed is not None:
        np.random.seed(seed)

    n_pixels = hp.nside2npix(nside)
    dtype = get_dtype()

    # Create a smooth random field (low resolution then upsample)
    lmax = 10
    alm = hp.synalm(np.zeros(lmax * 2), lmax=lmax) # Placeholder, will replace with actual generation
    
    # Simpler approach: generate random centers and grow circles
    # To ensure memory efficiency, we work in float32
    mask = np.zeros(n_pixels, dtype=dtype)
    
    # Number of clusters
    n_clusters = max(1, int(gap_fraction * n_pixels / 100))
    
    for _ in range(n_clusters):
        # Random pixel index
        idx = np.random.randint(0, n_pixels)
        # Random radius (in pixels)
        radius = np.random.randint(5, 20)
        
        # Get pixels within radius
        ring = hp.query_disc(nside, hp.pix2vec(nside, idx), radius * (3.14159 / (6 * nside)))
        mask[ring] = 1.0

    # Normalize to exact fraction
    current_frac = mask.sum() / n_pixels
    if current_frac > gap_fraction:
        # Remove random pixels
        excess = int((current_frac - gap_fraction) * n_pixels)
        indices = np.where(mask == 1)[0]
        remove_idx = np.random.choice(indices, size=excess, replace=False)
        mask[remove_idx] = 0
    elif current_frac < gap_fraction:
        # Add random pixels
        needed = int((gap_fraction - current_frac) * n_pixels)
        indices = np.where(mask == 0)[0]
        add_idx = np.random.choice(indices, size=needed, replace=False)
        mask[add_idx] = 1

    logger.info(f"Generated clustered mask: Nside={nside}, target_frac={gap_fraction:.2f}, actual_frac={mask.mean():.4f}")
    return mask

def generate_point_source_mask(nside: int, gap_fraction: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generates a mask simulating point source holes.
    """
    if seed is not None:
        np.random.seed(seed)

    n_pixels = hp.nside2npix(nside)
    dtype = get_dtype()
    
    mask = np.zeros(n_pixels, dtype=dtype)
    
    # Point sources are small holes
    # Estimate number of sources needed to reach fraction
    # Assume each source covers ~10 pixels
    pixels_per_source = 10
    n_sources = int((gap_fraction * n_pixels) / pixels_per_source)
    
    for _ in range(n_sources):
        idx = np.random.randint(0, n_pixels)
        radius = 3 # Small radius
        ring = hp.query_disc(nside, hp.pix2vec(nside, idx), radius * (3.14159 / (6 * nside)))
        mask[ring] = 1.0

    logger.info(f"Generated point source mask: Nside={nside}, target_frac={gap_fraction:.2f}, actual_frac={mask.mean():.4f}")
    return mask

def generate_galactic_plane_mask(nside: int, gap_fraction: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generates a mask simulating the Galactic plane cut.
    """
    if seed is not None:
        np.random.seed(seed)

    n_pixels = hp.nside2npix(nside)
    dtype = get_dtype()
    
    # Get latitudes
    theta, phi = hp.pix2ang(nside, np.arange(n_pixels))
    lat = 90 - np.degrees(theta)
    
    mask = np.zeros(n_pixels, dtype=dtype)
    
    # Initial cut width (will adjust to match fraction)
    cut_lat = 20.0 
    mask[np.abs(lat) < cut_lat] = 1.0
    
    current_frac = mask.mean()
    
    # Adjust cut width to match target fraction
    # Simple binary search or linear adjustment
    while abs(current_frac - gap_fraction) > 0.001:
        if current_frac > gap_fraction:
            cut_lat -= 1.0
        else:
            cut_lat += 1.0
        
        mask = np.zeros(n_pixels, dtype=dtype)
        mask[np.abs(lat) < cut_lat] = 1.0
        current_frac = mask.mean()
        
        if cut_lat < 0 or cut_lat > 90:
            logger.warning("Could not match gap fraction with galactic plane cut.")
            break

    logger.info(f"Generated galactic plane mask: Nside={nside}, target_frac={gap_fraction:.2f}, actual_frac={mask.mean():.4f}")
    return mask

def generate_null_model_mask(nside: int, gap_fraction: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Generates a null model mask (random gaps uncorrelated with signal).
    This is effectively the same as random_mask.
    """
    return generate_random_mask(nside, gap_fraction, seed)

def validate_mask(mask: np.ndarray, nside: int, target_fraction: float, tolerance: float = 0.005) -> bool:
    """
    Validates that the mask has the correct shape and gap fraction within tolerance.
    """
    n_pixels = hp.nside2npix(nside)
    if mask.shape != (n_pixels,):
        logger.error(f"Mask shape {mask.shape} does not match expected {n_pixels}")
        return False
    
    actual_fraction = float(mask.mean())
    if abs(actual_fraction - target_fraction) > tolerance:
        logger.error(f"Gap fraction {actual_fraction:.4f} outside tolerance of {target_fraction:.4f} ± {tolerance}")
        return False
    
    return True

def save_mask_to_fits_wrapper(mask: np.ndarray, filepath: Path, realization_id: str, gap_fraction: float, mask_type: str):
    """
    Saves a mask to a FITS file.
    Ensures float32 is used for storage to save space if configured.
    """
    import healpy as hp
    from data_io import save_mask_to_fits
    
    # Ensure dtype is consistent
    if FORCE_FLOAT32 and mask.dtype != np.float32:
        mask = mask.astype(np.float32)
        
    save_mask_to_fits(mask, filepath)
    logger.info(f"Saved mask to {filepath}")

def create_mask_by_type(nside: int, gap_fraction: float, mask_type: str, seed: Optional[int] = None) -> np.ndarray:
    """
    Factory function to create a mask by type.
    """
    generators = {
        "random": generate_random_mask,
        "clustered": generate_clustered_mask,
        "point_source": generate_point_source_mask,
        "galactic_plane": generate_galactic_plane_mask,
        "null_model": generate_null_model_mask
    }
    
    if mask_type not in generators:
        raise ValueError(f"Unknown mask type: {mask_type}. Available: {list(generators.keys())}")
    
    return generators[mask_type](nside, gap_fraction, seed)
