import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional, Any, Callable, Union
import random

logger = logging.getLogger(__name__)

def setup_logging(log_level: Union[str, int, None] = None, name: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    Accepts various forms of log_level:
    - None: Uses default INFO
    - String: "INFO", "DEBUG", etc.
    - Integer: logging.INFO, etc.
    - Object with 'log_level' attribute (for compatibility)
    """
    # Handle different call signatures
    if log_level is None:
        lvl = logging.INFO
    elif isinstance(log_level, str):
        lvl = getattr(logging, log_level.upper(), logging.INFO)
    elif isinstance(log_level, int):
        lvl = log_level
    else:
        lvl = logging.INFO

    # If name is passed but not used, just ignore it to maintain compatibility
    if name:
        pass

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(lvl)

    return logger

def pin_random_seed(seed: int):
    """Pin random seed for numpy, scipy, and python random."""
    np.random.seed(seed)
    random.seed(seed)
    # scipy uses numpy random, so no separate seed needed

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    pass

if __name__ == "__main__":
    main()
