import os
import logging
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from ..config import get_project_root
from ..utils.logging import get_logger

logger = get_logger(__name__)

def load_images_batch(directory: Path, max_images: Optional[int] = None) -> List[np.ndarray]:
    """
    Load a batch of images from a directory.
    
    Args:
        directory: Path to the directory containing images
        max_images: Maximum number of images to load (None for all)
        
    Returns:
        List of loaded images as numpy arrays
    """
    images = []
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
    
    image_files = []
    for ext in image_extensions:
        image_files.extend(directory.glob(f'*{ext}'))
        image_files.extend(directory.glob(f'*{ext.upper()}'))
    
    if max_images:
        image_files = image_files[:max_images]
    
    for img_path in image_files:
        img = cv2.imread(str(img_path))
        if img is not None:
            images.append(img)
            logger.debug(f"Loaded image: {img_path.name}")
        else:
            logger.warning(f"Failed to load image: {img_path.name}")
    
    logger.info(f"Loaded {len(images)} images from {directory}")
    return images

def process_stimuli_vectorized(images: List[np.ndarray]) -> List[Dict]:
    """
    Process a batch of images and return complexity metrics.
    
    Args:
        images: List of images as numpy arrays
        
    Returns:
        List of dictionaries containing complexity metrics
    """
    results = []
    
    for img in images:
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate edge density
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        
        # Calculate entropy
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
        hist = hist.flatten()
        prob = hist / np.sum(hist)
        prob = prob[prob > 0]
        image_entropy = np.sum(-prob * np.log2(prob))
        
        results.append({
            'edge_density': edge_density,
            'entropy': image_entropy
        })
    
    return results

def main():
    """Main entry point for batch processor."""
    root = get_project_root()
    stimuli_dir = root / "data" / "raw" / "stimuli"
    
    if not stimuli_dir.exists():
        logger.error(f"Stimuli directory not found: {stimuli_dir}")
        return
    
    images = load_images_batch(stimuli_dir)
    if not images:
        logger.warning("No images found to process")
        return
    
    results = process_stimuli_vectorized(images)
    logger.info(f"Processed {len(results)} images")
    
    # Output results
    for i, result in enumerate(results):
        logger.info(f"Image {i}: Edge Density = {result['edge_density']:.4f}, Entropy = {result['entropy']:.4f}")

if __name__ == "__main__":
    main()
