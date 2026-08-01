"""
Feature Extraction for Test Set (T022a)

Extracts grain size features for the test set ONLY to prevent data leakage.
Input: manifest.csv and data/processed/test/
Output: data/features/test_grain_features.csv
"""
import os
import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import cv2
import numpy as np

# Import existing config utilities
from utils.config import get_project_root, get_data_dir, get_processed_dir, get_results_dir, get_code_dir

def get_logger_module():
    """Setup logger for this module."""
    logger = logging.getLogger('extract_features')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
    return logger

def estimate_grain_size(image_path: Path) -> Optional[float]:
    """
    Estimate grain size (in micrometers) from a preprocessed EBSD image.
    
    Uses a simplified image processing pipeline:
    1. Convert to grayscale
    2. Apply adaptive thresholding to segment grain boundaries
    3. Count connected components or measure grain diameters
    
    Note: This is a heuristic estimation based on the synthetic dataset properties.
    In a real scenario, this would use calibrated EBSD grain boundary detection.
    
    Args:
        image_path: Path to the preprocessed image (224x224)
        
    Returns:
        Estimated grain size in micrometers, or None if estimation fails
    """
    try:
        # Read image
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            logging.warning(f"Could not read image: {image_path}")
            return None
        
        # Apply adaptive threshold to highlight grain boundaries
        # Synthetic EBSD images typically have dark boundaries
        thresh = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Morphological operations to clean up noise
        kernel = np.ones((3,3), np.uint8)
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        eroded = cv2.erode(dilated, kernel, iterations=1)
        
        # Find contours to estimate grain sizes
        contours, _ = cv2.findContours(
            eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        
        if not contours:
            logging.warning(f"No contours found in {image_path}")
            return None
        
        # Calculate equivalent circular diameter for each contour
        # and take the median as the representative grain size
        grain_sizes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 10:  # Filter small noise
                # Equivalent circular diameter: d = 2 * sqrt(A/pi)
                diameter = 2 * np.sqrt(area / np.pi)
                grain_sizes.append(diameter)
        
        if not grain_sizes:
            return None
        
        # Return median grain size in pixels, scaled to micrometers
        # Assuming 1 pixel = 0.1 um for this synthetic dataset
        median_pixels = np.median(grain_sizes)
        grain_size_um = median_pixels * 0.1
        
        return round(grain_size_um, 2)
        
    except Exception as e:
        logging.error(f"Error estimating grain size for {image_path}: {e}")
        return None

def extract_features_for_dataset(manifest_path: Path, test_dir: Path) -> List[Tuple[str, float]]:
    """
    Extract grain size features for all images in the test set.
    
    Args:
        manifest_path: Path to manifest.csv containing test set image info
        test_dir: Path to data/processed/test/ directory
        
    Returns:
        List of (image_id, grain_size_um) tuples
    """
    logger = get_logger_module()
    features = []
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    if not test_dir.exists():
        raise FileNotFoundError(f"Test directory not found: {test_dir}")
    
    logger.info(f"Reading manifest from {manifest_path}")
    logger.info(f"Processing images from {test_dir}")
    
    with open(manifest_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            image_id = row['image_id']
            filename = row['filename']
            image_path = test_dir / filename
            
            if not image_path.exists():
                logger.warning(f"Image not found: {image_path}, skipping")
                continue
            
            grain_size = estimate_grain_size(image_path)
            
            if grain_size is not None:
                features.append((image_id, grain_size))
                logger.debug(f"Extracted grain size {grain_size} um for {image_id}")
            else:
                logger.warning(f"Failed to estimate grain size for {image_id}")
    
    return features

def main():
    """Main entry point for feature extraction."""
    logger = get_logger_module()
    logger.info("Starting test set feature extraction (T022a)")
    
    try:
        # Get paths
        project_root = get_project_root()
        manifest_path = project_root / "data" / "processed" / "manifest.csv"
        test_dir = project_root / "data" / "processed" / "test"
        output_dir = project_root / "data" / "features"
        output_path = output_dir / "test_grain_features.csv"
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Extract features
        features = extract_features_for_dataset(manifest_path, test_dir)
        
        if not features:
            logger.error("No features extracted. Check input data.")
            sys.exit(1)
        
        # Write output CSV
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['image_id', 'grain_size_um'])
            for image_id, grain_size in features:
                writer.writerow([image_id, grain_size])
        
        logger.info(f"Successfully extracted {len(features)} features")
        logger.info(f"Output written to {output_path}")
        
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()