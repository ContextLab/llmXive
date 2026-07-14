import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional

logger = logging.getLogger(__name__)

def pin_random_seed(seed: int) -> None:
    """
    Pin random seeds for numpy and scipy to ensure reproducibility.
    """
    np.random.seed(seed)
    # scipy uses numpy's random state, so setting numpy's seed is sufficient
    logger.debug(f"Random seed pinned to {seed}")

def compute_file_checksum(filepath: str) -> str:
    """
    Compute SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {filepath}: {e}")
        return ""

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Setup logging infrastructure.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def main():
    pass
