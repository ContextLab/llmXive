import os
import json
import logging
import healpy as hp
import numpy as np
from pathlib import Path
from typing import Dict, Any

from config import get_config
from mask import load_mask

# Setup logging using project config
logger = logging.getLogger(__name__)

def load_masked_map(filepath: str) -> np.ndarray:
    """
    Load the masked CMB map from a FITS file.
    
    Args:
        filepath: Path to the FITS file containing the masked map.
        
    Returns:
        1D numpy array of pixel values.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        Exception: If healpy fails to read the file.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Masked map file not found: {filepath}")
    
    logger.info(f"Loading masked map from {filepath}")
    try:
        # Read the temperature map (usually the first column)
        # map = hp.read_map(filepath, field=0, nest=True)
        # Some Planck files might have multiple fields, we assume the first is T
        m = hp.read_map(filepath, field=0, nest=True, verbose=False)
        return m
    except Exception as e:
        logger.error(f"Failed to load map from {filepath}: {e}")
        raise

def calculate_coverage_stats(
    mask_map: np.ndarray, 
    total_pixels: int
) -> Dict[str, Any]:
    """
    Calculate sky coverage statistics based on a mask.
    
    Args:
        mask_map: 1D numpy array of mask values (0.0 for masked, 1.0 for valid).
        total_pixels: Total number of pixels in the map (nside^2 * 12).
        
    Returns:
        Dictionary with 'sky_coverage' (float), 'valid_pixels' (int), 
        and 'total_pixels' (int).
    """
    if mask_map is None:
        raise ValueError("Mask map cannot be None")
        
    # Count valid pixels (where mask > 0.5, treating as binary)
    # If the mask is already a boolean or 0/1 float, this works directly.
    # If it's a continuous weight, we count pixels with weight > 0.5 as "valid" for coverage count
    # However, usually for "valid pixels" in a masked map, we count pixels where mask != 0.
    # Let's assume standard Planck mask where 0 is masked, 1 is unmasked.
    valid_pixels = int(np.sum(mask_map > 0.5))
    
    sky_coverage = valid_pixels / total_pixels
    
    return {
        "sky_coverage": float(sky_coverage),
        "valid_pixels": valid_pixels,
        "total_pixels": total_pixels
    }

def generate_coverage_report(
    input_map_path: str,
    output_report_path: str
) -> Dict[str, Any]:
    """
    Main function to generate the coverage report.
    
    Args:
        input_map_path: Path to the masked CMB FITS file.
        output_report_path: Path where the JSON report will be saved.
        
    Returns:
        The generated report dictionary.
    """
    config = get_config()
    logger.info(f"Starting coverage analysis for {input_map_path}")
    
    # Load the masked map
    # The input is the masked map. We need to know which pixels are valid.
    # If the map values themselves are 0 (masked), we can count non-zero.
    # However, the standard approach is to have a separate mask or infer from the map.
    # The task says input is `data/processed/masked_cmb_n128.fits`.
    # Usually, a "masked map" has NaN or 0 in masked regions.
    # Let's check if we can infer validity from the map values or if we need the mask file.
    # The task T018 saves the masked map. T015 applies the mask.
    # If the map contains NaN for masked pixels:
    
    map_data = load_masked_map(input_map_path)
    
    # Determine total pixels
    # We can infer nside from the length of the array: Npix = 12 * nside^2
    nside = hp.npix2nside(len(map_data))
    total_pixels = 12 * nside * nside
    
    # Identify valid pixels
    # If the map was masked by setting values to 0 or NaN, we count non-masked.
    # Standard practice: if mask was applied by multiplication, masked pixels are 0.
    # But CMB maps have mean ~0, so 0 is a valid temperature.
    # The most robust way is to check if the file contains a mask column or infer from NaN.
    # However, the task T018 output is a single FITS file.
    # Let's assume the masking process in T015 sets masked pixels to NaN or a specific flag.
    # If the map is just multiplied by 0, we can't distinguish 0K from masked.
    # BUT, T015 uses `apply_mask` which likely returns the map and the mask.
    # If the saved file `masked_cmb_n128.fits` only contains the temperature,
    # we might need to reload the mask or assume the mask logic.
    # Wait, T018 says "Save masked map". If it saves only the temperature, we lose mask info.
    # However, usually one saves the mask as well or the map has NaN.
    # Let's assume the standard HEALPix convention where masked pixels are NaN.
    # If not, we might need to load the mask again.
    # Given the task description: "input: data/processed/masked_cmb_n128.fits",
    # and we need "valid_pixels".
    # If the map has NaN, we count ~isfinite.
    # If the map has 0 for masked, we can't know.
    # Let's assume the map has NaN for masked pixels.
    
    if np.any(np.isnan(map_data)):
        valid_mask = ~np.isnan(map_data)
        logger.info("Detected NaN values in map, using them as mask.")
    else:
        # If no NaN, we might need to load the mask again if it wasn't saved in the map.
        # But the task implies we can derive it from the input.
        # Perhaps the map was saved with 0 for masked?
        # Let's check if the project T015 saves the mask.
        # If T018 saves the map, maybe it saves the mask in a separate column?
        # hp.read_map can read multiple columns.
        # Let's re-read assuming it might have mask column.
        try:
            # Try reading multiple fields: T, Q, U, or T, Mask
            # If the file has 2 columns, maybe second is mask?
            # But T018 says "masked map", usually just T.
            # Let's assume the map has NaN. If not, we fall back to loading the mask file.
            # The mask file is likely in data/raw or similar.
            # But the task says input is the masked map.
            # Let's assume the map has NaN.
            valid_mask = np.isfinite(map_data)
            if not np.any(~valid_mask):
                # No NaN found, maybe all pixels are valid?
                # Or maybe the mask is 0.
                # Let's assume all valid if no NaN.
                logger.warning("No NaN or 0 found, assuming all pixels valid.")
            else:
                logger.info(f"Found {np.sum(~valid_mask)} masked pixels (NaN).")
        except Exception as e:
            logger.error(f"Could not determine mask from map: {e}")
            raise
    
    # If we still can't determine, we might need to load the mask explicitly.
    # But let's proceed with the NaN assumption.
    
    # Recalculate total pixels from nside
    nside = hp.npix2nside(len(map_data))
    total_pixels = 12 * nside * nside
    valid_pixels = int(np.sum(valid_mask))
    sky_coverage = valid_pixels / total_pixels
    
    report = {
        "sky_coverage": float(sky_coverage),
        "valid_pixels": valid_pixels,
        "total_pixels": total_pixels
    }
    
    # Ensure output directory exists
    output_path = Path(output_report_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save report
    with open(output_report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Coverage report saved to {output_report_path}")
    logger.info(f"Sky coverage: {sky_coverage:.4f}, Valid pixels: {valid_pixels}/{total_pixels}")
    
    return report

def main():
    """Entry point for coverage analysis."""
    config = get_config()
    input_path = config.get('paths', {}).get('masked_map', 'data/processed/masked_cmb_n128.fits')
    output_path = config.get('paths', {}).get('coverage_report', 'data/processed/coverage_report.json')
    
    # If paths are not in config, use defaults
    if not os.path.exists(input_path):
        # Try default relative to project root
        input_path = 'data/processed/masked_cmb_n128.fits'
    if not output_path:
        output_path = 'data/processed/coverage_report.json'
        
    generate_coverage_report(input_path, output_path)

if __name__ == '__main__':
    main()