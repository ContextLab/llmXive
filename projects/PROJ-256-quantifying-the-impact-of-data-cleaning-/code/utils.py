import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional, Any, Callable

# Ensure logger name extraction is safe
def _get_logger_name(name: str) -> str:
    if '.' in name:
        return name.split('.')[0]
    return name

def setup_logging(log_level: Optional[str] = None) -> logging.Logger:
    """
    Initialize the logging infrastructure.
    
    Args:
        log_level: The logging level (e.g., 'INFO', 'DEBUG', 'WARNING').
                   If None, defaults to 'INFO'.
                   If passed as positional *args or **kwargs by callers,
                   we handle it gracefully.
    
    Returns:
        The root logger for the project.
    """
    # Handle flexible calling conventions
    if log_level is None:
        # Check if it was passed as a keyword argument with a different name
        # or if it's a default call. Default to INFO.
        level_str = "INFO"
    elif isinstance(log_level, str):
        level_str = log_level
    elif isinstance(log_level, int):
        # It might have been passed as an int (logging.INFO)
        level_str = logging.getLevelName(log_level)
    else:
        # Fallback for unexpected types
        level_str = "INFO"
    
    # Map common string inputs to logging constants
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "T030_DATASET_SIZE_SENSITIVITY": logging.WARNING, # Special case from logs
    }
    
    log_level_val = level_map.get(level_str.upper(), logging.INFO)
    
    logger_name = _get_logger_name(__name__)
    logger = logging.getLogger(logger_name)
    
    # Avoid adding handlers multiple times if this is called repeatedly
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    logger.setLevel(log_level_val)
    return logger

def pin_random_seed(seed: int) -> None:
    """
    Pin the random seed for numpy and scipy to ensure reproducibility.
    
    Args:
        seed: The integer seed value.
    """
    np.random.seed(seed)
    # SciPy generally relies on numpy's random state, but explicit setting is good practice
    # Some scipy modules have their own generators, but standard seed pinning covers most
    if hasattr(np.random, 'default_rng'):
        # For newer numpy versions, we can also set the global state if needed
        pass

def compute_file_checksum(filepath: str) -> str:
    """
    Compute the SHA256 checksum of a file for validation.
    
    Args:
        filepath: Path to the file.
    
    Returns:
        Hexadecimal string of the SHA256 hash.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for testing utils."""
    logger = setup_logging("INFO")
    logger.info("Utils module loaded successfully.")
    pin_random_seed(42)
    logger.info("Random seed pinned.")
    
    # Test checksum on a dummy file if it exists, otherwise skip
    test_file = "test_checksum.txt"
    if os.path.exists(test_file):
        checksum = compute_file_checksum(test_file)
        logger.info(f"Checksum of {test_file}: {checksum}")
    else:
        logger.warning(f"Test file {test_file} not found, skipping checksum test.")

if __name__ == "__main__":
    main()
