import os
import sys
import logging
import cv2
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

from config import get_paths, load_config
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_luminance(image: np.ndarray) -> float:
    """
    Compute luminance as the mean intensity of the grayscale image.
    
    Args:
        image: BGR image loaded by OpenCV.
        
    Returns:
        Mean intensity value (float).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(np.mean(gray))

def compute_contrast(image: np.ndarray) -> float:
    """
    Compute contrast as the standard deviation of the grayscale image.
    
    Args:
        image: BGR image loaded by OpenCV.
        
    Returns:
        Standard deviation value (float).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(np.std(gray))

def compute_edge_density(image: np.ndarray, low_threshold: int = 100, high_threshold: int = 200) -> float:
    """
    Compute edge density as the ratio of edge pixels to total pixels using Canny.
    
    Args:
        image: BGR image loaded by OpenCV.
        low_threshold: Lower threshold for Canny edge detection.
        high_threshold: Upper threshold for Canny edge detection.
        
    Returns:
        Ratio of edge pixels (float).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, low_threshold, high_threshold)
    edge_pixels = cv2.countNonZero(edges)
    total_pixels = edges.size
    return float(edge_pixels / total_pixels) if total_pixels > 0 else 0.0

def process_image_features(image_path: Path) -> Tuple[str, float, float, float]:
    """
    Process a single image to extract low-level features.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        Tuple of (image_id, luminance, contrast, edge_density).
        
    Raises:
        FileNotFoundError: If the image file does not exist.
        cv2.error: If the image cannot be decoded.
    """
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to decode image: {image_path}")
    
    image_id = image_path.stem
    luminance = compute_luminance(image)
    contrast = compute_contrast(image)
    edge_density = compute_edge_density(image)
    
    return image_id, luminance, contrast, edge_density

def collect_image_paths(raw_dir: Path) -> List[Path]:
    """
    Collect all valid image paths from the raw data directory.
    
    Args:
        raw_dir: Path to the raw data directory.
        
    Returns:
        List of Path objects for supported image formats.
    """
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    image_paths = []
    
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return image_paths
    
    for root, _, files in os.walk(raw_dir):
        for file in files:
            ext = Path(file).suffix.lower()
            if ext in valid_extensions:
                image_paths.append(Path(root) / file)
    
    logger.info(f"Found {len(image_paths)} images in {raw_dir}")
    return image_paths

def write_features_csv(features: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the extracted features to a CSV file.
    
    Args:
        features: List of dictionaries containing feature data.
        output_path: Path to the output CSV file.
    """
    df = pd.DataFrame(features)
    df.to_csv(output_path, index=False)
    logger.info(f"Features written to {output_path}")

def main() -> None:
    """
    Main entry point for generating low-level features.
    
    This function:
    1. Loads configuration to determine data paths.
    2. Scans the raw data directory for images.
    3. Computes luminance, contrast, and edge density for each image.
    4. Writes the results to data/interim/low_level_features.csv.
    
    Raises:
        Exception: If any image processing fails (fail loudly).
    """
    config = load_config()
    paths = get_paths()
    
    raw_dir = paths.raw_data
    output_path = paths.interim / "low_level_features.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting low-level feature generation for images in {raw_dir}")
    
    image_paths = collect_image_paths(raw_dir)
    
    if not image_paths:
        logger.warning("No images found to process. Creating empty CSV with headers.")
        pd.DataFrame(columns=["image_id", "luminance", "contrast", "edge_density"]).to_csv(output_path, index=False)
        return
    
    features = []
    failed_images = []
    
    for image_path in image_paths:
        try:
            logger.debug(f"Processing {image_path.name}")
            result = process_image_features(image_path)
            features.append({
                "image_id": result[0],
                "luminance": result[1],
                "contrast": result[2],
                "edge_density": result[3]
            })
        except Exception as e:
            error_msg = f"Failed to process {image_path.name}: {str(e)}"
            logger.error(error_msg)
            failed_images.append({"image_id": image_path.stem, "error": str(e)})
            # Fail loudly: do not continue if processing fails
            raise RuntimeError(error_msg) from e
    
    if failed_images:
        logger.error(f"Failed to process {len(failed_images)} images. See logs for details.")
    
    write_features_csv(features, output_path)
    
    logger.info(f"Successfully processed {len(features)} images.")
    logger.info(f"Output saved to {output_path}")

if __name__ == "__main__":
    main()
