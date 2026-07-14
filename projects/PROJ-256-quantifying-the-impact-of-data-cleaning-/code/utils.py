import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional, Any, Callable, Union, List, Dict
import random
import logging

logger = logging.getLogger(__name__)

def setup_logging(log_level: Union[str, int, None] = None, name: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    Accepts various call signatures for flexibility:
    - setup_logging() -> uses default INFO
    - setup_logging("INFO") -> string level
    - setup_logging(log_level="INFO") -> kwarg
    - setup_logging(logging.INFO) -> int level
    - setup_logging(logging.INFO, "name") -> name arg (ignored if passed)
    - setup_logging(name="my_logger") -> name kwarg
    """
    # Determine log level
    level = logging.INFO
    
    if log_level is not None:
        if isinstance(log_level, str):
            level = getattr(logging, log_level.upper(), logging.INFO)
        elif isinstance(log_level, int):
            level = log_level
    
    # Configure logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Get logger
    if name:
        logger = logging.getLogger(name)
    else:
        logger = logging.getLogger('llmXive')
    
    # Ensure level is set
    logger.setLevel(level)
    
    return logger

def pin_random_seed(seed: int = 42):
    """Pin random seed for numpy, scipy, and python random for reproducibility."""
    np.random.seed(seed)
    random.seed(seed)
    # scipy uses numpy's random state, so no separate seeding needed
    logger.info(f"Random seed pinned to {seed} for reproducibility")

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
    """Main entry point for utils module."""
    logger = setup_logging("DEBUG")
    logger.info("Utils module loaded")
    
    # Test checksum
    test_file = "data/raw/test.csv"
    if os.path.exists(test_file):
        checksum = compute_file_checksum(test_file)
        logger.info(f"Checksum for {test_file}: {checksum}")

if __name__ == "__main__":
    main()
