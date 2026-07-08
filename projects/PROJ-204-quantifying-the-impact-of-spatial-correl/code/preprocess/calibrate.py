import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Union, Any
from pathlib import Path
from scipy import ndimage
import json

__all__ = [
    "detect_dead_pixels",
    "detect_artifacts",
    "mask_defective_regions",
    "calibrate_and_log",
    "apply_mask_to_dataset",
]

def detect_dead_pixels(image: np.ndarray, threshold: float = 0.0) -> np.ndarray:
    """
    Detect dead pixels (intensity <= threshold) in an image.

    Parameters
    ----------
    image: np.ndarray
        Input image.
    threshold: float, optional
        Intensity threshold (default 0.0).

    Returns
    -------
    np.ndarray
        Boolean mask where ``True`` indicates a dead pixel.
    """
    return image <= threshold

def detect_artifacts(image: np.ndarray, sigma: float = 3.0) -> np.ndarray:
    """
    Detect bright artifacts using a sigma‑clipped threshold.

    Parameters
    ----------
    image: np.ndarray
        Input image.
    sigma: float, optional
        Number of standard deviations above the mean to flag as artifact.

    Returns
    -------
    np.ndarray
        Boolean mask where ``True`` indicates an artifact pixel.
    """
    mean = np.mean(image)
    std = np.std(image)
    return image > (mean + sigma * std)

def mask_defective_regions(
    image: np.ndarray,
    dead_mask: np.ndarray,
    artifact_mask: np.ndarray,
) -> np.ndarray:
    """
    Combine dead pixel and artifact masks and apply to the image.

    Parameters
    ----------
    image: np.ndarray
        Original image.
    dead_mask: np.ndarray
        Boolean mask of dead pixels.
    artifact_mask: np.ndarray
        Boolean mask of artifacts.

    Returns
    -------
    np.ndarray
        Masked image where defective regions are set to zero.
    """
    combined = dead_mask | artifact_mask
    masked = np.where(combined, 0, image)
    return masked

def calibrate_and_log(
    image: np.ndarray,
    dead_threshold: float = 0.0,
    artifact_sigma: float = 3.0,
    log_path: Optional[Path] = None,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Detect defects, mask them, and optionally log statistics.

    Parameters
    ----------
    image: np.ndarray
        Input image.
    dead_threshold: float, optional
        Threshold for dead pixel detection.
    artifact_sigma: float, optional
        Sigma level for artifact detection.
    log_path: Path, optional
        Path to a JSON file where defect statistics will be saved.

    Returns
    -------
    Tuple[np.ndarray, Dict[str, Any]]
        (masked_image, statistics_dict)
    """
    dead = detect_dead_pixels(image, dead_threshold)
    artifact = detect_artifacts(image, artifact_sigma)
    masked = mask_defective_regions(image, dead, artifact)

    stats = {
        "dead_pixel_fraction": dead.mean(),
        "artifact_fraction": artifact.mean(),
    }

    if log_path:
        with open(log_path, "w") as f:
            json.dump(stats, f, indent=2)
        logging.info("Defect statistics written to %s", log_path)

    return masked, stats

def apply_mask_to_dataset(
    dataset: Dict[str, np.ndarray],
    mask: np.ndarray,
) -> Dict[str, np.ndarray]:
    """
    Apply a common mask to all images in a dataset.

    Parameters
    ----------
    dataset: Dict[str, np.ndarray]
        Mapping from element name to image array.
    mask: np.ndarray
        Boolean mask where ``True`` indicates a valid pixel.

    Returns
    -------
    Dict[str, np.ndarray]
        New dataset with masked images.
    """
    return {k: np.where(mask, v, 0) for k, v in dataset.items()}
