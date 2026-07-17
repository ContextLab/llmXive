import logging
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
from code.config import get_project_root, SATURATION_LEVELS, NOISE_LEVELS
from code.io.writer import save_fits_image, write_artifact_manifest
from code.metrics.ellipticity import calculate_ellipticity
from code.metrics.asymmetry import calculate_asymmetry
from code.io.loader import load_fits_image
import json
import csv

logger = logging.getLogger(__name__)

def inject_noise(image: np.ndarray, sigma: float) -> np.ndarray:
    """
    Inject Gaussian noise into an image.
    
    Args:
        image: Input image array
        sigma: Standard deviation of the Gaussian noise
    
    Returns:
        Noisy image array
    """
    if sigma <= 0:
        return image.copy()
    
    noise = np.random.normal(0, sigma, image.shape)
    return image + noise

def clip_saturation(image: np.ndarray, fraction: float) -> Tuple[np.ndarray, bool]:
    """
    Clip the brightest pixels to simulate saturation.
    
    Args:
        image: Input image array
        fraction: Fraction of brightest pixels to clip (0.0 to 1.0)
    
    Returns:
        Tuple of (clipped image, valid flag)
    """
    if fraction <= 0:
        return image.copy(), True
    
    if fraction >= 1.0:
        logger.warning(f"Saturation fraction {fraction} >= 1.0. Resulting in zero signal.")
        return np.zeros_like(image), False
    
    flat = image.flatten()
    threshold = np.percentile(flat, 100 * (1 - fraction))
    clipped = np.minimum(image, threshold)
    
    # Check if clipping results in zero total signal
    if np.sum(clipped) == 0:
        logger.warning("Clipping resulted in zero total signal.")
        return clipped, False
    
    return clipped, True

def run_saturation_sweep(base_image_path: str = None):
    """
    Run a saturation sweep across defined levels and save results.
    Produces data/processed/saturation_sweep.csv as required.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load base image if provided, otherwise generate a dummy for the sweep
    if base_image_path:
        base_path = Path(base_image_path)
        if not base_path.exists():
            logger.error(f"Base image not found: {base_path}")
            return
        base_image = load_fits_image(base_path)
    else:
        # Use a synthetic base from T006 if available
        synth_path = root / "data" / "synthetic" / "synth_000.fits"
        if synth_path.exists():
            base_image = load_fits_image(synth_path)
        else:
            logger.warning("No base image found. Skipping saturation sweep.")
            return

    results = []
    saturation_levels = [i * 0.05 for i in range(11)] # 0.00 to 0.50
    
    for level in saturation_levels:
        clipped_image, valid = clip_saturation(base_image, level)
        
        if not valid:
            logger.warning(f"Skipping metric calculation for saturation level {level} (invalid).")
            results.append({
                "saturation_fraction": level,
                "asymmetry_mean": np.nan,
                "asymmetry_std": np.nan,
                "valid": False
            })
            continue
        
        try:
            asymmetry = calculate_asymmetry(clipped_image)
            results.append({
                "saturation_fraction": level,
                "asymmetry_mean": asymmetry,
                "asymmetry_std": np.nan, # Single measurement
                "valid": True
            })
        except Exception as e:
            logger.error(f"Error calculating asymmetry for level {level}: {e}")
            results.append({
                "saturation_fraction": level,
                "asymmetry_mean": np.nan,
                "asymmetry_std": np.nan,
                "valid": False
            })
    
    # Write to CSV
    csv_path = processed_dir / "saturation_sweep.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["saturation_fraction", "asymmetry_mean", "asymmetry_std", "valid"])
        writer.writeheader()
        writer.writerows(results)
    
    logger.info(f"Saturation sweep results written to {csv_path}")
    return results
