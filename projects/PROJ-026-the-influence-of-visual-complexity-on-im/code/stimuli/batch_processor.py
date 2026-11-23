"""
Batch processing utilities for stimuli.
"""
import os
import logging
import numpy as np
import cv2
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from stimuli.metrics import process_image_vectorized
from utils.logging import get_logger

logger: logging.Logger = get_logger(__name__)

def load_images_batch(image_dir: str | Path) -> List[Path]:
    """
    Load a list of image paths from a directory.

    Args:
        image_dir: Directory containing images.

    Returns:
        List[Path]: List of valid image file paths.
    """
    dir_path = Path(image_dir)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
    image_files: List[Path] = []

    for file_path in dir_path.iterdir():
        if file_path.suffix.lower() in valid_extensions:
            image_files.append(file_path)

    logger.info(f"Found {len(image_files)} images in {dir_path}")
    return image_files

def process_stimuli_vectorized(image_paths: List[str | Path], output_csv: str | Path) -> None:
    """
    Process a batch of images and save metrics to a CSV file.

    Args:
        image_paths: List of image file paths.
        output_csv: Path to the output CSV file.
    """
    import pandas as pd

    results: List[Dict[str, float | str]] = []
    failed_count = 0

    for img_path in image_paths:
        try:
            logger.info(f"Processing {img_path}")
            edge_density, entropy_val, fractal_dim = process_image_vectorized(img_path)
            results.append({
                "filename": Path(img_path).name,
                "edge_density": edge_density,
                "entropy": entropy_val,
                "fractal_dim": fractal_dim
            })
        except Exception as e:
            logger.error(f"Failed to process {img_path}: {e}")
            failed_count += 1
            # Append with NaN for failed metrics to maintain row structure if needed, 
            # or skip. Here we skip to keep CSV clean, but log the error.
            continue

    if not results:
        logger.warning("No images were successfully processed.")
        # Create empty CSV with headers
        df = pd.DataFrame(columns=["filename", "edge_density", "entropy", "fractal_dim"])
    else:
        df = pd.DataFrame(results)

    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metrics for {len(results)} images to {output_csv}")
