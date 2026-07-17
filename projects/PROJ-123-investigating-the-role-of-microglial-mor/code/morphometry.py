import numpy as np
from skimage.morphology import skeletonize
from skimage.measure import label
from typing import Tuple, Dict, Any, Optional
import logging
from scipy.ndimage import convolve
from code.config import get_path

logger = logging.getLogger(__name__)

def handle_empty_fields(image: np.ndarray, image_id: str) -> bool:
    """
    Check if the provided image represents an empty field of view (no signal).
    
    An empty field is defined as an image where the total sum of pixel values
    is below a threshold derived from the noise floor, or the image contains
    no non-zero pixels after basic thresholding.
    
    Args:
        image: The 2D or 3D image array.
        image_id: Identifier for the image (used in logging).
        
    Returns:
        True if the field is empty and should be skipped.
        False if the field contains valid signal and should be processed.
    """
    if image is None:
        logger.warning(f"Image {image_id} is None. Skipping.")
        return True

    if image.size == 0:
        logger.warning(f"Image {image_id} has zero size. Skipping.")
        return True

    # Check for all-zero images
    if np.all(image == 0):
        logger.warning(f"Image {image_id} contains only zero values (empty FOV). Skipping.")
        return True

    # Calculate a simple noise floor threshold using the mean + 3*std of the background
    # Assuming background is the majority of the image.
    # If the image is extremely sparse but has a few hot pixels, we might want to 
    # check the median or mode, but for now, a strict sum check is safer for "empty" FOVs.
    # A more robust check: if the number of non-zero pixels is below a tiny fraction
    # of the total area, it's likely noise.
    non_zero_count = np.count_nonzero(image)
    total_pixels = image.size
    
    # If less than 0.01% of pixels are non-zero, treat as empty/noise
    if non_zero_count < (total_pixels * 0.0001):
        logger.warning(f"Image {image_id} has negligible signal ({non_zero_count}/{total_pixels} pixels). Skipping as empty FOV.")
        return True

    return False

def skeletonize_and_count(image: np.ndarray) -> Tuple[int, np.ndarray]:
    """
    Skeletonize the image and count the number of branch points.
    
    Args:
        image: Pre-processed binary or grayscale image.
        
    Returns:
        Tuple of (branch_point_count, skeleton_image).
    """
    if handle_empty_fields(image, "unknown"):
        return 0, np.zeros_like(image, dtype=bool)
    
    # Ensure binary for skeletonize
    if image.dtype != bool:
        binary_image = image > 0
    else:
        binary_image = image
    
    skeleton = skeletonize(binary_image)
    
    # Count branch points: pixels in skeleton with > 2 neighbors
    # Define a 3x3 kernel to count neighbors
    kernel = np.array([
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1]
    ])
    
    # Count neighbors for each pixel in the skeleton
    neighbor_count = convolve(skeleton.astype(int), kernel, mode='constant')
    
    # Branch points are skeleton pixels with more than 2 neighbors
    branch_points = (skeleton.astype(bool)) & (neighbor_count > 2)
    count = int(np.sum(branch_points))
    
    return count, skeleton

def calculate_soma_area_and_length(image: np.ndarray) -> Tuple[float, float]:
    """
    Calculate the soma area (approximated as connected component area) 
    and total process length.
    
    Args:
        image: Pre-processed image.
        
    Returns:
        Tuple of (soma_area, total_length).
    """
    if handle_empty_fields(image, "unknown"):
        return 0.0, 0.0
    
    if image.dtype != bool:
        binary_image = image > 0
    else:
        binary_image = image
        
    # Label connected components to find the soma (largest component)
    labeled_image = label(binary_image)
    if labeled_image.max() == 0:
        return 0.0, 0.0
        
    # Assume the largest connected component is the soma + processes
    # For a more precise soma detection, we might need watershed or specific 
    # size filtering, but per task scope, we treat the main structure.
    # However, usually soma is the large blob. Let's assume the largest label is the cell.
    region_sizes = np.bincount(labeled_image.ravel())
    # Ignore background (0)
    if len(region_sizes) < 2:
        return 0.0, 0.0
        
    max_label = np.argmax(region_sizes[1:]) + 1
    soma_mask = labeled_image == max_label
    soma_area = float(np.sum(soma_mask))
    
    # Total length can be approximated by skeleton length
    skeleton = skeletonize(soma_mask)
    total_length = float(np.sum(skeleton))
    
    return soma_area, total_length

def run_sholl_analysis(image: np.ndarray, radius_steps: list) -> Dict[str, Any]:
    """
    Perform Sholl analysis on the image.
    
    Args:
        image: Pre-processed binary image.
        radius_steps: List of radii to sample.
        
    Returns:
        Dictionary with Sholl analysis results.
    """
    if handle_empty_fields(image, "unknown"):
        return {"radii": radius_steps, "intersections": [0] * len(radius_steps)}
    
    if image.dtype != bool:
        binary_image = image > 0
    else:
        binary_image = image
        
    # Find center (centroid of the largest component)
    labeled_image = label(binary_image)
    region_sizes = np.bincount(labeled_image.ravel())
    if len(region_sizes) < 2:
        return {"radii": radius_steps, "intersections": [0] * len(radius_steps)}
        
    max_label = np.argmax(region_sizes[1:]) + 1
    coords = np.argwhere(labeled_image == max_label)
    center = coords.mean(axis=0)
    
    intersections = []
    for r in radius_steps:
        # Create a circle mask
        y, x = np.ogrid[:binary_image.shape[0], :binary_image.shape[1]]
        dist_from_center = np.sqrt((x - center[1])**2 + (y - center[0])**2)
        shell_mask = (dist_from_center >= r - 0.5) & (dist_from_center < r + 0.5)
        
        # Count intersections: pixels in skeleton that are on the shell
        skeleton = skeletonize(binary_image)
        hits = np.sum(skeleton[shell_mask])
        intersections.append(int(hits))
        
    return {"radii": radius_steps, "intersections": intersections}

def denoise_and_subtract(image: np.ndarray) -> np.ndarray:
    """
    Apply denoising and background subtraction.
    
    Args:
        image: Raw image.
        
    Returns:
        Processed image.
    """
    if handle_empty_fields(image, "unknown"):
        return np.zeros_like(image)
        
    # Simple mean filter for denoising (can be replaced with more advanced if needed)
    from scipy.ndimage import uniform_filter
    denoised = uniform_filter(image.astype(float), size=3)
    
    # Background subtraction: assume background is the mode or a low percentile
    # Using a simple rolling ball approximation or just global thresholding
    # For this implementation, we'll use Otsu's thresholding logic roughly
    # or just subtract the minimum value if it's not 0.
    background = np.percentile(image, 10)
    processed = denoised - background
    processed = np.maximum(processed, 0)
    
    return processed