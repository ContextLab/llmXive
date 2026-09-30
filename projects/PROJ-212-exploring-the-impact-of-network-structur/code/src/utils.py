import hashlib
import json
import logging
import sys
import os
import time
from pathlib import Path
from typing import Any, Dict, Union, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_logging(config: Dict[str, Any]) -> None:
    """
    Sets up logging based on configuration.
    """
    log_level = config.get('logging', {}).get('level', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    logging.getLogger().setLevel(numeric_level)
    logger.info(f"Logging set to {log_level}")

def compute_checksum(file_path: Path) -> str:
    """
    Computes the SHA256 checksum of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_error(error: Exception, log_path: Path) -> None:
    """
    Logs an error to a file.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, 'a') as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - ERROR - {str(error)}\n")
    logger.error(f"Error logged to {log_path}")

def safe_exit(code: int = 0) -> None:
    """
    Safely exits the program.
    """
    logger.info(f"Exiting with code {code}")
    sys.exit(code)

def timing_decorator(func):
    """
    Decorator to time function execution.
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper
