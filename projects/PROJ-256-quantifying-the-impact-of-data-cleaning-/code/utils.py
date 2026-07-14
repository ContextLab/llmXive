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
    # Note: scipy uses numpy's random state, so setting numpy seed is sufficient
    logger.info(f"Random seed pinned to {seed}")

def compute_file_checksum(filepath: str) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        Hexadecimal checksum string.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {filepath}: {e}", exc_info=True)
        return ""


def setup_logging(log_level: str = "INFO") -> None:
    """
    Setup logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
        
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger.info(f"Logging initialized at level {log_level}")

def main():
    """Test utility functions."""
    setup_logging("INFO")
    pin_random_seed(42)
    logger.info("Utils module test passed")

if __name__ == "__main__":
    main()