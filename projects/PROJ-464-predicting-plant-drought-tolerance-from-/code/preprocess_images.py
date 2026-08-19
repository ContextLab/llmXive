"""
Preprocess root images to extract Root System Architecture (RSA) metrics.

This module implements the image processing pipeline to convert raw root images
from the NPPN Plant Phenome Pipeline into quantitative architectural metrics:
- Depth: Maximum vertical extent of the root system
- Branching Density: (branch_points - endpoints) / total_length
- Surface Area: Calculated from contour analysis

Uses OpenCV and scikit-image for CPU-optimized processing.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage.measure import find_contours
import pandas as pd
from config import ensure_directories, get_config_summary

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RSAMetricsResult:
    """Data class to hold RSA metrics for a single image."""
    image_id: str
    species: str
    depth: float
    branching_density: float
    surface_area: float
    status: str  # 'success' or 'error'
    error_message: Optional[str] = None

def load_and_preprocess_image(image_path: Path) -> Optional[np.ndarray]:
    """
    Load and preprocess a single root image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Preprocessed binary image (0 for background, 1 for root) or None if error
    """
    try:
        # Load image
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Threshold to create binary mask (roots are typically darker than background)
        # Using Otsu's thresholding for automatic threshold selection
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Convert to boolean mask (0 for background, True for root)
        mask = cleaned > 0
        
        return mask
    
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        return None

def extract_skeleton_metrics(mask: np.ndarray, image_id: str) -> Tuple[float, int, int, float]:
    """
    Extract depth and branching metrics from the skeletonized root system.
    
    Args:
        mask: Binary mask of the root system
        image_id: Identifier for the image
        
    Returns:
        Tuple of (depth, branch_points, endpoints, total_length)
    """
    if not np.any(mask):
        logger.warning(f"Empty mask for {image_id}")
        return 0.0, 0, 0, 0.0
    
    # Skeletonize the root system (8-connectivity)
    skeleton = skeletonize(mask)
    
    # Calculate total length of skeleton
    total_length = np.sum(skeleton)
    
    if total_length == 0:
        logger.warning(f"Zero skeleton length for {image_id}")
        return 0.0, 0, 0, 0.0
    
    # Find endpoints (pixels with only 1 neighbor)
    # Convolve with a 3x3 kernel to count neighbors
    kernel = np.ones((3, 3), dtype=np.uint8)
    kernel[1, 1] = 0  # Exclude center pixel
    
    neighbor_count = cv2.filter2D(skeleton.astype(np.uint8), -1, kernel)
    
    # Endpoints have exactly 1 neighbor
    endpoints = np.sum(neighbor_count == 1)
    
    # Branch points have 3 or more neighbors
    branch_points = np.sum(neighbor_count >= 3)
    
    # Depth: maximum vertical extent (assuming roots grow downward)
    # Find all non-zero pixel coordinates
    coords = np.column_stack(np.where(skeleton))
    if len(coords) == 0:
        depth = 0.0
    else:
        # Assuming row index represents vertical position (0 at top)
        # Depth is the maximum row index
        depth = float(np.max(coords[:, 0]))
    
    return depth, branch_points, endpoints, total_length

def extract_surface_area(mask: np.ndarray, image_id: str) -> float:
    """
    Extract surface area from the root system mask using contour analysis.
    
    Args:
        mask: Binary mask of the root system
        image_id: Identifier for the image
        
    Returns:
        Surface area (number of pixels in the root system)
    """
    if not np.any(mask):
        logger.warning(f"Empty mask for {image_id}")
        return 0.0
    
    # Convert mask to uint8 for OpenCV
    mask_uint8 = (mask * 255).astype(np.uint8)
    
    # Find contours
    contours, _ = find_contours(mask_uint8)
    
    if not contours:
        logger.warning(f"No contours found for {image_id}")
        return 0.0
    
    # Calculate total area from all contours
    total_area = 0.0
    for contour in contours:
        # Area is simply the number of pixels in the contour
        area = cv2.contourArea(contour)
        total_area += area
    
    # If no contours were found via find_contours, fall back to pixel count
    if total_area == 0:
        total_area = float(np.sum(mask))
    
    return total_area

def calculate_branching_density(branch_points: int, endpoints: int, total_length: float) -> float:
    """
    Calculate branching density using the formula: (branch_points - endpoints) / total_length.
    
    Args:
        branch_points: Number of branch points in the skeleton
        endpoints: Number of endpoints in the skeleton
        total_length: Total length of the skeleton
        
    Returns:
        Branching density value
    """
    if total_length == 0:
        return 0.0
    
    # Formula: (branch_points - endpoints) / total_length
    density = (branch_points - endpoints) / total_length
    
    # Ensure non-negative (in case of calculation artifacts)
    return max(0.0, density)

def validate_metrics(metrics: RSAMetricsResult) -> bool:
    """
    Validate that all metrics are non-null and positive.
    
    Args:
        metrics: RSAMetricsResult object to validate
        
    Returns:
        True if validation passes, False otherwise
    """
    if metrics.status != 'success':
        return False
    
    # Check for null/None values
    if metrics.depth is None or metrics.branching_density is None or metrics.surface_area is None:
        logger.error(f"Null values detected for {metrics.image_id}")
        return False
    
    # Check for positive values
    if metrics.depth <= 0:
        logger.error(f"Non-positive depth for {metrics.image_id}: {metrics.depth}")
        return False
    
    if metrics.surface_area <= 0:
        logger.error(f"Non-positive surface area for {metrics.image_id}: {metrics.surface_area}")
        return False
    
    # Branching density can be zero but not negative
    if metrics.branching_density < 0:
        logger.error(f"Negative branching density for {metrics.image_id}: {metrics.branching_density}")
        return False
    
    return True

def process_single_image(image_path: Path, image_id: str, species: str) -> RSAMetricsResult:
    """
    Process a single image and extract all RSA metrics.
    
    Args:
        image_path: Path to the image file
        image_id: Identifier for the image
        species: Species name associated with the image
        
    Returns:
        RSAMetricsResult containing the extracted metrics
    """
    try:
        # Load and preprocess image
        mask = load_and_preprocess_image(image_path)
        
        if mask is None:
            return RSAMetricsResult(
                image_id=image_id,
                species=species,
                depth=0.0,
                branching_density=0.0,
                surface_area=0.0,
                status='error',
                error_message='Failed to load or preprocess image'
            )
        
        # Extract skeleton metrics
        depth, branch_points, endpoints, total_length = extract_skeleton_metrics(mask, image_id)
        
        # Extract surface area
        surface_area = extract_surface_area(mask, image_id)
        
        # Calculate branching density
        branching_density = calculate_branching_density(branch_points, endpoints, total_length)
        
        # Create result object
        result = RSAMetricsResult(
            image_id=image_id,
            species=species,
            depth=depth,
            branching_density=branching_density,
            surface_area=surface_area,
            status='success'
        )
        
        # Validate metrics
        if not validate_metrics(result):
            result.status = 'error'
            result.error_message = 'Validation failed: non-null and positive values required'
            logger.warning(f"Validation failed for {image_id}")
        
        return result
    
    except Exception as e:
        logger.error(f"Unexpected error processing {image_id}: {str(e)}")
        return RSAMetricsResult(
            image_id=image_id,
            species=species,
            depth=0.0,
            branching_density=0.0,
            surface_area=0.0,
            status='error',
            error_message=f'Unexpected error: {str(e)}'
        )

def process_directory(input_dir: Path, output_path: Path) -> List[RSAMetricsResult]:
    """
    Process all images in a directory and generate a CSV with RSA metrics.
    
    Args:
        input_dir: Directory containing root images
        output_path: Path to write the output CSV file
        
    Returns:
        List of RSAMetricsResult objects
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
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
        df = pd.DataFrame(columns=['image_id', 'species', 'depth', 'branching_density', 'surface_area', 'status', 'error_message'])
        df.to_csv(output_path, index=False)
        return []
    
    logger.info(f"Found {len(image_files)} image files to process")
    
    results = []
    successful = 0
    failed = 0
    
    for image_path in image_files:
        # Generate image_id from filename (without extension)
        image_id = image_path.stem
        
        # Extract species from directory structure or filename
        # Assuming species is in the parent directory name or part of the filename
        species = image_path.parent.name
        if species == input_dir.name:
            # If parent is the input directory, try to extract from filename
            # Assume format: species_imageName.ext
            parts = image_path.stem.split('_')
            if len(parts) > 1:
                species = parts[0]
            else:
                species = 'unknown'
        
        logger.info(f"Processing {image_id} (species: {species})")
        
        result = process_single_image(image_path, image_id, species)
        results.append(result)
        
        if result.status == 'success':
            successful += 1
        else:
            failed += 1
            logger.warning(f"Failed to process {image_id}: {result.error_message}")
    
    # Convert results to DataFrame
    df_data = [asdict(r) for r in results]
    df = pd.DataFrame(df_data)
    
    # Ensure correct column order
    columns = ['image_id', 'species', 'depth', 'branching_density', 'surface_area', 'status', 'error_message']
    df = df[columns]
    
    # Write to CSV
    df.to_csv(output_path, index=False)
    
    logger.info(f"Processing complete: {successful} successful, {failed} failed")
    logger.info(f"Results written to {output_path}")
    
    # Final validation: ensure no null values and positive numerical values in successful rows
    successful_df = df[df['status'] == 'success']
    if len(successful_df) > 0:
        # Check for null values
        null_counts = successful_df[['depth', 'branching_density', 'surface_area']].isnull().sum()
        if null_counts.any():
            logger.error(f"Null values found in successful results: {null_counts.to_dict()}")
            raise ValueError("Null values detected in successful results")
        
        # Check for positive values
        if (successful_df['depth'] <= 0).any():
            logger.error("Non-positive depth values found in successful results")
            raise ValueError("Non-positive depth values detected")
        
        if (successful_df['surface_area'] <= 0).any():
            logger.error("Non-positive surface area values found in successful results")
            raise ValueError("Non-positive surface area values detected")
        
        if (successful_df['branching_density'] < 0).any():
            logger.error("Negative branching density values found in successful results")
            raise ValueError("Negative branching density values detected")
        
        logger.info("Final validation passed: all successful results have non-null, positive numerical values")
    
    return results

def main():
    """Main entry point for the image preprocessing pipeline."""
    logger.info("Starting RSA metrics extraction pipeline")
    
    # Load configuration
    config = get_config_summary()
    
    # Define paths
    input_dir = Path(config['data_raw_dir']) / 'nppn_images'
    output_path = Path(config['data_derived_dir']) / 'rsametrics.csv'
    
    # Ensure directories exist
    ensure_directories()
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        logger.error("Please run download_images.py first to fetch the root images")
        sys.exit(1)
    
    # Process images
    try:
        results = process_directory(input_dir, output_path)
        
        if not results:
            logger.warning("No results generated")
            sys.exit(1)
        
        successful_count = sum(1 for r in results if r.status == 'success')
        if successful_count == 0:
            logger.error("No images were successfully processed")
            sys.exit(1)
        
        logger.info(f"Pipeline completed successfully. {successful_count}/{len(results)} images processed")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()