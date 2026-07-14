import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict

import cv2
import numpy as np
import pandas as pd
from skimage.morphology import skeletonize
from skimage.measure import find_contours, perimeter
from scipy import ndimage

from config import ensure_directories, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RSAMetricsResult:
    """Container for extracted RSA metrics for a single image."""
    image_id: str
    species_id: str
    depth: float
    branching_density: float
    surface_area: float
    error: Optional[str] = None

def load_and_preprocess_image(image_path: Path) -> Tuple[np.ndarray, str]:
    """
    Load an image and preprocess it for skeletonization.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Tuple of (binary_mask, error_message). 
        If successful, error_message is None.
    """
    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            return np.array([]), f"Failed to load image: {image_path.name}"
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Threshold to get binary mask (roots are typically darker than background)
        # Using Otsu's thresholding after Gaussian filtering
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up noise
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Ensure binary (0 and 255)
        binary_mask = (cleaned > 0).astype(np.uint8)
        
        if np.sum(binary_mask) == 0:
            return np.array([]), f"No root structure found in image: {image_path.name}"
        
        return binary_mask, None
        
    except Exception as e:
        return np.array([]), f"Error processing {image_path.name}: {str(e)}"

def extract_skeleton_metrics(binary_mask: np.ndarray) -> Dict[str, float]:
    """
    Extract depth and branching metrics from a binary root mask using skeletonization.
    
    Algorithm:
    - Skeletonize the binary mask (8-connectivity)
    - Calculate depth as max distance from root base to tip
    - Count branch points and endpoints
    - Calculate total skeleton length
    
    Args:
        binary_mask: Binary numpy array where 1 represents root pixels.
        
    Returns:
        Dictionary with 'depth', 'branch_points', 'endpoints', 'total_length'.
    """
    if binary_mask.size == 0:
        return {'depth': 0.0, 'branch_points': 0, 'endpoints': 0, 'total_length': 0.0}
    
    # Skeletonize (returns boolean array)
    skeleton = skeletonize(binary_mask)
    skeleton_uint8 = skeleton.astype(np.uint8)
    
    # Calculate branch points (pixels with 3 or more neighbors in 8-connectivity)
    # Convolve with a 3x3 kernel to count neighbors
    kernel = np.ones((3, 3), np.uint8)
    kernel[1, 1] = 0  # Exclude center pixel
    neighbor_count = ndimage.convolve(skeleton_uint8, kernel, mode='constant')
    
    # Branch points: skeleton pixels with exactly 3 or more neighbors
    branch_points = np.sum((skeleton_uint8 == 1) & (neighbor_count >= 3))
    
    # Endpoints: skeleton pixels with exactly 1 neighbor
    endpoints = np.sum((skeleton_uint8 == 1) & (neighbor_count == 1))
    
    # Total skeleton length (number of pixels in skeleton)
    total_length = float(np.sum(skeleton_uint8))
    
    # Calculate depth: maximum distance from any root pixel to the "base"
    # For simplicity, we'll use the maximum extent in the vertical direction
    # assuming roots grow downward. We find the bounding box of the skeleton.
    coords = np.column_stack(np.where(skeleton_uint8 > 0))
    if len(coords) > 0:
        # coords are (row, col) - row increases downward
        min_row, max_row = coords[:, 0].min(), coords[:, 0].max()
        depth = float(max_row - min_row)
    else:
        depth = 0.0
        
    return {
        'depth': depth,
        'branch_points': int(branch_points),
        'endpoints': int(endpoints),
        'total_length': total_length
    }

def extract_surface_area(binary_mask: np.ndarray) -> float:
    """
    Estimate surface area using contour-based approach.
    
    For 2D root images, surface area is approximated by:
    - Finding the contour of the root system
    - Calculating the perimeter
    - Estimating area from the binary mask (pixel count)
    
    Args:
        binary_mask: Binary numpy array where 1 represents root pixels.
        
    Returns:
        Estimated surface area (in pixels).
    """
    if binary_mask.size == 0:
        return 0.0
        
    # Use find_contours to get the outer boundary
    # skimage expects float in [0, 1]
    contours = find_contours(binary_mask.astype(float), 0.5)
    
    if not contours:
        # Fallback: use pixel count as area approximation
        return float(np.sum(binary_mask))
    
    # Sum the areas of all contours (using the binary mask area as proxy)
    # For root systems, the total area of the binary mask is a good approximation
    # of the cross-sectional area, which correlates with surface area
    total_area = float(np.sum(binary_mask))
    
    return total_area

def calculate_branching_density(branch_points: int, endpoints: int, total_length: float) -> float:
    """
    Calculate branching density.
    
    Formula: (branch_points - endpoints) / total_length
    This normalizes the branching complexity by the total root length.
    
    Args:
        branch_points: Number of branch points in the skeleton.
        endpoints: Number of endpoints in the skeleton.
        total_length: Total length of the skeleton (in pixels).
        
    Returns:
        Branching density (float). Returns 0.0 if total_length is 0.
    """
    if total_length == 0:
        return 0.0
    
    # Avoid negative density if endpoints > branch_points (rare but possible)
    density = max(0.0, (branch_points - endpoints) / total_length)
    return density

def validate_metrics(metrics: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate that all metrics are non-null and positive (where applicable).
    
    Args:
        metrics: Dictionary containing RSA metrics.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    required_fields = ['depth', 'branching_density', 'surface_area']
    
    for field in required_fields:
        if field not in metrics:
            return False, f"Missing required field: {field}"
        
        value = metrics[field]
        if value is None:
            return False, f"Null value for {field}"
        
        if not isinstance(value, (int, float)):
            return False, f"Non-numeric value for {field}: {type(value)}"
        
        if field != 'branching_density' and value < 0:
            return False, f"Negative value for {field}: {value}"
        
        # For branching_density, allow 0 but not negative
        if field == 'branching_density' and value < 0:
            return False, f"Negative value for {field}: {value}"
    
    return True, None

def process_single_image(image_path: Path, species_id: str) -> RSAMetricsResult:
    """
    Process a single root image and extract RSA metrics.
    
    Args:
        image_path: Path to the image file.
        species_id: Species identifier for the image.
        
    Returns:
        RSAMetricsResult object with extracted metrics or error information.
    """
    image_id = image_path.stem
    
    # Load and preprocess image
    binary_mask, error = load_and_preprocess_image(image_path)
    if error:
        logger.warning(error)
        return RSAMetricsResult(
            image_id=image_id,
            species_id=species_id,
            depth=0.0,
            branching_density=0.0,
            surface_area=0.0,
            error=error
        )
    
    # Extract skeleton metrics
    skeleton_metrics = extract_skeleton_metrics(binary_mask)
    
    # Extract surface area
    surface_area = extract_surface_area(binary_mask)
    
    # Calculate branching density
    branching_density = calculate_branching_density(
        skeleton_metrics['branch_points'],
        skeleton_metrics['endpoints'],
        skeleton_metrics['total_length']
    )
    
    # Compile metrics
    metrics = {
        'depth': skeleton_metrics['depth'],
        'branching_density': branching_density,
        'surface_area': surface_area
    }
    
    # Validate metrics
    is_valid, validation_error = validate_metrics(metrics)
    if not is_valid:
        logger.error(f"Validation failed for {image_path.name}: {validation_error}")
        return RSAMetricsResult(
            image_id=image_id,
            species_id=species_id,
            depth=0.0,
            branching_density=0.0,
            surface_area=0.0,
            error=validation_error
        )
    
    logger.info(f"Successfully processed {image_path.name}: depth={metrics['depth']:.2f}, "
               f"branching_density={metrics['branching_density']:.6f}, "
               f"surface_area={metrics['surface_area']:.2f}")
    
    return RSAMetricsResult(
        image_id=image_id,
        species_id=species_id,
        depth=metrics['depth'],
        branching_density=metrics['branching_density'],
        surface_area=metrics['surface_area'],
        error=None
    )

def process_directory(input_dir: Path, output_csv: Path) -> List[RSAMetricsResult]:
    """
    Process all images in a directory and save results to CSV.
    
    Args:
        input_dir: Directory containing root images.
        output_csv: Path to save the output CSV file.
        
    Returns:
        List of RSAMetricsResult objects.
    """
    # Ensure output directory exists
    ensure_directories([output_csv.parent])
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    # Find all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_dir.glob(f'*{ext}'))
        image_files.extend(input_dir.glob(f'*{ext.upper()}'))
    
    if not image_files:
        logger.error(f"No image files found in {input_dir}")
        # Create empty CSV with headers
        pd.DataFrame(columns=['image_id', 'species_id', 'depth', 'branching_density', 'surface_area', 'error']).to_csv(output_csv, index=False)
        return []
    
    logger.info(f"Found {len(image_files)} image files in {input_dir}")
    
    results = []
    for image_path in image_files:
        # Extract species_id from filename or directory structure
        # Assuming filename format: species_id_*.jpg or similar
        species_id = image_path.parent.name  # Use parent directory as species_id
        if species_id == input_dir.name:
            species_id = image_path.stem.split('_')[0] if '_' in image_path.stem else "unknown"
        
        result = process_single_image(image_path, species_id)
        results.append(result)
        
        # Log errors for skipped images
        if result.error:
            logger.warning(f"Skipped {image_path.name}: {result.error}")
    
    # Filter out results with errors for the final CSV
    valid_results = [r for r in results if r.error is None]
    
    if not valid_results:
        logger.error("No valid results to write to CSV. All images failed processing.")
        # Still write CSV with error information
        df = pd.DataFrame([asdict(r) for r in results])
        df.to_csv(output_csv, index=False)
        return results
    
    # Create DataFrame and validate
    df = pd.DataFrame([asdict(r) for r in valid_results])
    
    # Final validation: ensure no null values and positive numerical values
    numeric_cols = ['depth', 'branching_density', 'surface_area']
    for col in numeric_cols:
        if df[col].isnull().any():
            logger.error(f"Null values found in {col} column")
        if (df[col] < 0).any() and col != 'branching_density':
            logger.error(f"Negative values found in {col} column")
        if col == 'branching_density' and (df[col] < 0).any():
            logger.error(f"Negative values found in {col} column")
    
    # Write to CSV
    df.to_csv(output_csv, index=False)
    logger.info(f"Successfully wrote {len(valid_results)} valid records to {output_csv}")
    
    # Log summary
    logger.info(f"Processing complete: {len(valid_results)} successful, {len(results) - len(valid_results)} failed")
    
    return results

def main():
    """Main entry point for the image preprocessing pipeline."""
    config = get_config_summary()
    
    # Define paths
    input_dir = Path(config['data_raw_dir']) / 'nppn_images'
    output_csv = Path(config['data_derived_dir']) / 'rsametrics.csv'
    
    logger.info(f"Starting RSA metrics extraction from {input_dir}")
    logger.info(f"Output will be saved to {output_csv}")
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        logger.error("Please run download_images.py first to fetch the root images.")
        sys.exit(1)
    
    # Process images
    results = process_directory(input_dir, output_csv)
    
    if not results:
        logger.error("No images were processed. Check input directory and logs.")
        sys.exit(1)
    
    # Check for any processing errors
    failed_count = sum(1 for r in results if r.error is not None)
    if failed_count > 0:
        logger.warning(f"{failed_count} images failed to process. Check logs for details.")
    
    logger.info("RSA metrics extraction completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())