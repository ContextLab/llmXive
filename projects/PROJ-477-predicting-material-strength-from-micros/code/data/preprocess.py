"""
Image Preprocessing Pipeline for Microstructure Analysis.

This module handles the preprocessing of raw microstructure images:
1. Loading images from data/raw/
2. Resizing to 224x224 while handling aspect ratios (center crop + resize or pad)
3. Normalizing pixel values to [0, 1]
4. Saving processed images to data/processed/
5. Generating a manifest mapping processed images to original metadata
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np
import sys

# Import project utilities
from utils.config import get_project_root, get_data_dir, get_raw_dir, get_processed_dir, get_results_dir
from utils.logging_config import get_logger

# Constants
TARGET_WIDTH = 224
TARGET_HEIGHT = 224
SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}

def setup_logging() -> logging.Logger:
    """Initialize the logger for the preprocessing module."""
    return get_logger("preprocess", log_file="results/preprocess.log")

def resize_with_aspect_ratio(image: np.ndarray, target_width: int = TARGET_WIDTH, target_height: int = TARGET_HEIGHT) -> np.ndarray:
    """
    Resize an image to the target dimensions while preserving aspect ratio.

    Strategy:
    1. Calculate the scaling factor to fit the image within the target box.
    2. Resize the image using that factor.
    3. Create a black canvas of the target size.
    4. Center the resized image on the canvas.

    Args:
        image: Input image (H, W, C) or (H, W).
        target_width: Desired width.
        target_height: Desired height.

    Returns:
        Resized and padded image of shape (target_height, target_width, C).
    """
    h, w = image.shape[:2]
    scale = min(target_width / w, target_height / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # Resize
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # Create canvas
    if len(image.shape) == 2:
        canvas = np.zeros((target_height, target_width), dtype=image.dtype)
    else:
        canvas = np.zeros((target_height, target_width, image.shape[2]), dtype=image.dtype)

    # Center crop/position
    x_offset = (target_width - new_w) // 2
    y_offset = (target_height - new_h) // 2
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return canvas

def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image pixel values to [0, 1].

    Args:
        image: Input image (H, W, C) or (H, W) with values in [0, 255].

    Returns:
        Normalized image with float values in [0, 1].
    """
    if image.dtype == np.uint8:
        return image.astype(np.float32) / 255.0
    elif image.dtype == np.float32 or image.dtype == np.float64:
        # Assume already normalized or check range
        min_val = image.min()
        max_val = image.max()
        if max_val > 1.0:
            return (image - min_val) / (max_val - min_val + 1e-8)
        return image
    else:
        # Fallback for other types
        return image.astype(np.float32) / 255.0

def preprocess_single_image(input_path: Path, output_dir: Path, logger: logging.Logger) -> Optional[Dict]:
    """
    Process a single image: load, resize, normalize, save.

    Args:
        input_path: Path to the source image.
        output_dir: Directory to save the processed image.
        logger: Logger instance.

    Returns:
        Metadata dict for the manifest, or None if processing failed.
    """
    try:
        # Read image
        image = cv2.imread(str(input_path), cv2.IMREAD_COLOR)
        if image is None:
            logger.warning(f"Failed to load image: {input_path}")
            return None

        # Handle aspect ratio and resize
        processed = resize_with_aspect_ratio(image)

        # Normalize
        processed = normalize_image(processed)

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate output filename (keep original name, ensure .png)
        stem = input_path.stem
        output_filename = f"{stem}.png"
        output_path = output_dir / output_filename

        # Save as PNG (16-bit float representation or scaled uint8)
        # For simplicity and compatibility with standard loaders, we save as uint8 scaled back to 0-255
        # or keep as float if the downstream loader handles it.
        # Standard practice for CNNs: save as uint8 0-255 or float 0-1 in npy.
        # Here we save as PNG (uint8) to keep file sizes reasonable and compatible.
        # Note: Normalization to [0,1] is for model input; storage can be lossy uint8.
        # However, to preserve precision, we might save as .npy.
        # Let's stick to PNG for visual inspection compatibility, scaling to uint8.
        if processed.max() <= 1.0:
            save_img = (processed * 255.0).astype(np.uint8)
        else:
            save_img = processed.astype(np.uint8)

        cv2.imwrite(str(output_path), save_img)

        # Calculate original size for metadata
        orig_h, orig_w = image.shape[:2]

        return {
            "original_filename": input_path.name,
            "processed_filename": output_filename,
            "original_shape": [orig_h, orig_w],
            "processed_shape": [TARGET_HEIGHT, TARGET_WIDTH],
            "status": "success"
        }

    except Exception as e:
        logger.error(f"Error processing {input_path}: {e}")
        return None

def preprocess_dataset(logger: Optional[logging.Logger] = None) -> List[Dict]:
    """
    Main entry point to process the entire dataset from data/raw/ to data/processed/.

    Returns:
        List of metadata dictionaries for the manifest.
    """
    if logger is None:
        logger = setup_logging()

    logger.info("Starting dataset preprocessing...")

    raw_dir = get_raw_dir()
    processed_dir = get_processed_dir()

    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}. Run download.py first.")

    processed_dir.mkdir(parents=True, exist_ok=True)

    manifest = []
    image_files = []

    # Collect all image files
    for ext in SUPPORTED_EXTENSIONS:
        image_files.extend(raw_dir.glob(f"*{ext}"))
        image_files.extend(raw_dir.glob(f"*{ext.upper()}"))

    if not image_files:
        logger.warning(f"No image files found in {raw_dir}")
        return manifest

    logger.info(f"Found {len(image_files)} images to process.")

    for i, img_path in enumerate(image_files):
        if i % 100 == 0:
            logger.info(f"Processed {i}/{len(image_files)} images...")

        result = preprocess_single_image(img_path, processed_dir, logger)
        if result:
            manifest.append(result)

    logger.info(f"Preprocessing complete. {len(manifest)} images processed successfully.")
    return manifest

def save_manifest(manifest: List[Dict], output_path: Path):
    """Save the processing manifest to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def main():
    """CLI entry point."""
    logger = setup_logging()
    try:
        manifest = preprocess_dataset(logger)
        if manifest:
            manifest_path = get_processed_dir() / "preprocess_manifest.json"
            save_manifest(manifest, manifest_path)
            logger.info(f"Manifest saved to {manifest_path}")
        else:
            logger.warning("No images were processed. Manifest not created.")
    except Exception as e:
        logger.critical(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()