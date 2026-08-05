"""
utils.py - Helper functions for the smooth number distribution pipeline.

Provides:
  - Deterministic random seed management
  - Checksum generation for data integrity
  - Configurable structured logging
"""
import hashlib
import logging
import os
import random
from typing import Optional, Union

import numpy as np

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DEFAULT_SEED = 42

def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    format_str: str = DEFAULT_LOG_FORMAT
) -> logging.Logger:
    """
    Configure the root logger with the specified level and format.
    Optionally writes logs to a file.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs to console only.
        format_str: Log message format string.

    Returns:
        The configured root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in interactive environments
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_str))
    root_logger.addHandler(console_handler)

    # File handler
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str))
        root_logger.addHandler(file_handler)

    return root_logger


def set_deterministic_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Sets the random seed for reproducibility across Python's random,
    NumPy, and (optionally) other libraries if needed.

    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    # If using PyTorch or TensorFlow, set their seeds here as well
    # torch.manual_seed(seed)
    # torch.cuda.manual_seed_all(seed)


def generate_checksum(file_path: str, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """
    Generates a cryptographic checksum for a file to ensure data integrity.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (e.g., 'sha256', 'md5').
        chunk_size: Size of chunks to read from the file.

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm '{algorithm}': {e}")

    with open(file_path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            hasher.update(data)

    return hasher.hexdigest()


def get_file_size_human(file_path: str) -> str:
    """
    Returns the file size in a human-readable format (e.g., '1.5 MB').

    Args:
        file_path: Path to the file.

    Returns:
        Human-readable size string.
    """
    if not os.path.exists(file_path):
        return "0 B"

    size_bytes = os.path.getsize(file_path)
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} PB"