"""
Image preprocessing pipeline for material strength prediction.

This module handles:
- Resizing images to 224x224 while handling aspect ratios
- Normalizing pixel values using ImageNet statistics
- Converting grayscale to RGB where necessary
- Processing entire datasets and saving results
"""

import os
import logging
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import cv2
import numpy as np

from utils.config import get_processed_dir, get_raw_dir, get_data_dir, set_seed, get_seed


def setup_logging() -> logging.Logger:
    """Initialize and return a logger for the preprocessing module."""
    logger = logging.getLogger("preprocess")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def resize_with_aspect_ratio(
    image: np.ndarray,
    target_size: Tuple[int, int] = (224, 224),
    padding_color: Tuple[int, int, int] = (128, 128, 128)
) -> np.ndarray:
    """
    Resize an image to target_size while preserving aspect ratio.
    The image is centered and padded with gray if aspect ratios differ.

    Args:
        image: Input image as numpy array (H, W, C) or (H, W)
        target_size: Target (height, width)
        padding_color: Color for padding (BGR order for OpenCV)

    Returns:
        Resized and padded image of shape (target_height, target_width, 3)
    """
    if image.ndim == 2:
        # Grayscale to RGB
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.ndim == 3 and image.shape[2] == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.ndim == 3 and image.shape[2] == 4:
        # Remove alpha channel
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    h, w = image.shape[:2]
    target_h, target_w = target_size

    # Calculate scaling factor to fit within target while preserving aspect
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    # Resize
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Create padded canvas
    padded = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    padded[:, :] = padding_color

    # Calculate center position
    y_offset = (target_h - new_h) // 2
    x_offset = (target_w - new_w) // 2

    # Place resized image in center
    padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized

    return padded


def normalize_image(
    image: np.ndarray,
    mean: Tuple[float, float, float] = (0.485, 0.456, 0.406),
    std: Tuple[float, float, float] = (0.229, 0.224, 0.225)
) -> np.ndarray:
    """
    Normalize image pixel values using ImageNet statistics.

    Args:
        image: Input image (H, W, C) in uint8 range [0, 255]
        mean: Mean values for R, G, B channels
        std: Standard deviation values for R, G, B channels

    Returns:
        Normalized image as float32 array with values roughly in [-2, 2]
    """
    if image.dtype != np.float32:
        image = image.astype(np.float32)

    # Normalize to [0, 1]
    image = image / 255.0

    # Apply channel-wise normalization
    mean = np.array(mean, dtype=np.float32)
    std = np.array(std, dtype=np.float32)

    # Ensure mean and std are broadcastable
    normalized = (image - mean) / std

    return normalized


def preprocess_single_image(
    input_path: Path,
    output_path: Path,
    target_size: Tuple[int, int] = (224, 224),
    normalize: bool = True,
    save_as: str = "png"
) -> Dict[str, any]:
    """
    Preprocess a single image: resize, optionally normalize, and save.

    Args:
        input_path: Path to input image
        output_path: Path to save processed image
        target_size: Target dimensions (height, width)
        normalize: Whether to apply normalization
        save_as: Output format ('png' or 'npy')

    Returns:
        Dictionary with processing metadata
    """
    # Read image
    image = cv2.imread(str(input_path))
    if image is None:
        raise ValueError(f"Failed to read image: {input_path}")

    # Resize with aspect ratio preservation
    processed = resize_with_aspect_ratio(image, target_size)

    # Normalize if requested
    if normalize:
        processed = normalize_image(processed)
        # For saving, we need to convert back to uint8 for PNG
        # But we'll save as .npy for normalized data
        if save_as == "png":
            # Invert normalization roughly for visualization
            # mean: 0.485, 0.456, 0.406; std: 0.229, 0.224, 0.225
            # To get back to [0, 255]: (x * std + mean) * 255
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            processed_uint8 = np.clip((processed * std + mean) * 255, 0, 255).astype(np.uint8)
            cv2.imwrite(str(output_path), processed_uint8)
        else:
            # Save as .npy for normalized float values
            output_path = output_path.with_suffix('.npy')
            np.save(str(output_path), processed)
    else:
        # Save uint8 image directly
        cv2.imwrite(str(output_path), processed)

    return {
        "input_path": str(input_path),
        "output_path": str(output_path),
        "original_shape": image.shape,
        "processed_shape": processed.shape,
        "normalized": normalize
    }


def preprocess_dataset(
    raw_dir: Optional[Path] = None,
    processed_dir: Optional[Path] = None,
    manifest_path: Optional[Path] = None,
    target_size: Tuple[int, int] = (224, 224),
    normalize: bool = True,
    logger: Optional[logging.Logger] = None
) -> Dict[str, List[Dict]]:
    """
    Preprocess all images in a dataset.

    Args:
        raw_dir: Directory containing raw images
        processed_dir: Directory to save processed images
        manifest_path: Optional path to a manifest CSV/JSON listing images
        target_size: Target dimensions
        normalize: Whether to normalize
        logger: Logger instance

    Returns:
        Dictionary with 'processed' and 'failed' lists containing metadata
    """
    if logger is None:
        logger = setup_logging()

    if raw_dir is None:
        raw_dir = get_raw_dir()
    if processed_dir is None:
        processed_dir = get_processed_dir()

    processed_dir.mkdir(parents=True, exist_ok=True)

    # Determine input images
    images_to_process = []
    if manifest_path and manifest_path.exists():
        # Load from manifest
        if manifest_path.suffix == '.json':
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            images_to_process = manifest.get('images', [])
        elif manifest_path.suffix == '.csv':
            import csv
            with open(manifest_path, 'r') as f:
                reader = csv.DictReader(f)
                images_to_process = [row['image_path'] for row in reader]
    else:
        # Scan directory
        raw_dir = Path(raw_dir)
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.tif', '*.tiff']:
            images_to_process.extend(raw_dir.glob(ext))

    results = {"processed": [], "failed": []}

    for img_path in images_to_process:
        img_path = Path(img_path)
        if not img_path.exists():
            logger.warning(f"Image not found: {img_path}")
            results["failed"].append({"path": str(img_path), "error": "File not found"})
            continue

        try:
            # Create output path
            output_filename = img_path.stem + "_processed.png"
            output_path = processed_dir / output_filename

            # Preprocess
            metadata = preprocess_single_image(
                img_path,
                output_path,
                target_size=target_size,
                normalize=normalize,
                save_as="png"
            )
            results["processed"].append(metadata)
            logger.info(f"Processed: {img_path.name} -> {output_path.name}")

        except Exception as e:
            logger.error(f"Failed to process {img_path}: {str(e)}")
            results["failed"].append({"path": str(img_path), "error": str(e)})

    # Save processing report
    report_path = processed_dir / "preprocessing_report.json"
    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Preprocessing complete. Success: {len(results['processed'])}, Failed: {len(results['failed'])}")
    logger.info(f"Report saved to: {report_path}")

    return results


def main():
    """Main entry point for the preprocessing script."""
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess material microstructure images")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Directory containing raw images (default: data/raw)"
    )
    parser.add_argument(
        "--processed-dir",
        type=str,
        default=None,
        help="Directory to save processed images (default: data/processed)"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Path to manifest file listing images"
    )
    parser.add_argument(
        "--no-normalize",
        action="store_true",
        help="Disable normalization"
    )
    parser.add_argument(
        "--target-size",
        type=int,
        nargs=2,
        default=[224, 224],
        help="Target size (height width)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()

    # Set seed
    set_seed(args.seed)

    # Setup logging
    logger = setup_logging()
    logger.info("Starting image preprocessing pipeline")
    logger.info(f"Target size: {args.target_size}")
    logger.info(f"Normalization: {not args.no_normalize}")

    # Convert paths
    raw_dir = Path(args.raw_dir) if args.raw_dir else None
    processed_dir = Path(args.processed_dir) if args.processed_dir else None
    manifest_path = Path(args.manifest) if args.manifest else None

    # Run preprocessing
    results = preprocess_dataset(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        manifest_path=manifest_path,
        target_size=tuple(args.target_size),
        normalize=not args.no_normalize,
        logger=logger
    )

    # Exit with error if any failures
    if results["failed"]:
        logger.error(f"Failed to process {len(results['failed'])} images")
        sys.exit(1)

    logger.info("Preprocessing completed successfully")
    sys.exit(0)


if __name__ == "__main__":
    import sys
    main()