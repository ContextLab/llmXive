import numpy as np
from skimage.morphology import skeletonize, medial_axis
from skimage.measure import label, find_contours
from skimage.filters import gaussian
from scipy.ndimage import convolve, distance_transform_edt
from typing import Tuple, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def handle_empty_fields(image: np.ndarray, image_id: str = "unknown") -> bool:
    """
    Check if the input image represents an empty field of view (FOV).
    
    An empty FOV is defined as an image where the total non-zero pixel count
    (foreground) is below a negligible threshold relative to the image size,
    or if the image is entirely uniform (zero variance).
    
    This function implements the edge case logic required to skip processing
    of such images to prevent downstream errors in skeletonization and metric
    extraction.
    
    Args:
        image: 2D or 3D numpy array representing the microscopy image.
        image_id: Identifier for the image for logging purposes.
        
    Returns:
        bool: True if the field of view is considered empty and should be skipped.
              False if the image contains valid signal and should be processed.
              
    Side Effects:
        Logs a warning message if the field of view is empty.
    """
    if image is None:
        logger.warning(f"Empty field of view detected for {image_id}: Image is None.")
        return True
        
    if image.size == 0:
        logger.warning(f"Empty field of view detected for {image_id}: Image size is 0.")
        return True

    # Check for all-zero or near-all-zero images
    # Using a small epsilon to account for potential background noise
    # Threshold: if less than 0.1% of pixels are non-zero, consider it empty
    non_zero_count = np.count_nonzero(image)
    total_pixels = image.size
    fill_ratio = non_zero_count / total_pixels if total_pixels > 0 else 0.0
    
    # Threshold for "empty" - if less than 0.1% of pixels are active
    EMPTY_THRESHOLD = 0.001 
    
    if fill_ratio < EMPTY_THRESHOLD:
        logger.warning(
            f"Empty field of view detected for {image_id}. "
            f"Non-zero pixel ratio: {fill_ratio:.4f} (threshold: {EMPTY_THRESHOLD}). "
            "Skipping processing."
        )
        return True

    # Check for uniform images (zero variance) which indicate no signal variation
    # This catches cases where the image might be a solid block of background
    if np.std(image) == 0:
        logger.warning(
            f"Empty field of view detected for {image_id}. "
            f"Image has zero variance (uniform intensity). Skipping processing."
        )
        return True

    return False

def denoise_and_subtract(image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """
    Apply Gaussian denoising and background subtraction.
    """
    if handle_empty_fields(image):
        return image
        
    # Gaussian denoising
    denoised = gaussian(image, sigma=sigma)
    
    # Background subtraction using a morphological opening approximation
    # or simple rolling ball logic if needed, but for now using high-pass filter
    # logic via convolution or simple subtraction of a blurred version
    background = gaussian(image, sigma=sigma * 5)
    subtracted = denoised - background
    
    # Ensure no negative values if image is meant to be intensity
    return np.maximum(subtracted, 0)

def skeletonize_and_count(image: np.ndarray) -> Tuple[int, np.ndarray]:
    """
    Skeletonize the image and count branch points.
    """
    if handle_empty_fields(image):
        return 0, np.zeros_like(image, dtype=bool)
        
    # Binarize
    binary = image > 0
    if not np.any(binary):
        return 0, np.zeros_like(image, dtype=bool)
        
    skeleton = skeletonize(binary)
    
    # Count branch points (pixels with > 2 neighbors in the skeleton)
    # Convolve with 3x3 kernel to count neighbors
    kernel = np.ones((3, 3), dtype=int)
    kernel[1, 1] = 0
    neighbors = convolve(skeleton.astype(int), kernel, mode='constant')
    branch_points = (skeleton.astype(int) * (neighbors > 2)).sum()
    
    return int(branch_points), skeleton

def calculate_soma_area_and_length(image: np.ndarray) -> Tuple[float, float]:
    """
    Calculate soma area and total process length.
    """
    if handle_empty_fields(image):
        return 0.0, 0.0
        
    binary = image > 0
    if not np.any(binary):
        return 0.0, 0.0
        
    # Soma area: count of foreground pixels (assuming 1px = 1 unit area)
    # In real scenarios, this would be scaled by pixel size
    soma_area = float(np.count_nonzero(binary))
    
    # Total length: skeleton length
    # Using medial axis or skeletonize
    skeleton = skeletonize(binary)
    total_length = float(np.count_nonzero(skeleton))
    
    return soma_area, total_length

def run_sholl_analysis(image: np.ndarray, center: Optional[Tuple[int, int]] = None, 
                       step_size: float = 5.0, max_radius: Optional[float] = None) -> Dict[str, Any]:
    """
    Perform Sholl analysis on the microglia image.
    """
    if handle_empty_fields(image):
        return {"intersections": [], "radii": [], "max_intersections": 0}
        
    binary = image > 0
    if not np.any(binary):
        return {"intersections": [], "radii": [], "max_intersections": 0}
        
    if center is None:
        # Estimate center as centroid of the foreground
        coords = np.column_stack(np.where(binary))
        center = tuple(np.mean(coords, axis=0).astype(int))
        
    y, x = center
    h, w = binary.shape
    
    if max_radius is None:
        max_radius = max(np.sqrt((h/2)**2 + (w/2)**2))
        
    radii = np.arange(0, max_radius, step_size)
    intersections = []
    
    for r in radii:
        # Create a circle mask
        Y, X = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((X - x)**2 + (Y - y)**2)
        circle_mask = (dist_from_center <= r) & (dist_from_center > (r - step_size))
        
        # Count intersections (simplified: count pixels in the annulus that are foreground)
        # A more rigorous Sholl counts crossings of the contour, but for pixel grid:
        # We count the number of foreground pixels in the ring
        ring_pixels = binary & circle_mask
        intersections.append(float(np.count_nonzero(ring_pixels)))
        
    return {
        "intersections": intersections,
        "radii": list(radii),
        "max_intersections": max(intersections) if intersections else 0
    }

def process_microglia_image(image: np.ndarray, image_id: str = "unknown") -> Dict[str, Any]:
    """
    Main pipeline function to process a single microglia image.
    Returns a dictionary of morphological metrics.
    """
    if handle_empty_fields(image, image_id):
        return {
            "image_id": image_id,
            "branch_points": 0,
            "total_length": 0.0,
            "soma_area": 0.0,
            "sholl_intersections": [],
            "skipped": True
        }
        
    # Denoise
    processed = denoise_and_subtract(image)
    
    # Skeletonize and count
    branch_points, skeleton = skeletonize_and_count(processed)
    
    # Soma and length
    soma_area, total_length = calculate_soma_area_and_length(processed)
    
    # Sholl
    sholl_results = run_sholl_analysis(processed)
    
    return {
        "image_id": image_id,
        "branch_points": branch_points,
        "total_length": total_length,
        "soma_area": soma_area,
        "sholl_intersections": sholl_results["intersections"],
        "skipped": False
    }