import numpy as np
from skimage.morphology import skeletonize
from skimage.measure import label
from typing import Tuple, Dict, Any
import logging

from code.config import get_path
from code.logging_utils import get_logger

logger = get_logger(__name__)

def _is_binary_image(arr: np.ndarray) -> bool:
    """Check if the image is binary (0 and 1 or 0 and 255)."""
    unique_vals = np.unique(arr)
    return len(unique_vals) <= 2 and np.all(np.isin(unique_vals, [0, 1, 255]))

def skeletonize_and_count(preprocessed_image: np.ndarray) -> Dict[str, Any]:
    """
    Perform skeletonization on the denoised and background-subtracted image
    and count the number of branch points.

    This function consumes the output of `denoise_and_subtract()` (T013).
    It implements FR-003: Skeletonization and branch point counting.

    Parameters
    ----------
    preprocessed_image : np.ndarray
        A 2D binary or grayscale image where microglial processes are segmented.
        If grayscale, it is thresholded internally. If binary (0/1 or 0/255),
        it is used directly.

    Returns
    -------
    Dict[str, Any]
        A dictionary containing:
            - 'skeleton': np.ndarray (boolean), the 8-connected skeleton.
            - 'branch_points': int, the count of branch points.
            - 'success': bool, whether the operation was successful.
            - 'error': str, error message if failed.
    """
    if preprocessed_image.ndim != 2:
        raise ValueError(f"Expected 2D image, got {preprocessed_image.ndim}D")

    # Ensure binary
    if not _is_binary_image(preprocessed_image):
        # Threshold: if not binary, assume grayscale and threshold at 0.5 or max/2
        # Assuming normalized [0, 1] or [0, 255].
        if preprocessed_image.max() <= 1.0:
            threshold = 0.5
        else:
            threshold = preprocessed_image.max() / 2.0
        binary_img = preprocessed_image > threshold
        logger.debug(f"Thresholded grayscale image at {threshold}")
    else:
        binary_img = preprocessed_image.astype(bool)
        if preprocessed_image.max() == 255:
            binary_img = preprocessed_image > 127

    # Skeletonize
    # skimage.morphology.skeletonize expects boolean input
    try:
        skeleton = skeletonize(binary_img)
    except Exception as e:
        logger.error(f"Skeletonization failed: {e}")
        return {
            'skeleton': np.zeros_like(binary_img),
            'branch_points': 0,
            'success': False,
            'error': str(e)
        }

    if not np.any(skeleton):
        logger.warning("Skeleton is empty. No processes detected.")
        return {
            'skeleton': skeleton,
            'branch_points': 0,
            'success': True,
            'error': None
        }

    # Count branch points
    # A branch point in a skeleton is a pixel with 3 or more neighbors in the skeleton.
    # We use convolution with a 3x3 kernel of ones to count neighbors.
    from scipy.ndimage import convolve

    # Kernel to count neighbors (excluding center)
    kernel = np.ones((3, 3), dtype=int)
    kernel[1, 1] = 0

    # Count neighbors for each pixel in the skeleton
    neighbor_count = convolve(skeleton.astype(int), kernel, mode='constant', cval=0)

    # Branch points are skeleton pixels with >= 3 neighbors
    branch_points_mask = (skeleton & (neighbor_count >= 3))
    branch_point_count = int(np.sum(branch_points_mask))

    logger.debug(f"Detected {branch_point_count} branch points.")

    return {
        'skeleton': skeleton,
        'branch_points': branch_point_count,
        'success': True,
        'error': None
    }
