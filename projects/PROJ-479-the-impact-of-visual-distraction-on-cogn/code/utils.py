"""
Utility functions for logging, checksumming, and seed management.
"""
import logging
import os
import sys
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any

# Global seed state
_GLOBAL_SEED = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Configure and return a logger with JSON-formatted handlers.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def log_structured_error(
    error_type: str,
    context: Dict[str, Any],
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Log a structured JSON error message for specific failure types.
    """
    if logger is None:
        logger = get_logger()

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": error_type,
        "context": context,
    }
    logger.error(json.dumps(log_entry))

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the SHA256 checksum of a file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def init_seed_config(seed: int = 42) -> None:
    """
    Initialize the global random seed configuration.
    """
    global _GLOBAL_SEED
    _GLOBAL_SEED = seed

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for numpy and python random modules.
    """
    import random
    import numpy as np

    if seed is None:
        seed = _GLOBAL_SEED if _GLOBAL_SEED is not None else 42

    random.seed(seed)
    np.random.seed(seed)

def get_global_seed() -> Optional[int]:
    """
    Retrieve the currently configured global seed.
    """
    return _GLOBAL_SEED
