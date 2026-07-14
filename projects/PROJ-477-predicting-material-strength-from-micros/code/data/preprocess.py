"""
Image Preprocessing Module for Material Strength Prediction.

This module handles the preprocessing of EBSD microstructure images:
- Resizing to 224x224 (preserving aspect ratio with padding)
- Normalization (ImageNet statistics)
- Handling various input depths (grayscale, RGB)
- Saving processed images to the 'processed' directory
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

import cv2
import numpy as np
import torch
from torchvision import transforms

from utils.config import get_project_root, get_raw_dir, get_processed_dir
from utils.logging_config import get_logger

# Constants
TARGET_SIZE = 224
logger = get_logger(__name__)

# ImageNet normalization statistics
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def resize_with_aspect_ratio(
    image: np.ndarray,
    target_size: int = TARGET_SIZE
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Resize image to target_size x target_size while preserving aspect ratio.
    Pads with black pixels to fill the square.

    Args:
        image: Input image (H, W) or (H, W, C)
        target_size: Desired output dimension (square)

    Returns:
        Tuple of (padded_resized_image, (original_width, original_height))
    """
    original_height, original_width = image.shape[:2]
    aspect_ratio = original_width / original_height

    # Calculate new dimensions
    if aspect_ratio > 1:
        # Wider than tall
        new_width = target_size
        new_height = int(target_size / aspect_ratio)
    else:
        # Taller than wide
        new_height = target_size
        new_width = int(target_size * aspect_ratio)

    # Resize
    resized = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=cv2.INTER_AREA
    )

    # Create padding
    pad_h = (target_size - new_height) // 2
    pad_w = (target_size - new_width) // 2

    if len(image.shape) == 2:
        # Grayscale
        padded = cv2.copyMakeBorder(
            resized,
            pad_h,
            target_size - new_height - pad_h,
            pad_w,
            target_size - new_width - pad_w,
            cv2.BORDER_CONSTANT,
            value=0
        )
    else:
        # Color
        padded = cv2.copyMakeBorder(
            resized,
            pad_h,
            target_size - new_height - pad_h,
            pad_w,
            target_size - new_width - pad_w,
            cv2.BORDER_CONSTANT,
            value=[0, 0, 0]
        )

    return padded, (original_width, original_height)

def normalize_image(image: np.ndarray) -> torch.Tensor:
    """
    Convert image to tensor and normalize using ImageNet statistics.

    Args:
        image: Input image (H, W, C) in range [0, 255]

    Returns:
        Normalized tensor (C, H, W)
    """
    # Convert to float and normalize to [0, 1]
    img_float = image.astype(np.float32) / 255.0

    # Ensure 3 channels
    if len(img_float.shape) == 2:
        img_float = np.stack([img_float] * 3, axis=-1)

    # Convert to tensor (H, W, C) -> (C, H, W)
    tensor = torch.from_numpy(img_float).permute(2, 0, 1)

    # Normalize
    transform = transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD)
    normalized = transform(tensor)

    return normalized

def preprocess_single_image(
    input_path: Path,
    output_path: Path
) -> Dict:
    """
    Preprocess a single image: resize, normalize, and save.

    Args:
        input_path: Path to input image
        output_path: Path to save processed image

    Returns:
        Dictionary with processing metadata
    """
    # Read image
    image = cv2.imread(str(input_path))
    if image is None:
        raise ValueError(f"Failed to read image: {input_path}")

    # Handle BGR to RGB conversion if needed
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Resize with aspect ratio
    resized_image, original_size = resize_with_aspect_ratio(image, TARGET_SIZE)

    # Normalize and convert to tensor
    tensor = normalize_image(resized_image)

    # Save processed image (convert back to numpy for saving)
    # We save the normalized, resized version as a numpy array for inspection
    # Convert tensor back to numpy for saving (denormalize for visualization)
    # Note: We save the resized version, not the normalized tensor, for visual inspection
    save_image = resized_image
    if len(save_image.shape) == 2:
        save_image = np.stack([save_image] * 3, axis=-1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save as PNG
    cv2.imwrite(str(output_path), cv2.cvtColor(save_image, cv2.COLOR_RGB2BGR))

    return {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "original_size": original_size,
        "target_size": (TARGET_SIZE, TARGET_SIZE),
        "success": True
    }

def preprocess_dataset(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    image_extensions: List[str] = None
) -> Dict:
    """
    Preprocess all images in the raw directory.

    Args:
        raw_dir: Directory containing raw images (default: from config)
        processed_dir: Directory to save processed images (default: from config)
        image_extensions: List of valid image extensions

    Returns:
        Summary statistics of the preprocessing run
    """
    if raw_dir is None:
        raw_dir = get_raw_dir()
    if processed_dir is None:
        processed_dir = get_processed_dir()
    if image_extensions is None:
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']

    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Find all images
    image_files = []
    for ext in image_extensions:
        image_files.extend(raw_dir.glob(f"*{ext}"))
        image_files.extend(raw_dir.glob(f"*{ext.upper()}"))

    # Remove duplicates and sort
    image_files = sorted(list(set(image_files)))

    logger.info(f"Found {len(image_files)} images to preprocess")

    results = []
    failed = []

    for img_path in image_files:
        try:
            # Generate output path
            output_filename = f"processed_{img_path.name}"
            output_path = processed_dir / output_filename

            result = preprocess_single_image(img_path, output_path)
            results.append(result)
            logger.debug(f"Processed: {img_path.name}")

        except Exception as e:
            logger.error(f"Failed to process {img_path}: {str(e)}")
            failed.append({"path": str(img_path), "error": str(e)})

    summary = {
        "total_images": len(image_files),
        "processed_count": len(results),
        "failed_count": len(failed),
        "target_size": TARGET_SIZE,
        "normalization": "ImageNet",
        "results": results,
        "failures": failed
    }

    # Save summary report
    summary_path = processed_dir / "preprocessing_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Preprocessing complete: {len(results)}/{len(image_files)} successful")
    logger.info(f"Summary saved to: {summary_path}")

    return summary

def main():
    """Main entry point for preprocessing."""
    logger.info("Starting image preprocessing pipeline")

    try:
        summary = preprocess_dataset()

        if summary["failed_count"] > 0:
            logger.warning(f"Failed to process {summary['failed_count']} images")
            return 1

        logger.info("Preprocessing completed successfully")
        return 0

    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())