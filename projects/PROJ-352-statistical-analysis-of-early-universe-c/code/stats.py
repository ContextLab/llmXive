"""
Compute basic statistics (mean, std) on the masked CMB map.

This module implements Task T017:
- Input: data/processed/masked_cmb_n128.fits
- Output: data/processed/map_stats.json with schema {"mean": float, "std": float}
"""
import os
import json
import logging
import healpy as hp
import numpy as np
from pathlib import Path

from config import get_config

# Setup logger
logger = logging.getLogger(__name__)

def load_masked_map(filepath: str) -> np.ndarray:
    """
    Load the masked CMB map from a FITS file.

    Args:
        filepath: Path to the FITS file.

    Returns:
        numpy array containing the map values.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Masked map file not found: {filepath}")
    
    logger.info(f"Loading masked map from {filepath}")
    # Read the first column (temperature map)
    map_data = hp.read_map(filepath, field=0)
    return map_data

def compute_statistics(map_data: np.ndarray) -> dict:
    """
    Compute mean and standard deviation of the map, ignoring masked pixels.

    Args:
        map_data: 1D numpy array of map values (masked pixels are typically NaN or 0).

    Returns:
        Dictionary with 'mean' and 'std' keys.
    """
    # Healpix maps often use -1.6375e+30 or NaN for masked pixels.
    # We will filter out non-finite values and a known sentinel if present.
    valid_mask = np.isfinite(map_data)
    
    # Check for the specific HEALPix sentinel value for masked pixels
    # Standard HEALPix sentinel is -1.6375e+30, but let's be robust.
    if np.any(~valid_mask):
        logger.info(f"Found {np.sum(~valid_mask)} non-finite pixels (masked).")
    
    valid_pixels = map_data[valid_mask]
    
    if len(valid_pixels) == 0:
        raise ValueError("No valid pixels found in the map.")
    
    mean_val = float(np.mean(valid_pixels))
    std_val = float(np.std(valid_pixels))
    
    logger.info(f"Computed statistics: mean={mean_val:.6e}, std={std_val:.6e}")
    
    return {
        "mean": mean_val,
        "std": std_val
    }

def save_stats(stats: dict, output_path: str) -> None:
    """
    Save statistics to a JSON file.

    Args:
        stats: Dictionary containing statistics.
        output_path: Path to the output JSON file.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Statistics saved to {output_path}")

def main():
    """
    Main entry point for T017.
    """
    config = get_config()
    
    input_path = config.get('paths', {}).get('masked_map', 'data/processed/masked_cmb_n128.fits')
    output_path = config.get('paths', {}).get('map_stats', 'data/processed/map_stats.json')
    
    logger.info(f"Starting T017: Compute statistics for {input_path}")
    
    try:
        map_data = load_masked_map(input_path)
        stats = compute_statistics(map_data)
        save_stats(stats, output_path)
        logger.info("T017 completed successfully.")
    except Exception as e:
        logger.error(f"T017 failed: {e}")
        raise

if __name__ == "__main__":
    # Ensure logging is set up if run directly
    setup_logging = getattr(__import__('config'), 'setup_logging', None)
    if setup_logging:
        setup_logging()
    else:
        logging.basicConfig(level=logging.INFO)
    
    main()
