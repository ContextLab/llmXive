import logging
import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Optional
from PIL import Image, ExifTags

# Global seed state
_global_seed = None

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with a specific format.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    return logger

def log_structured_error(error_type: str, message: str, details: Optional[dict] = None):
    """
    Logs a specific error with structured JSON message as per Edge Cases in spec.md.
    """
    logger = get_logger(__name__)
    error_data = {
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    logger.error(json.dumps(error_data))

def compute_file_checksum(filepath: str) -> str:
    """
    Computes SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        log_structured_error("file_not_found", f"Checksum failed: {filepath}")
        raise

def init_seed_config(seed: int):
    """
    Initializes the global random seed configuration.
    """
    global _global_seed
    _global_seed = seed
    logging.info(f"Global seed initialized to {seed}")

def set_random_seed(seed: int):
    """
    Sets the random seed for numpy and random modules.
    """
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)

def get_global_seed() -> int:
    """
    Returns the global seed if set, otherwise defaults to 42.
    """
    global _global_seed
    if _global_seed is None:
        return 42
    return _global_seed

def sanitize_image_pii(image_dir: str) -> int:
    """
    Implements PII Sanitization (Task T016):
    1. Renames all images in `image_dir` to `img_<sha256_hash>.jpg`.
    2. Strips all EXIF data from images using Pillow.
    3. Logs the count of sanitized images.
    
    Args:
        image_dir (str): Path to the directory containing images.
        
    Returns:
        int: Number of images successfully sanitized.
    """
    logger = get_logger(__name__)
    sanitized_count = 0
    
    if not os.path.exists(image_dir):
        log_structured_error("image_processing_failures", f"Directory not found: {image_dir}")
        return 0

    files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff'))]
    
    if not files:
        logger.warning(f"No image files found in {image_dir}")
        return 0

    for filename in files:
        old_path = os.path.join(image_dir, filename)
        
        # Compute SHA256 of the file content
        try:
            file_hash = compute_file_checksum(old_path)
        except Exception as e:
            log_structured_error("image_processing_failures", f"Failed to compute checksum for {filename}", {"error": str(e)})
            continue
        
        new_filename = f"img_{file_hash}.jpg"
        new_path = os.path.join(image_dir, new_filename)
        
        # Skip if already sanitized (hash matches filename pattern)
        if filename.startswith("img_") and filename.endswith(".jpg") and len(filename) == 40: # 8 (img_) + 32 (hash) + 4 (.jpg)
            # Verify it's actually the hash of itself to avoid double processing
            try:
                current_hash = compute_file_checksum(old_path)
                if filename == f"img_{current_hash}.jpg":
                    logger.debug(f"Skipping already sanitized image: {filename}")
                    continue
            except:
                pass

        try:
            # Open image and strip EXIF
            with Image.open(old_path) as img:
                # Convert to RGB if necessary (e.g., for PNGs with alpha or CMYK JPEGs)
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')
                elif img.mode == 'CMYK':
                    img = img.convert('RGB')
                
                # Save without EXIF data
                # Explicitly setting exif=None ensures no metadata is copied
                img.save(new_path, "JPEG", exif=None, quality=95)
            
            # Remove the old file
            os.remove(old_path)
            
            # If the new name is different from the old name (and not just a rename to hash), remove old
            # Note: We already removed old_path above. If new_path == old_path, we have a problem, 
            # but the logic above prevents that unless the hash happens to match the filename exactly.
            
            sanitized_count += 1
            logger.info(f"Sanitized and renamed: {filename} -> {new_filename}")
            
        except Exception as e:
            log_structured_error("image_processing_failures", f"Failed to sanitize image {filename}", {"error": str(e)})
            continue

    logger.info(f"PII Sanitization complete. {sanitized_count} images processed.")
    return sanitized_count
