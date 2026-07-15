import logging
import os
import sys
import hashlib
import json
from datetime import datetime

# Global seed state
_global_seed = None
_seed_initialized = False

def get_logger(name: str) -> logging.Logger:
    """
    Configure and return a logger with a standard format.

    Args:
        name: The name of the logger (usually __name__).

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

def log_structured_error(error_type: str, message: str, details: dict = None) -> None:
    """
    Log an error in a structured JSON format for downstream parsing.

    Args:
        error_type: The specific type of error (e.g., 'unmatched_participant_ids').
        message: A human-readable description.
        details: Optional dictionary of additional context.
    """
    logger = get_logger(__name__)
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_type": error_type,
        "message": message,
        "details": details or {}
    }
    logger.error(json.dumps(log_entry))

def compute_file_checksum(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.

    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    hasher = hashlib.new(algorithm)
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        raise ValueError(f"Failed to compute checksum: {e}")

def init_seed_config(seed: int = 42):
    """
    Initialize the global random seed configuration.

    Args:
        seed: The seed value to use.
    """
    global _global_seed, _seed_initialized
    _global_seed = seed
    _seed_initialized = True
    # Also set for numpy and random for consistency
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)

def set_random_seed(seed: int = None):
    """
    Set the random seed for reproducibility. Uses global seed if none provided.

    Args:
        seed: Optional explicit seed.
    """
    import random
    import numpy as np

    if seed is None:
        if not _seed_initialized:
            raise RuntimeError("Global seed not initialized. Call init_seed_config first.")
        seed = _global_seed

    random.seed(seed)
    np.random.seed(seed)

def get_global_seed() -> int:
    """
    Get the currently configured global seed.

    Returns:
        The global seed integer.

    Raises:
        RuntimeError: If seed has not been initialized.
    """
    if not _seed_initialized:
        raise RuntimeError("Global seed not initialized. Call init_seed_config first.")
    return _global_seed
