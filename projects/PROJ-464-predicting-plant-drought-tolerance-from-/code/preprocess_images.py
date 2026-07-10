"""
Preprocess root images to extract Root System Architecture (RSA) metrics.

This module processes images downloaded by download_images.py to extract:
- Depth (max vertical extent of the skeleton)
- Branching density (ratio of branch points to total length)
- Surface area (from contours)

Algorithm:
1. Load image, convert to grayscale, threshold
2. Skeletonize using 8-connectivity for depth/branching analysis
3. Find contours for surface area calculation
4. Calculate metrics and validate results
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
import cv2
from skimage.morphology import skeletonize
from skimage.feature import peak_local_max
from skimage import measure
from scipy import ndimage

# Import config for paths
try:
    from code.config import get_project_root, get_raw_image_dir, get_derived_data_dir
except ImportError:
    # Fallback if code directory is not in path during direct execution
    from pathlib import Path
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    def get_project_root(): return PROJECT_ROOT
    def get_raw_image_dir(): return PROJECT_ROOT / "data" / "raw" / "nppn_images"
    def get_derived_data_dir(): return PROJECT_ROOT / "data" / "derived"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class RSAMetricsResult:
    """Container for extracted RSA metrics."""
    image_id: str
    species_id: str
    depth: float
    branching_density: float
    surface_area: float
    total_length: float
    branch_points: int
    endpoints: int
    error: Optional[str] = None

def load_and_preprocess_image(image_path: Path) -> Optional[np.ndarray]:
    """
    Load an image, convert to grayscale, and apply thresholding.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Binary numpy array (0 for background, 1 for foreground) or None if failed
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
        
        # Threshold using Otsu's method
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Clean up noise with morphological operations
        kernel = np.ones((3, 3), np.uint8)
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # Ensure binary (0 and 255)
        binary_clean = (cleaned > 0).astype(np.uint8)
        
        return binary_clean
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        return None

def extract_skeleton_metrics(binary_image: np.ndarray) -> Dict[str, Any]:
    """
    Extract skeleton-based metrics: depth, branch points, endpoints, total length.
    
    Args:
        binary_image: Binary image (0 for background, 1 for foreground)
        
    Returns:
        Dictionary with skeleton metrics
    """
    # Skeletonize using 8-connectivity (default for skeletonize)
    skeleton = skeletonize(binary_image)
    
    if np.sum(skeleton) == 0:
        return {
            'skeleton': None,
            'depth': 0.0,
            'branch_points': 0,
            'endpoints': 0,
            'total_length': 0.0
        }
    
    # Calculate depth (max vertical extent)
    y_coords, x_coords = np.where(skeleton > 0)
    if len(y_coords) == 0:
        return {
            'skeleton': None,
            'depth': 0.0,
            'branch_points': 0,
            'endpoints': 0,
            'total_length': 0.0
        }
    
    depth = float(np.max(y_coords) - np.min(y_coords))
    
    # Calculate total length (number of skeleton pixels)
    total_length = float(np.sum(skeleton))
    
    # Detect branch points and endpoints using convolution
    # Kernel to detect 3-way connections (branch points)
    kernel_3 = np.array([
        [0, 1, 0],
        [1, 1, 1],
        [0, 1, 0]
    ], dtype=np.uint8)
    
    # Kernel to detect endpoints (1 connection)
    kernel_1 = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]
    ], dtype=np.uint8)
    
    # Convolve to find connections
    padded_skeleton = np.pad(skeleton.astype(np.uint8), 1, mode='constant')
    conv_result = ndimage.convolve(padded_skeleton.astype(np.float32), np.ones((3, 3)), mode='constant')
    
    # Count branch points (pixels with 3 or more neighbors in 8-connectivity)
    # A branch point has exactly 3 neighbors in the 8-neighborhood (excluding self)
    # But in skeleton, a branch point typically has 3 connections
    branch_mask = (conv_result >= 4) & (conv_result <= 5) # 3 neighbors + self = 4, 4 neighbors + self = 5 (junctions)
    # More precise: count neighbors for each skeleton pixel
    neighbors = ndimage.convolve(skeleton.astype(np.float32), np.ones((3, 3)), mode='constant')
    branch_points = int(np.sum((neighbors == 4) & skeleton)) # 3 neighbors + self
    
    # Count endpoints (pixels with exactly 1 neighbor)
    endpoints = int(np.sum((neighbors == 2) & skeleton)) # 1 neighbor + self
    
    return {
        'skeleton': skeleton,
        'depth': depth,
        'branch_points': branch_points,
        'endpoints': endpoints,
        'total_length': total_length
    }

def extract_surface_area(binary_image: np.ndarray) -> float:
    """
    Calculate surface area from the binary image using contour detection.
    
    Args:
        binary_image: Binary image (0 for background, 1 for foreground)
        
    Returns:
        Surface area in pixels
    """
    # Find contours
    contours, _ = cv2.findContours(
        binary_image.astype(np.uint8),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    total_area = 0.0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 10: # Filter out small noise
            total_area += area
    
    return float(total_area)

def calculate_branching_density(branch_points: int, endpoints: int, total_length: float) -> float:
    """
    Calculate branching density as (branch_points - endpoints) / total_length.
    
    Args:
        branch_points: Number of branch points
        endpoints: Number of endpoints
        total_length: Total skeleton length
        
    Returns:
        Branching density value
    """
    if total_length == 0:
        return 0.0
    
    # Avoid negative density
    numerator = max(0, branch_points - endpoints)
    return float(numerator) / total_length

def validate_metrics(metrics: RSAMetricsResult) -> bool:
    """
    Validate that all metrics are positive and non-null.
    
    Args:
        metrics: RSAMetricsResult to validate
        
    Returns:
        True if valid, False otherwise
    """
    if metrics.error is not None:
        return False
    
    if metrics.depth <= 0:
        logger.warning(f"Invalid depth for {metrics.image_id}: {metrics.depth}")
        return False
    
    if metrics.surface_area <= 0:
        logger.warning(f"Invalid surface area for {metrics.image_id}: {metrics.surface_area}")
        return False
    
    if metrics.total_length <= 0:
        logger.warning(f"Invalid total length for {metrics.image_id}: {metrics.total_length}")
        return False
    
    # Branching density can be 0 but not negative
    if metrics.branching_density < 0:
        logger.warning(f"Invalid branching density for {metrics.image_id}: {metrics.branching_density}")
        return False
    
    return True

def process_single_image(image_path: Path, species_id: str = "unknown") -> Optional[RSAMetricsResult]:
    """
    Process a single image and extract all RSA metrics.
    
    Args:
        image_path: Path to the image file
        species_id: Species identifier (extracted from filename if not provided)
        
    Returns:
        RSAMetricsResult or None if processing failed
    """
    image_id = image_path.stem
    
    # Try to extract species from filename if not provided
    if species_id == "unknown":
        # Assume format: species_id_XXX.png or similar
        parts = image_path.stem.split('_')
        if len(parts) > 0:
            species_id = parts[0]
    
    logger.info(f"Processing image: {image_id}")
    
    # Load and preprocess
    binary_image = load_and_preprocess_image(image_path)
    if binary_image is None:
        return RSAMetricsResult(
            image_id=image_id,
            species_id=species_id,
            depth=0.0,
            branching_density=0.0,
            surface_area=0.0,
            total_length=0.0,
            branch_points=0,
            endpoints=0,
            error="Failed to load or preprocess image"
        )
    
    # Extract skeleton metrics
    skeleton_metrics = extract_skeleton_metrics(binary_image)
    if skeleton_metrics['skeleton'] is None:
        return RSAMetricsResult(
            image_id=image_id,
            species_id=species_id,
            depth=0.0,
            branching_density=0.0,
            surface_area=0.0,
            total_length=0.0,
            branch_points=0,
            endpoints=0,
            error="No skeleton found in image"
        )
    
    # Extract surface area
    surface_area = extract_surface_area(binary_image)
    
    # Calculate branching density
    branching_density = calculate_branching_density(
        skeleton_metrics['branch_points'],
        skeleton_metrics['endpoints'],
        skeleton_metrics['total_length']
    )
    
    # Create result
    result = RSAMetricsResult(
        image_id=image_id,
        species_id=species_id,
        depth=skeleton_metrics['depth'],
        branching_density=branching_density,
        surface_area=surface_area,
        total_length=skeleton_metrics['total_length'],
        branch_points=skeleton_metrics['branch_points'],
        endpoints=skeleton_metrics['endpoints']
    )
    
    # Validate
    if not validate_metrics(result):
        result.error = "Validation failed: non-positive or null values detected"
    
    return result

def process_directory(input_dir: Path, output_path: Path) -> pd.DataFrame:
    """
    Process all images in a directory and save results to CSV.
    
    Args:
        input_dir: Directory containing images
        output_path: Path to save the output CSV
        
    Returns:
        DataFrame with all metrics
    """
    results: List[RSAMetricsResult] = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    
    # Get all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(input_dir.glob(f'*{ext}'))
        image_files.extend(input_dir.glob(f'*{ext.upper()}'))
    
    if not image_files:
        logger.warning(f"No image files found in {input_dir}")
        # Create empty DataFrame with correct columns
        df = pd.DataFrame(columns=['species_id', 'depth', 'branching_density', 'surface_area'])
        df.to_csv(output_path, index=False)
        return df
    
    logger.info(f"Found {len(image_files)} images to process")
    
    for img_path in image_files:
        try:
            result = process_single_image(img_path)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Unexpected error processing {img_path}: {str(e)}")
            results.append(RSAMetricsResult(
                image_id=img_path.stem,
                species_id="unknown",
                depth=0.0,
                branching_density=0.0,
                surface_area=0.0,
                total_length=0.0,
                branch_points=0,
                endpoints=0,
                error=f"Unexpected error: {str(e)}"
            ))
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        'species_id': r.species_id,
        'depth': r.depth,
        'branching_density': r.branching_density,
        'surface_area': r.surface_area
    } for r in results if r.error is None])
    
    # Log errors
    error_count = sum(1 for r in results if r.error is not None)
    if error_count > 0:
        logger.warning(f"Skipped {error_count} images due to errors")
        for r in results:
            if r.error:
                logger.error(f"Error for {r.image_id}: {r.error}")
    
    # Validate final DataFrame
    if not df.empty:
        null_counts = df.isnull().sum()
        if null_counts.any():
            logger.warning(f"DataFrame contains null values:\n{null_counts}")
        
        # Check for non-positive values
        for col in ['depth', 'branching_density', 'surface_area']:
            if (df[col] <= 0).any():
                logger.warning(f"Column {col} contains non-positive values")
    
    # Save to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved results to {output_path}")
    
    return df

def main():
    """Main entry point for the preprocessing pipeline."""
    logger.info("Starting RSA metrics extraction pipeline")
    
    # Get directories
    input_dir = get_raw_image_dir()
    output_path = get_derived_data_dir() / "rsametrics.csv"
    
    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output file: {output_path}")
    
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    # Process images
    df = process_directory(input_dir, output_path)
    
    if df.empty:
        logger.error("No valid metrics extracted. Pipeline failed.")
        sys.exit(1)
    
    logger.info(f"Successfully processed {len(df)} images")
    logger.info("Pipeline completed successfully")

if __name__ == "__main__":
    main()
