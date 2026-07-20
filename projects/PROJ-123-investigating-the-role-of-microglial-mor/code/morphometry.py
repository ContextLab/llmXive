import numpy as np
from skimage.morphology import skeletonize, medial_axis
from skimage.measure import label, find_contours, regionprops
from skimage.filters import gaussian, threshold_otsu
from skimage.exposure import rescale_intensity
from scipy.ndimage import convolve, distance_transform_edt, binary_erosion
import logging
from typing import Dict, Any, Tuple, Optional

# Initialize logger for this module
logger = logging.getLogger(__name__)

def handle_empty_fields(image: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if the provided image represents an empty field of view.
    
    An empty field of view is defined as an image where:
    1. The image is all zeros (no signal).
    2. The image contains only background noise below a negligible threshold 
       (e.g., mean intensity < 1.0 after potential scaling).
    
    Args:
        image: 2D or 3D numpy array representing the microscopy image.
        metadata: Optional dictionary containing image metadata (e.g., acquisition 
                parameters) that might help determine validity.
    
    Returns:
        bool: True if the field is empty and should be skipped, False otherwise.
    
    Side Effects:
        Logs a WARNING if an empty field is detected, including the image shape 
        and mean intensity.
    """
    if image is None:
        logger.warning("Empty field detected: image is None.")
        return True
    
    if image.size == 0:
        logger.warning("Empty field detected: image has zero size.")
        return True
    
    # Check for all zeros
    if np.all(image == 0):
        logger.warning(
            "Skipping empty field of view (all zeros). "
            f"Image shape: {image.shape}, Mean intensity: 0.0"
        )
        return True
    
    # Check for negligible signal (noise floor)
    # Using a very low threshold to catch images that are effectively empty
    # but might have minor sensor noise.
    mean_intensity = np.mean(image)
    if mean_intensity < 1e-6:
        logger.warning(
            f"Skipping empty field of view (negligible signal). "
            f"Image shape: {image.shape}, Mean intensity: {mean_intensity:.2e}"
        )
        return True
    
    return False

def denoise_and_subtract(image: np.ndarray) -> np.ndarray:
    """
    Apply Gaussian denoising and background subtraction.
    
    Args:
        image: 2D or 3D numpy array.
    
    Returns:
        Processed image with background removed.
    """
    if handle_empty_fields(image):
        return np.zeros_like(image)
    
    # Gaussian denoising
    denoised = gaussian(image, sigma=1.0)
    
    # Background subtraction using morphological opening or rolling ball approximation
    # Using a large kernel for background estimation
    kernel_size = max(15, image.shape[0] // 10)
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    # Create a structuring element for morphological opening
    from skimage.morphology import disk, ball
    if image.ndim == 2:
        selem = disk(kernel_size // 2)
    else:
        selem = ball(kernel_size // 2)
    
    # Estimate background
    background = opening(denoised, selem)
    
    # Subtract background
    result = denoised - background
    result = np.clip(result, 0, None)
    
    return result

def skeletonize_and_count(image: np.ndarray) -> Tuple[int, np.ndarray]:
    """
    Skeletonize the image and count branch points.
    
    Args:
        image: Preprocessed 2D image.
    
    Returns:
        Tuple of (branch_point_count, skeleton_image).
    """
    if handle_empty_fields(image):
        return 0, np.zeros_like(image, dtype=bool)
    
    # Threshold the image
    thresh = threshold_otsu(image)
    binary = image > thresh
    
    # Skeletonize
    skeleton = skeletonize(binary)
    
    # Count branch points: pixels in skeleton with > 2 neighbors
    # Use convolution with a 3x3 kernel to count neighbors
    kernel = np.ones((3, 3), dtype=int)
    kernel[1, 1] = 0
    neighbors = convolve(skeleton.astype(int), kernel, mode='constant')
    branch_points = (skeleton & (neighbors > 2))
    count = np.sum(branch_points)
    
    return int(count), skeleton

def calculate_soma_area_and_length(image: np.ndarray, skeleton: np.ndarray) -> Tuple[float, float]:
    """
    Calculate soma area and total process length.
    
    Args:
        image: Preprocessed 2D image.
        skeleton: Skeletonized image from skeletonize_and_count.
    
    Returns:
        Tuple of (soma_area, total_length).
    """
    if handle_empty_fields(image):
        return 0.0, 0.0
    
    # Threshold for soma detection (usually the brightest region)
    thresh = threshold_otsu(image)
    binary = image > thresh
    
    # Label connected components
    labeled_image = label(binary)
    props = regionprops(labeled_image)
    
    if not props:
        return 0.0, 0.0
    
    # Assume the largest component is the soma
    soma_props = max(props, key=lambda p: p.area)
    soma_area = soma_props.area
    
    # Total length from skeleton (number of pixels)
    total_length = np.sum(skeleton)
    
    return float(soma_area), float(total_length)

def run_sholl_analysis(image: np.ndarray, skeleton: np.ndarray, 
                      step_size: float = 5.0, max_radius: Optional[float] = None) -> Dict[str, Any]:
    """
    Perform Sholl analysis on the skeletonized image.
    
    Args:
        image: Preprocessed 2D image.
        skeleton: Skeletonized image.
        step_size: Radius step size for Sholl circles.
        max_radius: Maximum radius to consider. If None, uses half the image diagonal.
    
    Returns:
        Dictionary containing Sholl intersections data.
    """
    if handle_empty_fields(image):
        return {"intersections": [], "radii": []}
    
    # Find centroid of the skeleton (approximate soma center)
    coords = np.column_stack(np.where(skeleton))
    if len(coords) == 0:
        return {"intersections": [], "radii": []}
    
    center = np.mean(coords, axis=0)
    
    if max_radius is None:
        h, w = image.shape
        max_radius = np.sqrt((h/2)**2 + (w/2)**2)
    
    radii = np.arange(0, max_radius, step_size)
    intersections = []
    
    for r in radii:
        # Create a circle mask
        y, x = np.ogrid[:image.shape[0], :image.shape[1]]
        dist_from_center = np.sqrt((x - center[1])**2 + (y - center[0])**2)
        circle_mask = (dist_from_center <= r) & (dist_from_center > r - step_size)
        
        # Count intersections (pixels in skeleton within the annulus)
        intersection_count = np.sum(skeleton & circle_mask)
        intersections.append(int(intersection_count))
    
    return {"intersections": intersections, "radii": radii.tolist()}

def process_microglia_image(image: np.ndarray, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Full pipeline to process a single microglia image.
    
    Args:
        image: Raw image array.
        metadata: Dictionary with image metadata.
    
    Returns:
        Dictionary with extracted metrics or None if image is empty.
    """
    # Check for empty field
    if handle_empty_fields(image, metadata):
        return None
    
    # Denoise and subtract background
    processed = denoise_and_subtract(image)
    
    # Skeletonize and count branch points
    branch_points, skeleton = skeletonize_and_count(processed)
    
    # Calculate soma area and length
    soma_area, total_length = calculate_soma_area_and_length(processed, skeleton)
    
    # Run Sholl analysis
    sholl_data = run_sholl_analysis(processed, skeleton)
    
    # Aggregate Sholl intersections (e.g., total or max)
    # For simplicity, using the sum of intersections as the metric
    sholl_intersections = sum(sholl_data["intersections"])
    
    return {
        "branch_points": branch_points,
        "total_length": total_length,
        "soma_area": soma_area,
        "sholl_intersections": sholl_intersections,
        "metadata": metadata
    }

# Import opening from skimage if not already available
from skimage.morphology import opening