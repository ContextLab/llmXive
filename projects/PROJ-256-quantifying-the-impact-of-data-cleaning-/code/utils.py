"""
Utility functions for the project.
Includes logging setup, random seed pinning, and file checksums.
"""
import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional, Any, Callable, Union
import sys

logger = logging.getLogger(__name__)

def setup_logging(log_level: Union[str, int, None] = None, name: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Accepts multiple signatures for flexibility:
    - setup_logging() -> uses default INFO
    - setup_logging("INFO") -> string level
    - setup_logging(log_level="INFO") -> kwarg
    - setup_logging(logging.INFO) -> int level
    - setup_logging(logging.INFO, "name") -> name arg (ignored if passed)
    - setup_logging(name="my_logger") -> name kwarg (ignored)
    
    Args:
        log_level: String ("INFO", "DEBUG", etc.) or int (logging.INFO).
        name: Optional logger name (ignored for global config, but accepted for compatibility).
    
    Returns:
        The root logger instance.
    """
    # Determine log level
    level = logging.INFO
    if log_level is not None:
        if isinstance(log_level, str):
            level = getattr(logging, log_level.upper(), logging.INFO)
        elif isinstance(log_level, int):
            level = log_level
        # else: ignore unknown types
    
    # Configure root logger if not already configured
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)
    
    # If a specific name is requested, return that logger
    if name:
        return logging.getLogger(name)
    
    return logging.getLogger()

def pin_random_seed(seed: int) -> None:
    """Pin the random seed for numpy and scipy to ensure reproducibility."""
    np.random.seed(seed)
    # Scipy uses numpy's random state, so setting numpy's seed is usually sufficient
    # For older scipy versions or specific modules, we might need more, but this covers most.

def compute_file_checksum(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def main():
    """Main entry point for testing."""
    logger = setup_logging("INFO")
    logger.info("Utils module loaded.")
    pin_random_seed(42)
    logger.info(f"Random seed pinned. Numpy version: {np.__version__}")

if __name__ == "__main__":
    main()
