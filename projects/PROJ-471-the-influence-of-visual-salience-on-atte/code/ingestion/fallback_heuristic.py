"""
Fallback Heuristic for Salience Map Generation.

Implements Graph-Based Visual Saliency (GBVS) as a fallback mechanism
when DeepGaze II fails. This module ensures the pipeline can continue
processing even if the primary deep learning model encounters errors.

Dependencies:
    - opencv-python
    - numpy
    - scipy (for normalization)

Output:
    - .npy file containing the salience map (2D float array)

Error Handling:
    - If GBVS fails for any reason, raises a RuntimeError to trigger
      image exclusion from the pipeline.
"""

import os
import sys
import logging
import numpy as np
from pathlib import Path
from typing import Optional

# Attempt to import cv2 and scipy
try:
    import cv2
except ImportError:
    raise ImportError(
        "OpenCV (opencv-python) is required for GBVS fallback. "
        "Please install it via: pip install opencv-python"
    )

try:
    from scipy.ndimage import gaussian_filter
except ImportError:
    raise ImportError(
        "SciPy is required for GBVS normalization. "
        "Please install it via: pip install scipy"
    )

from config import get_paths, load_config
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_activation_map(image: np.ndarray) -> np.ndarray:
    """
    Computes the activation map based on color and intensity channels.
    
    Args:
        image: Input image in BGR format (uint8).
    
    Returns:
        Normalized activation map (float32).
    """
    # Convert to HSV for color features
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Extract channels: Hue, Saturation, Value
    h = hsv[:, :, 0].astype(np.float32)
    s = hsv[:, :, 1].astype(np.float32)
    v = hsv[:, :, 2].astype(np.float32)
    
    # Compute activation based on saturation and value (intensity)
    # GBVS typically uses contrast in color and intensity
    # Here we use a simplified heuristic: high saturation and high intensity
    activation = (s * v) / 255.0
    
    return activation

def compute_contrast_map(image: np.ndarray) -> np.ndarray:
    """
    Computes the contrast map using a simple difference of Gaussians approximation.
    
    Args:
        image: Input image in BGR format (uint8).
    
    Returns:
        Contrast map (float32).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Apply Gaussian blur to get the "surround"
    surround = gaussian_filter(gray, sigma=2)
    
    # Difference of Gaussians approximation
    contrast = gray - surround
    
    # Normalize to [0, 1]
    if np.max(contrast) > np.min(contrast):
        contrast = (contrast - np.min(contrast)) / (np.max(contrast) - np.min(contrast))
    else:
        contrast = np.zeros_like(gray)
        
    return contrast

def run_gvs(image_path: str, output_path: Optional[str] = None) -> np.ndarray:
    """
    Runs the Graph-Based Visual Saliency (GBVS) heuristic.
    
    This function computes a salience map based on color and intensity contrast.
    It serves as a fallback when DeepGaze II fails.
    
    Args:
        image_path: Path to the input image.
        output_path: Optional path to save the .npy salience map.
    
    Returns:
        Salience map as a numpy array (float32).
    
    Raises:
        RuntimeError: If the image cannot be loaded or processed.
    """
    logger.info(f"Running GBVS fallback for image: {image_path}")
    
    # Load image
    if not os.path.exists(image_path):
        raise RuntimeError(f"Image not found: {image_path}")
    
    image = cv2.imread(image_path)
    if image is None:
        raise RuntimeError(f"Failed to load image with OpenCV: {image_path}")
    
    try:
        # Compute activation and contrast maps
        activation = compute_activation_map(image)
        contrast = compute_contrast_map(image)
        
        # Combine maps (simple weighted average)
        # In a full GBVS implementation, this would involve graph construction
        # and Markov chain equilibrium, but for a robust fallback, we use
        # a normalized sum of contrast and activation.
        salience_map = (activation + contrast) / 2.0
        
        # Normalize final map to [0, 1]
        if np.max(salience_map) > np.min(salience_map):
            salience_map = (salience_map - np.min(salience_map)) / (np.max(salience_map) - np.min(salience_map))
        else:
            salience_map = np.zeros_like(salience_map)
        
        # Ensure output is float32
        salience_map = salience_map.astype(np.float32)
        
        # Save if output path provided
        if output_path:
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            np.save(output_path, salience_map)
            logger.info(f"GBVS salience map saved to: {output_path}")
        
        return salience_map
        
    except Exception as e:
        logger.error(f"GBVS processing failed for {image_path}: {str(e)}")
        raise RuntimeError(f"GBVS fallback failed for {image_path}: {str(e)}")

def main():
    """
    Main entry point for running GBVS on a single image from command line.
    
    Usage:
        python -m code.ingestion.fallback_heuristic <image_path> [output_path]
    """
    if len(sys.argv) < 2:
        print("Usage: python -m code.ingestion.fallback_heuristic <image_path> [output_path]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        salience_map = run_gvs(image_path, output_path)
        print(f"Success. Salience map shape: {salience_map.shape}")
    except RuntimeError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()