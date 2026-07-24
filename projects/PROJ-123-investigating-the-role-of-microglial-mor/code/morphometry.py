"""
Morphometry Module.
Implements image processing for microglial morphology.
"""
import numpy as np
from skimage.morphology import skeletonize, medial_axis
from skimage.measure import label, find_contours, regionprops
from skimage.filters import gaussian, threshold_otsu
from skimage.exposure import rescale_intensity
from scipy.ndimage import convolve, distance_transform_edt, binary_erosion
import logging
from typing import List, Dict, Any, Tuple, Optional

from code.logging_utils import get_logger
from code.config import get_morphometry_config

logger = get_logger(__name__)


def handle_empty_fields(image: np.ndarray) -> bool:
    """
    Check if the image is empty or invalid.
    Returns True if empty.
    """
    if image is None or image.size == 0:
        logger.warning("Empty field of view detected.")
        return True
    if np.all(image == 0):
        logger.warning("Field of view contains only zeros.")
        return True
    return False


def denoise_and_subtract(image: np.ndarray) -> np.ndarray:
    """
    Denoise and subtract background.
    """
    # Gaussian denoising
    denoised = gaussian(image, sigma=1)
    # Background subtraction (simple morphological opening)
    # For simplicity, we use a threshold
    thresh = threshold_otsu(denoised)
    binary = denoised > thresh
    return binary.astype(np.uint8)


def skeletonize_and_count(image: np.ndarray) -> int:
    """
    Skeletonize the image and count branch points.
    """
    if handle_empty_fields(image):
        return 0
    
    skel = skeletonize(image)
    # Count branch points: pixels with > 2 neighbors in skeleton
    kernel = np.ones((3,3), dtype=int)
    kernel[1,1] = 0
    neighbors = convolve(skel.astype(int), kernel)
    branch_points = np.sum((skel == 1) & (neighbors > 2))
    return int(branch_points)


def calculate_soma_area_and_length(image: np.ndarray) -> Tuple[float, float]:
    """
    Calculate soma area and total process length.
    """
    if handle_empty_fields(image):
        return 0.0, 0.0
    
    # Soma area: area of largest connected component (assuming soma is largest)
    labeled = label(image)
    props = regionprops(labeled)
    if not props:
        return 0.0, 0.0
    
    # Assume largest is soma
    soma = max(props, key=lambda x: x.area)
    soma_area = float(soma.area)
    
    # Total length: length of skeleton
    # Approximation: count non-zero pixels in skeleton * pixel_size
    skel = skeletonize(image)
    total_length = float(np.sum(skel)) # assuming pixel size 1
    
    return soma_area, total_length


def run_sholl_analysis(image: np.ndarray, radii: Optional[List[float]] = None) -> List[int]:
    """
    Run Sholl analysis with configurable radius steps.
    
    Reads default radii from config if not provided.
    Returns a list of intersection counts corresponding to the provided radii.
    
    Args:
        image: Binary or grayscale image of the microglial cell.
        radii: List of radii (in pixels) to sample. If None, uses config defaults.
    
    Returns:
        List of intersection counts for each radius.
    """
    if handle_empty_fields(image):
        if radii is None:
            # Return empty list if no radii provided and image empty
            return []
        return [0] * len(radii)
    
    # Load config for default radii if not provided
    if radii is None:
        config = get_morphometry_config()
        # Default steps: 2, 5, 10 microns (assuming 1px = 1um for simplicity in synthetic, 
        # but in real data this would be scaled by pixel_size)
        # Config might define 'start', 'stop', 'step' or explicit list
        default_radii = config.get('sholl_radii', [5, 10, 15, 20, 25])
        if isinstance(default_radii, dict):
            start = default_radii.get('start', 0)
            stop = default_radii.get('stop', 30)
            step = default_radii.get('step', 5)
            radii = list(range(int(start), int(stop) + 1, int(step)))
        else:
            radii = list(default_radii)
    
    # Find center (centroid of largest component)
    labeled = label(image)
    props = regionprops(labeled)
    if not props:
        return [0] * len(radii)
    
    # Use the centroid of the largest component as the center
    # Note: regionprops returns (row, col), so centroid is (y, x)
    soma = max(props, key=lambda x: x.area)
    y, x = soma.centroid
    
    counts = []
    
    # Pre-calculate skeleton to avoid recomputing
    skel = skeletonize(image)
    
    # Calculate distance transform once
    # distance_transform_edt on the inverted image gives distance from background
    # We want distance from the center, so we compute Euclidean distance map from center
    y_coords, x_coords = np.ogrid[:image.shape[0], :image.shape[1]]
    dist_from_center = np.sqrt((y_coords - y)**2 + (x_coords - x)**2)
    
    for r in radii:
        # Define a tolerance band for the ring (r - 0.5, r + 0.5)
        # This captures pixels whose distance is approximately r
        lower_bound = r - 0.5
        upper_bound = r + 0.5
        
        mask = (dist_from_center >= lower_bound) & (dist_from_center <= upper_bound)
        
        # Count skeleton pixels within this ring
        intersection_count = int(np.sum(skel & mask))
        counts.append(intersection_count)
    
    return counts


def process_microglia_image(image: np.ndarray) -> Dict[str, Any]:
    """
    Full processing pipeline for a single image.
    """
    branch_points = skeletonize_and_count(image)
    soma_area, total_length = calculate_soma_area_and_length(image)
    sholl = run_sholl_analysis(image)
    
    return {
        'branch_points': branch_points,
        'total_length': total_length,
        'soma_area': soma_area,
        'sholl_intersections': sholl
    }