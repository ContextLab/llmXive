"""
T041: Image Preprocessor
Resizes images to 224x224, normalizes pixel values, and handles aspect ratios/depths.
Input: data/raw/
Output: data/processed/
"""
from __future__ import annotations

import os
import logging
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import cv2
import numpy as np

# Import from local project structure
# We need to add the 'code' directory to sys.path if running as a script
# but the runner usually handles this. We'll try to import, and if it fails,
# we adjust sys.path.
try:
    from utils.logging_config import get_logger, log_operation
    from utils.config import get_data_dir, get_processed_dir, get_raw_dir
except ImportError:
    # Fallback for direct execution or path issues
    code_root = Path(__file__).parent.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    from utils.logging_config import get_logger, log_operation
    from utils.config import get_data_dir, get_processed_dir, get_raw_dir

# Constants
TARGET_SIZE = (224, 224)
TARGET_DEPTH = 3  # RGB
MIN_PIXEL_VALUE = 0.0
MAX_PIXEL_VALUE = 1.0

def setup_logging() -> Any:
    """Setup logging for the preprocess task."""
    # Use the tolerant logger
    return get_logger("preprocess", log_file="results/preprocess.log")

def resize_with_aspect_ratio(image: np.ndarray, target_size: Tuple[int, int] = TARGET_SIZE) -> np.ndarray:
    """
    Resize image to target size while maintaining aspect ratio, then pad to fill.
    Handles different input depths (1, 3, 4) by converting to 3-channel RGB.
    """
    h, w = image.shape[:2]
    target_h, target_w = target_size

    # Handle depth conversion first
    if len(image.shape) == 2 or image.shape[2] == 1:
        # Grayscale or single channel -> RGB
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    elif image.shape[2] == 4:
        # RGBA -> RGB (drop alpha)
        image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
    
    current_h, current_w = image.shape[:2]

    # Calculate scaling factor
    scale = min(target_w / current_w, target_h / current_h)
    new_w = int(current_w * scale)
    new_h = int(current_h * scale)

    # Resize
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # Create a blank canvas
    canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
    
    # Calculate padding
    pad_w = (target_w - new_w) // 2
    pad_h = (target_h - new_h) // 2

    # Paste resized image onto canvas
    canvas[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized

    return canvas

def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image pixel values to [0, 1] range.
    Assumes input is uint8 [0, 255] or float [0, 255].
    """
    if image.dtype == np.uint8:
        normalized = image.astype(np.float32) / 255.0
    elif np.issubdtype(image.dtype, np.floating):
        # Already float, check range
        if image.max() > 1.0:
            normalized = image / 255.0
        else:
            normalized = image
    else:
        # Fallback for other types
        min_val = image.min()
        max_val = image.max()
        if max_val - min_val == 0:
            normalized = np.zeros_like(image, dtype=np.float32)
        else:
            normalized = (image - min_val) / (max_val - min_val)
    
    return normalized

def preprocess_single_image(input_path: Path, output_path: Path, logger: Any) -> bool:
    """
    Preprocess a single image: resize and normalize.
    Returns True if successful, False otherwise.
    """
    try:
        # Read image
        image = cv2.imread(str(input_path))
        if image is None:
            logger.error(f"Failed to read image: {input_path}")
            return False

        # Resize with aspect ratio handling
        resized = resize_with_aspect_ratio(image)

        # Normalize
        normalized = normalize_image(resized)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save as PNG (lossless)
        # We save as float32 PNG? No, cv2 expects uint8. 
        # For deep learning, we usually keep as float in memory or save as float16/32 in numpy.
        # However, the task says "Output: data/processed/". 
        # Let's save as normalized float16 numpy file or re-quantize to uint8 [0, 255] for storage.
        # Standard practice for image datasets is to store as uint8.
        # But for "normalized" data often used in CNNs, storing as float16 is efficient.
        # Let's save as .npy for precision, or .png scaled back to 0-255.
        # Given the context of "images", let's save as PNG scaled to 0-255 for compatibility,
        # but the "normalized" aspect is often an in-memory transform.
        # The prompt says "normalize" in the task. If we save as PNG, we lose the exact float.
        # Let's save as .npy to preserve the float32 normalized state.
        
        # Alternative: Save as uint8 PNG (0-255) and normalize again at load time?
        # The task says "Output: data/processed/". 
        # Let's save as .npy to preserve the processed float state exactly.
        np.save(str(output_path.with_suffix('.npy')), normalized)
        
        logger.info(f"Processed: {input_path.name} -> {output_path.with_suffix('.npy').name}")
        return True

    except Exception as e:
        logger.error(f"Error processing {input_path}: {str(e)}")
        return False

def preprocess_dataset(logger: Any) -> Dict[str, Any]:
    """
    Iterate through data/raw/ and preprocess all images to data/processed/.
    Returns statistics.
    """
    raw_dir = get_raw_dir()
    processed_dir = get_processed_dir()
    
    if not raw_dir.exists():
        logger.error(f"Raw directory not found: {raw_dir}")
        return {"success": False, "error": "Raw directory not found"}

    processed_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "files": []
    }

    # Walk through raw directory
    for root, _, files in os.walk(raw_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                input_path = Path(root) / file
                # Preserve relative structure
                rel_path = input_path.relative_to(raw_dir)
                output_path = processed_dir / rel_path
                
                stats["total"] += 1
                if preprocess_single_image(input_path, output_path, logger):
                    stats["success"] += 1
                else:
                    stats["failed"] += 1
                    stats["files"].append({"file": str(input_path), "status": "failed"})

    return stats

def save_manifest(stats: Dict[str, Any], output_path: Path) -> None:
    """Save processing manifest as JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)

def main() -> None:
    """Main entry point."""
    logger = setup_logging()
    logger.info("Starting preprocessing pipeline")
    
    try:
        stats = preprocess_dataset(logger)
        manifest_path = get_processed_dir() / "preprocess_manifest.json"
        save_manifest(stats, manifest_path)
        
        logger.info(f"Preprocessing complete. Success: {stats['success']}, Failed: {stats['failed']}")
        
        if stats['failed'] > 0:
            sys.exit(1)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()