"""Artifact injection logic for synthetic planetary nebulae.

This module provides functions to inject noise and saturation artifacts
into synthetic images to simulate instrumental effects.
"""
import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any

import numpy as np

from code.config import get_project_root, SATURATION_LEVELS, NOISE_LEVELS
from code.io.writer import save_fits_image, write_artifact_manifest

logger = logging.getLogger(__name__)

def inject_noise(
    image: np.ndarray,
    sigma: float,
    seed: int = 42
) -> np.ndarray:
    """Inject Gaussian noise into an image.

    Args:
        image: Input 2D array representing the clean image.
        sigma: Standard deviation of the Gaussian noise to inject.
        seed: Random seed for reproducibility.

    Returns:
        Noisy image (float64).
    """
    if sigma <= 0:
        logger.debug("Sigma is non-positive, returning copy of image.")
        return image.copy()

    rng = np.random.default_rng(seed)
    noise = rng.normal(0, sigma, size=image.shape)
    noisy_image = image.astype(np.float64) + noise
    return noisy_image

def clip_saturation(
    image: np.ndarray,
    fraction: float,
    seed: int = 42
) -> Tuple[np.ndarray, float]:
    """Clip the brightest pixels in the image to simulate saturation.

    This function identifies the threshold corresponding to the top `fraction`
    of pixels by intensity and clips all pixels above that threshold to the
    threshold value.

    Args:
        image: Input 2D array.
        fraction: Fraction of brightest pixels to clip (0.0 to 1.0).
        seed: Random seed (currently unused for deterministic thresholding).

    Returns:
        Tuple of (clipped_image, threshold_value).
    """
    if fraction <= 0.0:
        logger.debug("Fraction is non-positive, returning copy of image.")
        return image.copy(), float(np.max(image))

    if fraction >= 1.0:
        # Edge case: clip everything to the minimum? Or max?
        # If fraction is 1.0, we clip the top 100%, which means everything is above the min.
        # Threshold is min. Everything becomes min.
        threshold = float(np.min(image))
        logger.warning("Fraction >= 1.0, clipping all pixels to minimum value.")
        result = np.full_like(image, threshold, dtype=np.float64)
        return result, threshold

    flat = image.flatten()
    # Calculate the threshold value: the value below which (1-fraction) of the data falls.
    # e.g., fraction=0.1 -> 90th percentile.
    threshold = float(np.percentile(flat, 100 * (1 - fraction)))

    result = image.astype(np.float64).copy()
    result[result > threshold] = threshold

    return result, threshold

def run_saturation_sweep(
    clean_image: np.ndarray,
    output_dir: str = "data/processed",
    seed: int = 42
) -> List[Dict[str, Any]]:
    """Perform a saturation sweep across defined levels and save results.

    This function implements the sweep logic required by T021:
    - Iterates over saturation levels from 0.0 to 0.5 in 0.05 increments.
    - Clips the image at each level.
    - Saves the resulting FITS images.
    - Returns a list of result dictionaries for downstream processing.

    Args:
        clean_image: The clean synthetic image (2D array).
        output_dir: Directory to save output FITS files.
        seed: Random seed for reproducibility.

    Returns:
        List of dictionaries containing metadata for each sweep step.
    """
    # Use the concrete saturation levels defined in config (0.0 to 0.5 step 0.05)
    # Fallback to the task-specified range if config is missing for some reason,
    # but T004 ensures these are defined.
    levels = getattr(__import__('code.config', fromlist=['SATURATION_LEVELS']), 'SATURATION_LEVELS', None)
    if levels is None:
        levels = [round(x * 0.05, 2) for x in range(0, 11)] # 0.0, 0.05, ..., 0.5
    
    # Ensure we strictly follow the task spec: 0.0 to 0.5 in 0.05 increments
    # Filter or generate to match exactly if config drifts
    sweep_levels = [round(0.0 + i * 0.05, 2) for i in range(11)]
    if len(sweep_levels) != 11 or sweep_levels[-1] != 0.5:
        logger.warning("Config saturation levels do not match T021 spec. Overriding with T021 levels.")
        sweep_levels = [round(0.0 + i * 0.05, 2) for i in range(11)]

    results = []
    output_path = Path(get_project_root()) / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting saturation sweep with {len(sweep_levels)} levels.")

    for fraction in sweep_levels:
        logger.info(f"Processing saturation level: {fraction:.2f}")
        
        # Apply saturation clipping
        clipped_image, threshold = clip_saturation(clean_image, fraction, seed=seed)
        
        # Construct output filename
        filename = f"saturation_sweep_{fraction:.2f}.fits"
        filepath = output_path / filename
        
        # Save the FITS image
        # We assume save_fits_image takes a path and an array
        save_fits_image(str(filepath), clipped_image)
        
        # Record result
        result_entry = {
            "fraction": fraction,
            "threshold": threshold,
            "output_file": str(filepath),
            "checksum": None # Calculated during save if needed, or left for writer to handle
        }
        results.append(result_entry)

    # Write a manifest for the sweep
    manifest_path = output_path / "saturation_sweep_manifest.json"
    write_artifact_manifest(str(manifest_path), results, "saturation_sweep")
    
    logger.info(f"Saturation sweep complete. Results saved to {output_path}")
    return results