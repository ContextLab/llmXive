import logging
import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Optional

# Global seed state
_global_seed = None

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a logger with a specific format.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    return logger

def log_structured_error(error_type: str, message: str, details: Optional[dict] = None):
    """
    Logs a specific error with structured JSON message as per Edge Cases in spec.md.
    """
    logger = get_logger(__name__)
    error_data = {
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }
    logger.error(json.dumps(error_data))

def compute_file_checksum(filepath: str) -> str:
    """
    Computes SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        log_structured_error("file_not_found", f"Checksum failed: {filepath}")
        raise

def init_seed_config(seed: int):
    """
    Initializes the global random seed configuration.
    """
    global _global_seed
    _global_seed = seed
    logging.info(f"Global seed initialized to {seed}")

def set_random_seed(seed: int):
    """
    Sets the random seed for numpy and random modules.
    """
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)

def get_global_seed() -> int:
    """
    Returns the global seed if set, otherwise defaults to 42.
    """
    global _global_seed
    if _global_seed is None:
        return 42
    return _global_seed
