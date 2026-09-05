"""
Topological Metrics Calculation Module.

Implements utility functions to calculate shape_factor and connectivity
for microstructure images using scikit-image morphology tools.

Purpose:
  - Record metrics for Data Hygiene (Constitution Principle III)
  - Support Generalization Boundary Disclosure (Principle VII)
  - DO NOT use these metrics for stratification (stratification is strictly
    by inclusion_density and topology_type per FR-005)

Calculations:
  - shape_factor: perimeter^2 / (4 * pi * area)
    (1.0 for a perfect circle, >1.0 for complex shapes)
  - connectivity: Euler number (number of objects - number of holes)
    calculated via skimage.measure.euler_number
"""

import numpy as np
from skimage import measure, morphology
from typing import Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


def calculate_shape_factor(binary_mask: np.ndarray) -> float:
    """
    Calculate the shape factor for a binary mask.

    Formula: perimeter^2 / (4 * pi * area)
    - Returns 1.0 for a perfect circle
    - Returns >1.0 for irregular shapes
    - Returns np.nan if area is zero

    Args:
        binary_mask: 2D boolean or integer array where True/Non-zero represents
                     the inclusion/void phase.

    Returns:
        float: The calculated shape factor, or np.nan if invalid.
    """
    if binary_mask.size == 0:
        logger.warning("Empty mask provided to calculate_shape_factor")
        return np.nan

    # Ensure boolean
    mask = binary_mask.astype(bool)

    # Calculate perimeter using measure.perimeter (pixel-based)
    # measure.perimeter counts the boundary pixels
    perimeter = measure.perimeter(mask)

    # Calculate area (number of foreground pixels)
    area = np.sum(mask)

    if area == 0:
        logger.warning("Zero area detected in mask for shape factor calculation")
        return np.nan

    # Shape factor formula
    # Using 4 * pi * area as the denominator
    shape_factor = (perimeter ** 2) / (4.0 * np.pi * area)

    return float(shape_factor)


def calculate_connectivity(binary_mask: np.ndarray) -> int:
    """
    Calculate the connectivity (Euler number) for a binary mask.

    The Euler number is defined as: (Number of Objects) - (Number of Holes)
    - Positive values indicate more objects than holes
    - Negative values indicate more holes than objects
    - Zero indicates equal numbers

    Args:
        binary_mask: 2D boolean or integer array where True/Non-zero represents
                     the inclusion/void phase.

    Returns:
        int: The Euler number (connectivity).
    """
    if binary_mask.size == 0:
        logger.warning("Empty mask provided to calculate_connectivity")
        return 0

    # Ensure boolean
    mask = binary_mask.astype(bool)

    # Calculate Euler number using skimage.measure.euler_number
    # connectivity=1 is standard for 2D (4-connectivity for background, 8 for foreground)
    euler_number = measure.euler_number(mask, connectivity=1)

    return int(euler_number)


def compute_topological_metrics(image_path: str) -> Dict[str, Any]:
    """
    Compute topological metrics (shape_factor and connectivity) for a given image.

    This function loads a binary or grayscale microstructure image, binarizes it
    (if grayscale, using Otsu thresholding or simple >0), and calculates the
    required metrics.

    Args:
        image_path: Path to the image file (PNG, etc.).

    Returns:
        dict: A dictionary containing:
              - 'shape_factor': float
              - 'connectivity': int
              - 'area_fraction': float (optional, for logging)
    """
    from skimage import io
    import numpy as np

    try:
        # Load image
        img = io.imread(image_path)

        # Convert to grayscale if necessary
        if img.ndim == 3:
            # Convert RGB to grayscale
            img = np.dot(img[..., :3], [0.2989, 0.5870, 0.1140])

        # Binarize: Assume non-zero is foreground.
        # If the image is already binary (0 and 1 or 0 and 255), this works.
        # For more robust binarization, one could use Otsu from skimage.filters
        # but the task implies a direct calculation on the provided mask.
        # We assume the input image represents the microstructure phase directly.
        # If values are 0 and 255, normalize to 0/1 or just cast to bool.
        binary_mask = img > 0.5 if img.max() <= 1.0 else img > 127.5

        # Calculate metrics
        shape_factor = calculate_shape_factor(binary_mask)
        connectivity = calculate_connectivity(binary_mask)
        area_fraction = float(np.sum(binary_mask) / binary_mask.size)

        return {
            "shape_factor": shape_factor,
            "connectivity": connectivity,
            "area_fraction": area_fraction
        }

    except Exception as e:
        logger.error(f"Failed to compute topological metrics for {image_path}: {e}")
        raise


def calculate_topological_metrics_from_array(
    binary_array: np.ndarray
) -> Dict[str, float]:
    """
    Calculate topological metrics directly from a numpy array.

    Args:
        binary_array: 2D numpy array (boolean or 0/1/255) representing the mask.

    Returns:
        dict: Dictionary with 'shape_factor' and 'connectivity'.
    """
    shape_factor = calculate_shape_factor(binary_array)
    connectivity = calculate_connectivity(binary_array)

    return {
        "shape_factor": shape_factor,
        "connectivity": float(connectivity)
    }
