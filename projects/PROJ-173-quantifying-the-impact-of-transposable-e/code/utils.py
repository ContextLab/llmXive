import hashlib
import logging
import os
import random
import sys
from datetime import datetime
from typing import Optional

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Sets up a logger with optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if specified
        if log_file:
            ensure_directory(log_file)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)

    return logger

def compute_file_checksum(filepath: str, algorithm: str = 'md5') -> str:
    """Computes the checksum of a file."""
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def set_random_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)

def ensure_directory(filepath: str) -> None:
    """Ensures the directory for a given file path exists."""
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

def get_timestamp_string() -> str:
    """Returns a timestamp string suitable for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")
