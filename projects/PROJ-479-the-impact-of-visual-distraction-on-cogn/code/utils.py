import logging
import os
import sys
import hashlib
import json
from datetime import datetime
from PIL import Image
from io import BytesIO

# Global seed state
_seed_config = {
    "seed": 42,
    "initialized": False
}

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_structured_error(error_type: str, message: str, details: dict = None):
    """Log specific errors as structured JSON."""
    logger = get_logger(__name__)
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "message": message,
        "details": details or {}
    }
    logger.error(json.dumps(log_entry))

def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def init_seed_config(seed: int = 42):
    """Initialize global random seed."""
    _seed_config["seed"] = seed
    _seed_config["initialized"] = True

def set_random_seed(seed: int = None):
    """Set random seed for reproducibility."""
    import random
    import numpy as np
    if seed is None:
        seed = _seed_config["seed"]
    random.seed(seed)
    np.random.seed(seed)

def get_global_seed() -> int:
    """Get the current global seed."""
    return _seed_config["seed"]

def sanitize_image_pii(image_path: str, output_path: str = None) -> str:
    """
    Sanitize image PII by stripping EXIF data and renaming.
    Returns the new sanitized file path.
    """
    logger = get_logger(__name__)
    
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return None
        
    try:
        with Image.open(image_path) as img:
            # Extract basic info
            info = img.info
            mode = img.mode
            size = img.size
            
            # Create new image without EXIF
            new_img = Image.new(mode, size)
            new_img.putdata(list(img.getdata()))
            
            # Generate sanitized name
            base_name = os.path.basename(image_path)
            file_ext = os.path.splitext(base_name)[1]
            file_hash = hashlib.sha256(base_name.encode()).hexdigest()[:16]
            sanitized_name = f"img_{file_hash}{file_ext}"
            
            if output_path is None:
                output_dir = os.path.dirname(image_path)
                output_path = os.path.join(output_dir, sanitized_name)
            else:
                # Ensure output path has correct extension if needed
                if not output_path.endswith(file_ext):
                    output_path += file_ext
                
            # Save without EXIF
            new_img.save(output_path, format=img.format)
            
            logger.info(f"Sanitized image: {image_path} -> {output_path}")
            return output_path
            
    except Exception as e:
        logger.error(f"Failed to sanitize image {image_path}: {e}")
        return None
