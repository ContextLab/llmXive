import os
import logging
import numpy as np
import healpy as hp
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from config import get_config
from setup_logging import get_logger

# Ensure the logger is configured
logger = get_logger(__name__)

def download_mask_if_needed(mask_path: Path) -> None:
    """
    Download the Galactic mask if it does not exist.
    Uses the Planck Legacy Archive mask (e.g., r41_mask.fits) or a standard
    U80/U70 mask. For this implementation, we assume a standard mask path
    or fetch from a known URL if missing.
    """
    if mask_path.exists():
        logger.info(f"Mask already exists at {mask_path}")
        return

    logger.info(f"Downloading mask to {mask_path}")
    # Placeholder for actual download logic using download_with_retry
    # In a real scenario, this would call the download module
    # For now, we assume the mask is provided or downloaded by T014
    raise FileNotFoundError(
        f"Mask file not found at {mask_path}. "
        "Please ensure T014 has successfully downloaded or provided the mask."
    )

def load_mask(mask_path: Path) -> np.ndarray:
    """
    Load the Galactic mask from a FITS file.
    Returns a numpy array of 0s (masked) and 1s (unmasked).
    """
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask file not found: {mask_path}")

    logger.info(f"Loading mask from {mask_path}")
    mask = hp.read_map(mask_path, field=0, dtype=None)
    # Ensure mask is binary (0 or 1)
    mask = (mask > 0.5).astype(float)
    logger.info(f"Mask loaded: {mask.size} pixels, unmasked fraction: {np.mean(mask):.4f}")
    return mask

def apply_mask(cmb_map: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """
    Apply the mask to the CMB map by setting masked pixels to 0.
    """
    if len(cmb_map) != len(mask):
        raise ValueError(f"Map and mask size mismatch: {len(cmb_map)} vs {len(mask)}")
    
    masked_map = cmb_map.copy()
    masked_map[mask == 0] = 0.0
    logger.info("Mask applied to CMB map")
    return masked_map

def apply_buffer_zone(mask: np.ndarray, nside: int, buffer_size: int = 2) -> np.ndarray:
    """
    Apply a pixel buffer zone to the mask as the PRIMARY method for edge handling.
    
    Algorithm: For each pixel, if distance to nearest masked pixel (0) <= buffer_size,
    set the pixel value to 0 (masked).
    
    This creates a "buffer" around the masked regions to avoid edge effects.
    
    Args:
        mask: Binary numpy array (1=unmasked, 0=masked)
        nside: HEALPix Nside parameter
        buffer_size: Number of pixels to buffer (default 2 per Spec Edge Cases)
    
    Returns:
        Modified mask with buffer zone applied
    """
    logger.info(f"Applying pixel buffer zone of size {buffer_size}")
    
    # Convert mask to boolean for easier manipulation
    # True = unmasked (1), False = masked (0)
    unmasked = mask > 0.5
    
    # Get the number of pixels
    n_pix = len(mask)
    
    # We need to find pixels within 'buffer_size' of a masked pixel
    # We'll use a distance transform approach on the HEALPix grid
    
    # Create a distance map initialized to infinity
    # We'll use a simple iterative approach: 
    # 1. Start with all masked pixels (distance 0)
    # 2. Propagate distance to neighbors up to buffer_size
    
    # Initialize distances: 0 for masked, infinity for unmasked
    distances = np.full(n_pix, np.inf)
    masked_pixels = np.where(mask <= 0.5)[0]
    distances[masked_pixels] = 0
    
    # Create a queue for BFS
    queue = list(masked_pixels)
    visited = set(masked_pixels)
    
    # HEALPix neighbor function
    # We'll use healpy's get_neighbors to find adjacent pixels
    
    current_distance = 0
    while current_distance < buffer_size and queue:
        next_queue = []
        for pix in queue:
            # Get neighbors of this pixel
            neighbors = hp.get_neighbors(nside, pix, inclusive=False)
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = current_distance + 1
                    next_queue.append(neighbor)
        queue = next_queue
        current_distance += 1
    
    # Set pixels within buffer_size to 0 (masked)
    buffer_mask = (distances <= buffer_size)
    mask[buffer_mask] = 0.0
    
    unmasked_count = np.sum(mask > 0.5)
    total_count = len(mask)
    logger.info(f"Buffer zone applied: {total_count - unmasked_count} pixels now masked "
                f"(including buffer). Unmasked fraction: {unmasked_count/total_count:.4f}")
    
    return mask

def save_masked_map(masked_map: np.ndarray, nside: int, output_path: Path) -> None:
    """
    Save the masked CMB map to a FITS file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hp.write_map(output_path, masked_map, overwrite=True)
    logger.info(f"Saved masked map to {output_path}")

def main() -> None:
    """
    Main function to orchestrate mask application and buffer zone.
    """
    config = get_config()
    nside = config.get('nside', 128)
    
    # Paths
    raw_dir = Path(config.get('data_raw_dir', 'data/raw'))
    processed_dir = Path(config.get('data_processed_dir', 'data/processed'))
    
    cmb_map_path = raw_dir / "COM_CMB_ILM-NR1-000_R2.01.fits"
    mask_path = raw_dir / "r41_mask.fits"  # Example mask name
    output_path = processed_dir / "mask_with_buffer.fits"
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load CMB map
    logger.info(f"Loading CMB map from {cmb_map_path}")
    if not cmb_map_path.exists():
        raise FileNotFoundError(f"CMB map not found: {cmb_map_path}")
    
    cmb_map = hp.read_map(cmb_map_path, field=0, dtype=None)
    logger.info(f"CMB map loaded: {len(cmb_map)} pixels")
    
    # Load mask
    mask = load_mask(mask_path)
    
    # Apply buffer zone (PRIMARY method per Spec Edge Cases)
    mask = apply_buffer_zone(mask, nside, buffer_size=2)
    
    # Apply mask to CMB map
    masked_map = apply_mask(cmb_map, mask)
    
    # Save result
    save_masked_map(masked_map, nside, output_path)
    
    logger.info("Mask application and buffer zone completed successfully.")

if __name__ == "__main__":
    main()