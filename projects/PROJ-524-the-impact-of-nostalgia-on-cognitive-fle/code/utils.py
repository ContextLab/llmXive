"""
Utility functions for the project.
"""
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure logging is configured before use in other modules
_logger: Optional[logging.Logger] = None


def setup_logging(level: int = logging.INFO, name: str = "llmXive") -> logging.Logger:
    """
    Configures the root logger for the application.

    Args:
        level: The logging level (e.g., logging.INFO).
        name: The name of the logger (usually the project name).

    Returns:
        The configured logger instance.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if not _logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
            _logger.setLevel(level)
    return _logger


def log_info(msg: str) -> None:
    """Logs an info message."""
    logger = _logger or setup_logging()
    logger.info(msg)


def log_debug(msg: str) -> None:
    """Logs a debug message."""
    logger = _logger or setup_logging()
    logger.debug(msg)


def log_warning(msg: str) -> None:
    """Logs a warning message."""
    logger = _logger or setup_logging()
    logger.warning(msg)


def log_error(msg: str) -> None:
    """Logs an error message."""
    logger = _logger or setup_logging()
    logger.error(msg)


def log_critical(msg: str) -> None:
    """Logs a critical message."""
    logger = _logger or setup_logging()
    logger.critical(msg)


def compute_sha256(file_path: str) -> str:
    """
    Computes the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verifies if a file's SHA-256 checksum matches the expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: The expected hexadecimal checksum string.

    Returns:
        True if the checksums match, False otherwise.
    """
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum


def get_version() -> str:
    """
    Returns the current project version string.
    """
    return "0.1.0-dev"


def get_timestamp() -> str:
    """
    Returns the current timestamp in ISO 8601 format.
    """
    return datetime.now().isoformat()
