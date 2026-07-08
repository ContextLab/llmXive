"""
Utility functions for data processing, including seed management and logging.
"""
import os
import random
import hashlib
import logging
from typing import Optional, Dict, Any

# Constants
DEFAULT_SEED = 42
SEED_ENV_VAR = "MOL_PERM_SEED"
LOG_LEVEL_ENV_VAR = "MOL_PERM_LOG_LEVEL"

# Global state for reproducibility
_global_seed: Optional[int] = None
_seed_hash: Optional[str] = None


def set_seed(seed: Optional[int] = None) -> int:
    """
    Initialize random seeds for reproducibility across Python, NumPy (if available),
    and PyTorch (if available).

    Args:
        seed: The seed value to use. If None, reads from environment variable
              `MOL_PERM_SEED`, or defaults to 42.

    Returns:
        The seed value that was set.
    """
    global _global_seed, _seed_hash

    if seed is None:
        seed = int(os.getenv(SEED_ENV_VAR, DEFAULT_SEED))

    _global_seed = seed
    _seed_hash = hashlib.sha256(str(seed).encode()).hexdigest()[:16]

    # Set Python's random seed
    random.seed(seed)

    # Set NumPy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    # Set PyTorch seeds if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass

    return seed


def get_seed() -> Optional[int]:
    """
    Get the currently set global seed.

    Returns:
        The global seed integer, or None if not yet set.
    """
    return _global_seed


def get_seed_hash() -> Optional[str]:
    """
    Get the hash of the currently set seed for logging and tracking.

    Returns:
        The SHA-256 hash (truncated to 16 chars) of the seed, or None.
    """
    return _seed_hash


def _get_log_level_from_env() -> int:
    """
    Determine the logging level from environment variables.
    
    Checks MOL_PERM_LOG_LEVEL for a string representation (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    Falls back to logging.INFO if not set or invalid.
    
    Returns:
        The logging level constant.
    """
    level_str = os.getenv(LOG_LEVEL_ENV_VAR, "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, logging.INFO)


def setup_logging(
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    name: str = "mol_perm"
) -> logging.Logger:
    """
    Configure and return a logger with console and optional file handlers.
    
    The logging level can be provided explicitly or determined from the 
    MOL_PERM_LOG_LEVEL environment variable.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO). If None,
               reads from environment variable `MOL_PERM_LOG_LEVEL`, or defaults to INFO.
        log_file: Optional path to a log file. If None, only console logging.
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    if level is None:
        level = _get_log_level_from_env()

    logger = logging.getLogger(name)
    
    # Only configure if handlers are not already present to avoid duplication
    if not logger.handlers:
        logger.setLevel(level)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (optional)
        if log_file:
            # Ensure directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    else:
        # If handlers exist, just ensure the level is correct
        logger.setLevel(level)

    return logger


def ensure_seed_initialized() -> int:
    """
    Ensure a seed has been set. If not, initialize it with the default.

    Returns:
        The seed value in use.
    """
    if _global_seed is None:
        return set_seed()
    return _global_seed