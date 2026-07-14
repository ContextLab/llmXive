import os
import hashlib
import logging
import numpy as np
import scipy
from typing import Optional, Any, Callable, Union, List, Dict
import random
import sys

def setup_logging(
    log_level: Optional[Union[str, int]] = None,
    name: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.
    
    Flexible signature to handle multiple call patterns:
    - setup_logging() -> uses default INFO
    - setup_logging("INFO") -> string level
    - setup_logging(log_level="INFO") -> kwarg
    - setup_logging(logging.INFO) -> int level
    - setup_logging(logging.INFO, "name") -> name arg (ignored if passed)
    - setup_logging(name="my_logger") -> name kwarg (ignored)
    
    Args:
        log_level: Log level as string ("INFO", "DEBUG", etc.) or int (logging.INFO)
        name: Logger name (optional, currently ignored for simplicity)
    
    Returns:
        Configured logger instance
    """
    # Determine log level
    if log_level is None:
        level = logging.INFO
    elif isinstance(log_level, str):
        level = getattr(logging, log_level.upper(), logging.INFO)
    elif isinstance(log_level, int):
        level = log_level
    else:
        level = logging.INFO
    
    # Configure logging if not already configured
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Get logger
    logger_name = name if name else "llmXive"
    logger = logging.getLogger(logger_name)
    
    # Set level explicitly
    logger.setLevel(level)
    
    return logger

def pin_random_seed(seed: int) -> None:
    """
    Pin random seed for reproducibility across numpy, scipy, and random modules.
    """
    np.random.seed(seed)
    random.seed(seed)
    # For scipy, seed is typically handled through numpy
    # If scipy has its own random state, it uses numpy's
    os.environ['PYTHONHASHSEED'] = str(seed)

def compute_file_checksum(filepath: str) -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        filepath: Path to the file
    
    Returns:
        Hex string of SHA256 checksum
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to compute checksum for {filepath}: {e}")
        return ""

def main():
    """
    Main entry point for utils module.
    """
    logger = setup_logging("INFO")
    logger.info("Utils module loaded")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
