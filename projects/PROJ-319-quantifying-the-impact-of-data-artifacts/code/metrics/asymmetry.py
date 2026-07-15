"""Asymmetry calculation metrics for planetary nebulae.

This module implements the calculation of the asymmetry index (A-statistic)
as defined by Conselice (2003).
"""
import logging
from typing import Tuple, Optional

import numpy as np

logger = logging.getLogger(__name__)

def calculate_asymmetry(
    image: np.ndarray,
    center: Optional[Tuple[int, int]] = None,
    background_image: Optional[np.ndarray] = None
) -> Tuple[float, float]:
    """Calculate the asymmetry index (A-statistic) for an image.

    The asymmetry is defined as:
    A = sum |I_0 - I_180| / sum |I_0|

    Where I_0 is the original image and I_180 is the image rotated by 180 degrees.
    The center of rotation is the centroid of the image or a provided center.
    Background correction is optional and subtracts the asymmetry of a background
    region if provided.

    Args:
        image: 2D array representing the image.
        center: Optional tuple (x, y) for the center of rotation.
                If None, the centroid of the image is used.
        background_image: Optional 2D array of the same shape representing
                          the background region to correct for noise bias.
                          If None, no background correction is applied.

    Returns:
        Tuple (asymmetry, background_correction).
        background_correction is the asymmetry of the background (0.0 if not provided).
    """
    if image.ndim != 2:
        raise ValueError("Image must be a 2D array.")

    if image.size == 0:
        logger.warning("Image is empty, returning zero asymmetry.")
        return 0.0, 0.0

    # Determine center of rotation
    if center is None:
        # Calculate centroid (weighted mean of coordinates)
        y, x = np.indices(image.shape)
        total_flux = np.sum(image)
        if total_flux == 0:
            logger.warning("Image has zero flux, returning zero asymmetry.")
            return 0.0, 0.0
        x_bar = np.sum(x * image) / total_flux
        y_bar = np.sum(y * image) / total_flux
        center = (int(round(x_bar)), int(round(y_bar)))

    # Robust centering: Shift image so the center is at the array center
    # to ensure rotation works correctly relative to the object centroid.
    # We use interpolation to shift the image.
    rows, cols = image.shape
    cy, cx = rows / 2.0 - 0.5, cols / 2.0 - 0.5
    # Target center is the calculated centroid
    target_y, target_x = center

    # Calculate shift required to move centroid to array center
    shift_y = cy - target_y
    shift_x = cx - target_x

    # Create grid for interpolation
    # We want to sample the original image at coordinates that are shifted
    # relative to the output grid.
    # Output grid (y, x) maps to Input grid (y + shift_y, x + shift_x)
    y_grid, x_grid = np.indices(image.shape)
    src_y = y_grid + shift_y
    src_x = x_grid + shift_x

    # Use scipy.ndimage.map_coordinates for robust interpolation
    try:
        from scipy.ndimage import map_coordinates
    except ImportError:
        raise ImportError("scipy is required for robust centering interpolation.")

    # Interpolate with linear order (1)
    # Order 0 (nearest) is faster but less precise for centroid alignment
    # Order 1 (linear) is a good balance
    image_shifted = map_coordinates(image, [src_y, src_x], order=1, mode='nearest')

    # Rotate 180 degrees around the array center
    # Rotating 180 degrees is equivalent to flipping both axes
    image_rotated = np.rot90(image_shifted, k=2)

    # Calculate asymmetry
    numerator = np.sum(np.abs(image_shifted - image_rotated))
    denominator = np.sum(np.abs(image_shifted))

    if denominator == 0:
        logger.warning("Shifted image sum is zero, returning zero asymmetry.")
        return 0.0, 0.0

    A = numerator / denominator

    # Background correction
    bg_correction = 0.0
    if background_image is not None:
        if background_image.shape != image.shape:
            raise ValueError("Background image must have the same shape as the input image.")
        
        # Calculate asymmetry for background
        # We assume the background is centered similarly or just use the same center
        # For background, we might not need to re-center if it's uniform, but for consistency:
        bg_y, bg_x = np.indices(background_image.shape)
        bg_total = np.sum(background_image)
        if bg_total > 0:
            bg_cx = np.sum(bg_x * background_image) / bg_total
            bg_cy = np.sum(bg_y * background_image) / bg_total
            bg_center = (int(round(bg_cx)), int(round(bg_cy)))
            
            # Shift background to center
            bg_shifted = map_coordinates(background_image, [bg_x + shift_y, bg_y + shift_x], order=1, mode='nearest')
            bg_rotated = np.rot90(bg_shifted, k=2)
            
            bg_num = np.sum(np.abs(bg_shifted - bg_rotated))
            bg_den = np.sum(np.abs(bg_shifted))
            
            if bg_den > 0:
                bg_correction = bg_num / bg_den

    return A, bg_correction
