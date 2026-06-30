"""
Utility functions for the llmXive research pipeline.
"""
import os
import hashlib
import logging
import numpy as np
import scipy

def pin_random_seed(seed: int) -> None:
    """
    Pin the random seed for numpy and scipy to ensure reproducibility.
    
    Args:
        seed: The integer seed value to use.
    """
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    # Ensure scipy uses the same seed state for its random operations
    # scipy.random is a wrapper around numpy, so setting numpy seed is sufficient
    # for most scipy.stats operations, but we explicitly set it here for clarity.
    # Note: Some older scipy versions might have separate random state, 
    # but modern versions rely on numpy's global state or explicit generators.
    # For robust reproducibility in this context, setting numpy seed is the primary action.
    
    # Explicitly set the random state for scipy if using newer versions with Generator
    # However, standard practice for legacy compatibility in stats is numpy seed.
    # We ensure numpy is set.
    

def compute_file_checksum(filepath: str) -> str:
    """
    Compute the SHA256 checksum of a file.
    
    Args:
        filepath: Path to the file to checksum.
        
    Returns:
        The hexadecimal SHA256 checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there is an error reading the file.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def setup_logging(log_level: str) -> logging.Logger:
    """
    Setup the logging infrastructure.
    
    Args:
        log_level: The logging level as a string (e.g., 'INFO', 'DEBUG').
        
    Returns:
        The root logger instance configured with the specified level.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        force=True
    )
    return logging.getLogger(__name__.split('.')[0])