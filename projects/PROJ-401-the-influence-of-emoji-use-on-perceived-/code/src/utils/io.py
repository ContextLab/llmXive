"""
I/O utilities for the llmXive research pipeline.

Provides:
- Logging configuration
- Checksum verification helpers
- Global random seed setting
"""

import hashlib
import logging
import os
import random
from pathlib import Path
from typing import Union

import numpy as np

# Project root relative to this file
_ROOT = Path(__file__).resolve().parent.parent.parent


def configure_logging(
    level: int = logging.INFO,
    log_file: Union[str, Path, None] = None,
    name: str = "llmXive"
) -> logging.Logger:
    """
    Configure logging for the project.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs only to console.
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.handlers:
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def set_global_seed(seed: int = 42) -> None:
    """
    Set global random seeds for reproducibility.

    Args:
        seed: Integer seed value. Defaults to 42.
    """
    random.seed(seed)
    np.random.seed(seed)
    # Note: If using PyTorch or TensorFlow, additional seeding would go here.


def compute_file_checksum(
    file_path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (e.g., 'sha256', 'md5').
        chunk_size: Size of chunks to read.

    Returns:
        Hexadecimal digest of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file_path: Union[str, Path],
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal digest.
        algorithm: Hash algorithm used.

    Returns:
        True if checksums match, False otherwise.
    """
    actual = compute_file_checksum(file_path, algorithm)
    return actual.lower() == expected_checksum.lower()


def ensure_directory(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory.

    Returns:
        The Path object of the directory.
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path
