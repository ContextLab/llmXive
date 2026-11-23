"""
Shared utility functions for the Glass Transition Temperature Prediction Pipeline.

This module provides common helpers for logging configuration and checksum
verification to ensure data integrity during the research pipeline.
"""

import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def setup_logging(
    name: str = "glass_pipeline",
    level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configure and return a logger with standardized formatting.

    Args:
        name: Name of the logger.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs only to stderr.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def compute_file_checksum(
    file_path: Path,
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """
    Compute the cryptographic checksum of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: 'sha256').
        chunk_size: Size of chunks to read for large files.

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm '{algorithm}': {e}")

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file_path: Path,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: The expected hex checksum string.
        algorithm: Hash algorithm used.

    Returns:
        True if checksums match, False otherwise.
    """
    if not file_path.exists():
        return False

    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum.lower()


def ensure_directory(dir_path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        dir_path: Path to the directory.
    """
    dir_path.mkdir(parents=True, exist_ok=True)


def get_project_root() -> Path:
    """
    Return the absolute path to the project root.

    Returns:
        Path object for the project root.
    """
    return PROJECT_ROOT