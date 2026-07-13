import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional

logger = logging.getLogger(__name__)

def pin_random_seed(seed: int) -> None:
    """Pin random seed for numpy and scipy to ensure reproducibility."""
    np.random.seed(seed)
    # scipy uses numpy's random state, so this should cover it
    logger.debug(f"Random seed pinned to {seed}")

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {filepath}")
        return ""

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Initialize logging infrastructure."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized at level {log_level}")
    return logger

def main():
    """Main entry point for utils module."""
    setup_logging("INFO")
    pin_random_seed(42)
    checksum = compute_file_checksum("code/utils.py")
    print(f"Checksum of this file: {checksum}")

if __name__ == "__main__":
    main()
