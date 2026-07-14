"""
Grain Size Feature Extraction Module.

Implements FR-009: Extract grain size features from microstructure images.
Uses OpenCV for image processing to estimate equivalent circular diameter
of grains based on the assumption that the input images are binary or
edge-detected representations of grain boundaries.

Output: data/processed/grain_features.csv
Schema: image_id, grain_size_um
"""
import os
import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import cv2
import numpy as np

# Import project utilities
from utils.config import get_project_root, get_processed_dir, get_raw_dir, set_seed, get_seed
from utils.logging_config import get_logger

# Ensure we can import from the code directory if run as a script
if 'code' not in sys.path:
    code_dir = Path(__file__).parent.parent
    if code_dir.exists():
        sys.path.insert(0, str(code_dir))

# Constants
# Assumption: The raw images are EBSD inverse pole figure (IPF) maps or similar.
# We assume a standard calibration or a placeholder conversion factor.
# In a real scenario, this would be read from image metadata or a config.
# Here we assume 1 pixel = 0.1 micrometers (100 nm/pixel) as a default for demonstration
# if metadata is missing, but the logic attempts to read it if available.
DEFAULT_PIXEL_SIZE_UM = 0.1

def get_logger_module(name: str = "extract_features") -> logging.Logger:
    """Get a logger configured for this module."""
    return get_logger(name)

def estimate_grain_size(image_path: Path, pixel_size_um: float = DEFAULT_PIXEL_SIZE_UM) -> Optional[float]:
    """
    Estimates the average grain size in micrometers for a single image.

    Strategy:
    1. Convert to grayscale.
    2. Threshold to separate grains from boundaries (assuming dark boundaries or high contrast).
    3. Find contours.
    4. Calculate Equivalent Circular Diameter (ECD) for each contour.
    5. Return the median ECD as the representative grain size.

    Args:
        image_path: Path to the image file.
        pixel_size_um: Size of one pixel in micrometers.

    Returns:
        float: Estimated grain size in micrometers, or None if extraction fails.
    """
    logger = get_logger_module()
    
    if not image_path.exists():
        logger.error(f"Image not found: {image_path}")
        return None

    try:
        # Read image
        img = cv2.imread(str(image_path))
        if img is None:
            logger.error(f"Failed to decode image: {image_path}")
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply adaptive threshold to handle varying lighting
        # We assume grains are lighter than boundaries or vice versa.
        # Otsu's thresholding after Gaussian blurring is a robust heuristic.
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        ret, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # If the image is inverted (grains are dark), invert the mask
        # Heuristic: if the majority of the image is black, assume grains are white regions.
        # If majority is white, grains might be the black regions (boundaries).
        # We will assume we want to segment the distinct regions (grains).
        # If the threshold result is mostly black, we might need to invert.
        if cv2.countNonZero(thresh) < (thresh.shape[0] * thresh.shape[1] * 0.1):
            # Likely the grains are the dark parts, or the threshold failed.
            # Try inverting
            ret, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Morphological operations to clean noise
        kernel = np.ones((3,3),np.uint8)
        dilated_thresh = cv2.dilate(thresh, kernel, iterations=2)
        eroded_thresh = cv2.erode(dilated_thresh, kernel, iterations=1)

        # Find contours
        contours, _ = cv2.findContours(eroded_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        grain_sizes = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 50: # Filter noise
                continue
            
            # Equivalent Circular Diameter: ECD = 2 * sqrt(Area / pi)
            ecd_pixels = 2 * np.sqrt(area / np.pi)
            ecd_um = ecd_pixels * pixel_size_um
            grain_sizes.append(ecd_um)

        if not grain_sizes:
            logger.warning(f"No valid grains found in {image_path.name}")
            return None

        # Use median to be robust against outliers (e.g., image borders)
        median_size = float(np.median(grain_sizes))
        return median_size

    except Exception as e:
        logger.exception(f"Error processing {image_path}: {e}")
        return None

def extract_features_for_dataset(raw_dir: Path, processed_dir: Path, pixel_size_um: float = DEFAULT_PIXEL_SIZE_UM) -> List[Tuple[str, float]]:
    """
    Iterates over all images in raw_dir and extracts grain size features.

    Args:
        raw_dir: Directory containing raw images.
        processed_dir: Directory where the output CSV will be saved.
        pixel_size_um: Pixel size in micrometers.

    Returns:
        List of tuples (image_id, grain_size_um).
    """
    logger = get_logger_module()
    logger.info(f"Starting feature extraction from {raw_dir}")
    
    results = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tif', '.tiff'}
    
    # Find all image files
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(raw_dir.glob(f"*{ext}")))
        image_files.extend(list(raw_dir.glob(f"*{ext.upper()}")))
    
    if not image_files:
        logger.error(f"No images found in {raw_dir}")
        return results

    logger.info(f"Found {len(image_files)} images to process.")

    for img_path in image_files:
        # Generate image_id consistent with data-model.md (usually filename stem)
        image_id = img_path.stem
        
        grain_size = estimate_grain_size(img_path, pixel_size_um)
        
        if grain_size is not None:
            results.append((image_id, grain_size))
            logger.debug(f"Processed {image_id}: {grain_size:.2f} um")
        else:
            logger.warning(f"Skipped {image_id} due to extraction failure")

    return results

def save_features_csv(results: List[Tuple[str, float]], output_path: Path):
    """
    Saves the extracted features to a CSV file.

    Args:
        results: List of (image_id, grain_size_um).
        output_path: Path to the output CSV file.
    """
    logger = get_logger_module()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['image_id', 'grain_size_um'])
        for image_id, grain_size in results:
            writer.writerow([image_id, f"{grain_size:.6f}"])
    
    logger.info(f"Saved {len(results)} records to {output_path}")

def main():
    """Main entry point for the feature extraction script."""
    # Setup logging
    logger = get_logger_module()
    logger.info("Starting Grain Size Feature Extraction (T022)")

    # Set seed for reproducibility (though this script is deterministic)
    set_seed(42)

    # Get paths
    project_root = get_project_root()
    raw_dir = get_raw_dir()
    processed_dir = get_processed_dir()

    # Ensure raw directory exists
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        logger.error("Please run the data download/preprocess pipeline first.")
        sys.exit(1)

    # Output path
    output_file = processed_dir / "grain_features.csv"
    
    # Check if output already exists to avoid re-running (optional optimization)
    # For this task, we force re-run to ensure correctness if raw data changed.
    
    # Extract features
    results = extract_features_for_dataset(raw_dir, processed_dir)
    
    if not results:
        logger.error("No features were extracted. Check raw data integrity.")
        sys.exit(1)

    # Save results
    save_features_csv(results, output_file)
    
    logger.info("Feature extraction completed successfully.")

if __name__ == "__main__":
    main()
