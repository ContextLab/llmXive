import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional, Any, Callable, Union, List, Dict
import random
import sys

logger = logging.getLogger(__name__)

def setup_logging(log_level: Union[str, int, None] = "INFO", name: Optional[str] = None) -> logging.Logger:
    """
    Initialize the logging infrastructure.
    Accepts various forms of log_level (string, int, None) and optional name.
    """
    # Determine the level
    if log_level is None:
        level = logging.INFO
    elif isinstance(log_level, str):
        level = getattr(logging, log_level.upper(), logging.INFO)
    elif isinstance(log_level, int):
        level = log_level
    else:
        level = logging.INFO

    # Configure if not already configured
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)
    else:
        # Update level if handlers exist
        root_logger.setLevel(level)

    # Return specific logger or root
    if name:
        return logging.getLogger(name)
    return root_logger

def pin_random_seed(seed: int) -> None:
    """
    Pin random seeds for numpy, scipy, and standard random module for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    # scipy does not have a global seed setter, but uses numpy's
    # If using specific scipy stats functions that take random_state, pass np.random.RandomState(seed)
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
    except FileNotFoundError:
        logger.error(f"File not found: {filepath}")
        return ""
    except Exception as e:
        logger.error(f"Error computing checksum for {filepath}: {e}")
        return ""

def main():
    """Test utilities."""
    logger = setup_logging("DEBUG")
    logger.info("Utils module loaded and tested.")

if __name__ == "__main__":
    main()