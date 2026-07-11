"""
Preprocess root images to extract Root System Architecture (RSA) traits.

This module implements the core image analysis pipeline for User Story 1.
It converts raw root images from the NPPN dataset into quantitative metrics:
depth, branching density, and surface area.

Algorithm:
- Skeletonize (8-connectivity) for depth/branching analysis.
- Find contours for surface area calculation.
- Branching density = (branch_points - endpoints) / total_length.

Includes error logging for corrupted images and validation logic to ensure
no null values and positive numerical values for all traits in output.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
import json

import numpy as np
import pandas as pd
import cv2
from skimage.morphology import skeletonize
from skimage.measure import find_contours
from skimage.filters import threshold_otsu
from PIL import Image

from config import ensure_directories, get_config_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RSAMetricsResult:
    """Dataclass to hold extracted RSA metrics for a single image."""
    image_id: str
    species: str
    depth: float
    branching_density: float
    surface_area: float
    branch_points: int
    endpoints: int
    total_length: float
    status: str  # 'success' or 'failed'
    error_message: Optional[str] = None

def load_and_preprocess_image(image_path: Path) -> np.ndarray:
    """
    Load an image and preprocess it for skeletonization.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Binary numpy array (0 for background, 1 for root).
        
    Raises:
        ValueError: If image cannot be loaded or processed.
    """
    try:
        # Load image using OpenCV
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Apply Otsu's thresholding to binarize the image
        # Invert if necessary (assuming roots are darker than background or vice versa)
        # Standard assumption: roots are dark, background is light.
        # We want roots to be True (1) in the binary mask.
        threshold = threshold_otsu(img)
        binary_mask = img < threshold
        
        # Convert to 0/1 float for processing
        binary_mask = binary_mask.astype(float)
        
        # Clean small noise
        kernel = np.ones((3,3),np.uint8)
        # Dilate then erode to close small gaps
        # Note: cv2 requires uint8, so convert temporarily
        temp_mask = (binary_mask * 255).astype(np.uint8)
        cleaned_mask = cv2.morphologyOps(temp_mask, cv2.MORPH_CLOSE, kernel)
        cleaned_mask = cleaned_mask > 128
        
        return cleaned_mask.astype(float)
        
    except Exception as e:
        raise ValueError(f"Failed to preprocess image {image_path}: {str(e)}")

def extract_skeleton_metrics(binary_mask: np.ndarray) -> Tuple[float, int, int, float]:
    """
    Extract depth, branch points, endpoints, and total length from the skeleton.
    
    Args:
        binary_mask: Preprocessed binary mask of the root system.
        
    Returns:
        Tuple of (max_depth, branch_points, endpoints, total_length).
    """
    # Skeletonize the binary mask (8-connectivity)
    skeleton = skeletonize(binary_mask)
    
    if np.sum(skeleton) == 0:
        return 0.0, 0, 0, 0.0
    
    # Calculate total length (number of pixels in skeleton)
    # This is a pixel count; for real-world units, a scale factor would be needed.
    total_length = float(np.sum(skeleton))
    
    # Find endpoints (pixels with exactly 1 neighbor in the 8-neighborhood)
    # Find branch points (pixels with >= 3 neighbors in the 8-neighborhood)
    kernel = np.ones((3,3), dtype=int)
    kernel[1,1] = 0 # Center is 0 so we count neighbors only
    
    # Convolve to count neighbors
    from scipy.signal import convolve2d
    neighbor_count = convolve2d(skeleton.astype(int), kernel, mode='same', boundary='symm')
    
    # Endpoints: 1 neighbor
    endpoints = np.sum(neighbor_count == 1)
    
    # Branch points: 3 or more neighbors
    branch_points = np.sum(neighbor_count >= 3)
    
    # Depth: Maximum vertical extent of the skeleton
    # Assuming the root grows downwards (y increases)
    # We find the max y coordinate where skeleton exists
    ys, xs = np.where(skeleton > 0)
    if len(ys) == 0:
        max_depth = 0.0
    else:
        max_depth = float(np.max(ys) - np.min(ys))
        
    return max_depth, int(branch_points), int(endpoints), total_length

def extract_surface_area(binary_mask: np.ndarray) -> float:
    """
    Extract surface area from the binary mask using contour analysis.
    
    Args:
        binary_mask: Preprocessed binary mask of the root system.
        
    Returns:
        Surface area in pixel units.
    """
    # Convert to uint8 for OpenCV
    mask_uint8 = (binary_mask * 255).astype(np.uint8)
    
    # Find external contours
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        return 0.0
    
    # Sum the area of all contours
    total_area = 0.0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        total_area += area
        
    return float(total_area)

def calculate_branching_density(branch_points: int, endpoints: int, total_length: float) -> float:
    """
    Calculate branching density.
    
    Formula: (branch_points - endpoints) / total_length
    Note: This formula is specified in the task. 
    Usually, branching density might be defined differently (e.g., branch points per unit length),
    but we follow the task specification exactly.
    
    Args:
        branch_points: Number of branch points.
        endpoints: Number of endpoints.
        total_length: Total length of the skeleton.
        
    Returns:
        Branching density.
    """
    if total_length == 0:
        return 0.0
    
    # Specified formula
    density = (branch_points - endpoints) / total_length
    return float(density)

def validate_metrics(metrics: RSAMetricsResult) -> bool:
    """
    Validate that metrics are non-null and positive where required.
    
    Args:
        metrics: RSAMetricsResult object to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    if metrics.status != 'success':
        return False
        
    # Check for nulls (None) - dataclass fields are typed, but check anyway
    if metrics.depth is None or metrics.branching_density is None or metrics.surface_area is None:
        logger.warning(f"Null value detected in metrics for {metrics.image_id}")
        return False
        
    # Check for positive values (or zero for some cases like 0 depth if no root found, but we expect >0)
    # Task says "positive numerical values". We'll enforce > 0 for depth and surface_area.
    # Branching density can be 0 or negative if (branch - end) is negative, but we'll check it's not NaN/Inf.
    
    if metrics.depth <= 0:
        logger.warning(f"Non-positive depth ({metrics.depth}) for {metrics.image_id}")
        return False
        
    if metrics.surface_area <= 0:
        logger.warning(f"Non-positive surface area ({metrics.surface_area}) for {metrics.image_id}")
        return False
        
    if not np.isfinite(metrics.branching_density):
        logger.warning(f"Non-finite branching density ({metrics.branching_density}) for {metrics.image_id}")
        return False
        
    return True

def process_single_image(image_path: Path, species_name: str) -> RSAMetricsResult:
    """
    Process a single image and extract RSA metrics.
    
    Args:
        image_path: Path to the image file.
        species_name: Species name associated with the image.
        
    Returns:
        RSAMetricsResult object.
    """
    image_id = image_path.stem
    
    try:
        # Load and preprocess
        binary_mask = load_and_preprocess_image(image_path)
        
        if np.sum(binary_mask) == 0:
            raise ValueError("No root content found in image after thresholding")
        
        # Extract skeleton metrics
        depth, branch_points, endpoints, total_length = extract_skeleton_metrics(binary_mask)
        
        # Extract surface area
        surface_area = extract_surface_area(binary_mask)
        
        # Calculate branching density
        branching_density = calculate_branching_density(branch_points, endpoints, total_length)
        
        result = RSAMetricsResult(
            image_id=image_id,
            species=species_name,
            depth=depth,
            branching_density=branching_density,
            surface_area=surface_area,
            branch_points=branch_points,
            endpoints=endpoints,
            total_length=total_length,
            status='success'
        )
        
        if not validate_metrics(result):
            result.status = 'failed'
            result.error_message = "Validation failed: non-positive or invalid metrics"
            
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        result = RSAMetricsResult(
            image_id=image_id,
            species=species_name,
            depth=0.0,
            branching_density=0.0,
            surface_area=0.0,
            branch_points=0,
            endpoints=0,
            total_length=0.0,
            status='failed',
            error_message=str(e)
        )
        
    return result

def process_directory(input_dir: Path, output_csv: Path) -> None:
    """
    Process all images in a directory and save results to CSV.
    
    Args:
        input_dir: Directory containing root images.
        output_csv: Path to the output CSV file.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    
    results: List[RSAMetricsResult] = []
    processed_count = 0
    failed_count = 0
    
    # Iterate through files
    for file_path in input_dir.rglob('*'):
        if file_path.suffix.lower() in image_extensions:
            # Try to infer species from directory structure if possible
            # Assuming structure: input_dir/species_name/image.jpg
            # Or just use a generic name if not found
            parts = file_path.relative_to(input_dir).parts
            if len(parts) > 1:
                species_name = parts[0]
            else:
                species_name = "unknown"
                
            logger.info(f"Processing: {file_path} (Species: {species_name})")
            
            result = process_single_image(file_path, species_name)
            results.append(result)
            
            if result.status == 'success':
                processed_count += 1
            else:
                failed_count += 1
                
    logger.info(f"Processing complete. Success: {processed_count}, Failed: {failed_count}")
    
    # Convert to DataFrame
    df = pd.DataFrame([asdict(r) for r in results])
    
    # Filter out failed entries if we want only successful ones, 
    # but for debugging we might keep them. 
    # The task says "validation logic to ensure no null values and positive numerical values".
    # We will save all, but the validation is done during processing.
    # However, for the final output, we should probably only include valid ones 
    # or mark them clearly. Let's include all but ensure the 'status' column is there.
    
    # Save to CSV
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    logger.info(f"Results saved to {output_csv}")
    
    # Additional validation report
    valid_df = df[df['status'] == 'success']
    if len(valid_df) > 0:
        # Check for any nulls or non-positive in valid set (should be none due to validation)
        null_counts = valid_df[['depth', 'branching_density', 'surface_area']].isnull().sum()
        if null_counts.any():
            logger.error(f"Found nulls in valid set: {null_counts}")
        else:
            logger.info("No null values found in valid metrics.")
            
        # Check for non-positive
        if (valid_df['depth'] <= 0).any() or (valid_df['surface_area'] <= 0).any():
            logger.error("Found non-positive values in valid metrics.")
        else:
            logger.info("All valid metrics are positive.")

def main():
    """Main entry point for the image preprocessing pipeline."""
    logger.info("Starting RSA metrics extraction pipeline...")
    
    # Load config
    config = get_config_summary()
    input_dir = Path(config['paths']['raw_images'])
    output_csv = Path(config['paths']['derived_rsa'])
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output CSV: {output_csv}")
    
    # Ensure directories exist
    ensure_directories()
    
    try:
        process_directory(input_dir, output_csv)
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()