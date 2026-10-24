"""
code/preprocess/calibrate.py
----------------------------
Implements the masking and calibration logic for EDS maps.
Detects dead pixels and outliers (artifacts) to ensure spatial
metrics are computed on valid data.
"""
import numpy as np
import logging
from typing import Tuple, Dict
from pathlib import Path

log = logging.getLogger(__name__)

def calibrate_and_log(
    image: np.ndarray, 
    dead_threshold: float = 0.0, 
    artifact_sigma: float = 3.0, 
    log_path: Path = None
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Masks defective pixels (dead pixels and outliers) in an EDS map.

    Parameters
    ----------
    image: np.ndarray
        2-D elemental map.
    dead_threshold: float
        Values at or below this threshold are considered dead pixels.
    artifact_sigma: float
        Values more than this many standard deviations from the mean 
        are considered artifacts.
    log_path: Path, optional
        Path to write a detailed log of masked pixels.

    Returns
    -------
    Tuple[np.ndarray, Dict[str, float]]
        A tuple containing the masked image (with NaNs) and a dictionary 
        of masking statistics.
    """
    # 1. Detect dead pixels (values <= threshold or NaN)
    dead_mask = (image <= dead_threshold) | np.isnan(image)
    
    # 2. Detect artifacts (outliers)
    # Use nanmean/nanstd to ignore existing NaNs
    mean_val = np.nanmean(image)
    std_val = np.nanstd(image)
    
    if std_val == 0:
        artifact_mask = np.zeros_like(dead_mask, dtype=bool)
    else:
        artifact_mask = np.abs(image - mean_val) > (artifact_sigma * std_val)
    
    # Combine masks
    full_mask = dead_mask | artifact_mask
    
    # Apply mask: replace defective pixels with NaN
    masked_image = image.copy().astype(float)
    masked_image[full_mask] = np.nan
    
    # Calculate statistics
    total_pixels = image.size
    dead_fraction = np.sum(dead_mask) / total_pixels
    artifact_fraction = np.sum(artifact_mask & ~dead_mask) / total_pixels
    
    stats = {
        "dead_pixel_fraction": float(dead_fraction),
        "artifact_fraction": float(artifact_fraction),
        "total_mask_fraction": float(np.sum(full_mask) / total_pixels)
    }
    
    if log_path:
        with open(log_path, "a") as f:
            f.write(f"Masking stats: {stats}\n")
            
    return masked_image, stats
