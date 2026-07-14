"""Artifact injection logic for synthetic planetary nebulae.

This module provides functions to inject noise and saturation artifacts
into synthetic images to simulate instrumental effects.
"""
import logging
from typing import Tuple

import numpy as np

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
