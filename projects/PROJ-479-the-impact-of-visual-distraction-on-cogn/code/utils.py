import logging
import os
import sys
import hashlib
import json
from datetime import datetime
from PIL import Image
import random
import numpy as np

# --- Logging Setup ---
def get_logger(name=__name__):
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

logger = get_logger(__name__)

# --- Structured Error Logging ---
def log_structured_error(error_type: str, details: str):
    """Log specific errors as structured JSON."""
    error_log = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "details": details
    }
    logger.error(json.dumps(error_log))

# --- Checksumming ---
def compute_file_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None

# --- Random Seed Management ---
SEED = 42

def init_seed_config():
    """Initialize global random seed."""
    random.seed(SEED)
    np.random.seed(SEED)
    logger.info(f"Random seed initialized to {SEED}")

def set_random_seed(seed: int):
    """Set global random seed."""
    global SEED
    SEED = seed
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Random seed set to {seed}")

def get_global_seed() -> int:
    """Get current global random seed."""
    return SEED

# --- PII Sanitization ---
def sanitize_image_pii(image_path: str) -> str:
    """
    Sanitize image by renaming with SHA256 hash and stripping EXIF.
    Returns the new path.
    """
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        return None

    # Compute hash
    checksum = compute_file_checksum(image_path)
    if not checksum:
        return None

    # New filename
    new_filename = f"img_{checksum}.jpg"
    new_path = os.path.join("data/processed/sanitized_images", new_filename)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(new_path), exist_ok=True)

    try:
        # Open image and strip EXIF
        img = Image.open(image_path)
        # Save without EXIF
        img.save(new_path, exif=None)
        logger.info(f"Sanitized image: {image_path} -> {new_path}")
        return new_path
    except Exception as e:
        logger.error(f"Failed to sanitize image {image_path}: {e}")
        return None
