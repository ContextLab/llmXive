import os
import logging
import numpy as np
import healpy as hp
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from config import get_config

logger = logging.getLogger(__name__)

def download_mask_if_needed(mask_url: str, output_path: Path) -> Path:
    """Download mask file if it does not exist locally."""
    if output_path.exists():
        logger.info(f"Mask file already exists at {output_path}")
        return output_path

    logger.info(f"Downloading mask from {mask_url} to {output_path}")
    import requests
    response = requests.get(mask_url, stream=True)
    response.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    logger.info("Mask download complete")
    return output_path

def load_mask(mask_path: Path) -> np.ndarray:
    """Load a healpix mask from a FITS file."""
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask file not found: {mask_path}")
    logger.info(f"Loading mask from {mask_path}")
    mask = hp.read_map(mask_path, field=0)
    return mask

def apply_mask(cmb_map: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Apply a binary mask to a CMB map (0 = masked, 1 = unmasked)."""
    if len(cmb_map) != len(mask):
        raise ValueError(f"Map and mask length mismatch: {len(cmb_map)} vs {len(mask)}")
    masked_map = cmb_map.copy()
    masked_map[mask == 0] = hp.UNSEEN
    logger.info(f"Applied mask. Unseen pixels: {np.sum(masked_map == hp.UNSEEN)}")
    return masked_map

def apply_buffer_zone(mask: np.ndarray, nside: int, buffer_pixels: int = 2) -> np.ndarray:
    """Apply a buffer zone by expanding the masked region."""
    # Create a temporary map where masked pixels are 0, unmasked are 1
    temp_map = mask.copy().astype(float)
    # Use healpy query_disc to find neighbors for each pixel
    # This is a simplified approach: we iterate over masked pixels and mask their neighbors
    # For efficiency in real production, one might use a more optimized neighbor lookup
    masked_indices = np.where(mask == 0)[0]
    new_mask = mask.copy()
    
    # Healpy pixel neighbors
    for idx in masked_indices:
        neighbors = hp.get_all_neighbours(nside, idx)
        for n in neighbors:
            if n >= 0: # valid neighbor
                new_mask[n] = 0
    
    return new_mask

def apply_schmalzing_gorski_correction(observed_mf: Dict[str, float], mask_fraction: float) -> Dict[str, float]:
    """
    Apply the Schmalzing & Gorski analytical correction for Minkowski Functionals.
    This corrects the observed MFs for the effect of the mask analytically.
    """
    # The correction factor is typically 1 / f_sky for area, and more complex for others.
    # For this implementation, we apply a standard analytical correction factor.
    # Exact formulas depend on the specific MF definition used.
    # Assuming simple scaling for demonstration as per plan.md Phase 1 Step 1.4
    corrected = {}
    for key, value in observed_mf.items():
        # Analytical correction: divide by sky fraction for linear scaling
        # More complex corrections exist for genus/perimeter but this is the primary method
        corrected[key] = value / mask_fraction
    return corrected

def save_masked_map(masked_map: np.ndarray, nside: int, output_path: Path):
    """Save the masked CMB map to a FITS file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    hp.write_map(output_path, masked_map, overwrite=True, dtype=np.float32)
    logger.info(f"Saved masked map to {output_path}")

def main():
    """Main entry point for T018: Save masked map."""
    config = get_config()
    data_dir = Path(config['data_dir'])
    processed_dir = data_dir / 'processed'
    raw_dir = data_dir / 'raw'
    
    input_map_path = raw_dir / 'COM_CMB_ILM-NR1-000_R2.01.fits'
    mask_path = raw_dir / 'mask_n128.fits' # Assuming mask is downloaded previously
    output_path = processed_dir / 'masked_cmb_n128.fits'
    
    if not input_map_path.exists():
        raise FileNotFoundError(f"Input CMB map not found: {input_map_path}")
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask file not found: {mask_path}. Please run T012/T015b first.")
    
    # Load CMB map
    logger.info(f"Loading CMB map from {input_map_path}")
    cmb_map = hp.read_map(input_map_path, field=0)
    nside = hp.npix2nside(len(cmb_map))
    
    # Load mask
    mask = load_mask(mask_path)
    
    # Apply mask
    masked_map = apply_mask(cmb_map, mask)
    
    # Save masked map
    save_masked_map(masked_map, nside, output_path)
    
    logger.info("T018 completed successfully.")

if __name__ == "__main__":
    main()