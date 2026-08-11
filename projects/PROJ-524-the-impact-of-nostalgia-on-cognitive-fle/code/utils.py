"""
Utility functions for logging, checksums, and versioning.
"""
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level.
        log_file: Optional path to a log file.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("nostalgia_cognitive")
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


def log_info(logger: logging.Logger, message: str):
    """Log an info message."""
    logger.info(message)


def log_debug(logger: logging.Logger, message: str):
    """Log a debug message."""
    logger.debug(message)


def log_warning(logger: logging.Logger, message: str):
    """Log a warning message."""
    logger.warning(message)


def log_error(logger: logging.Logger, message: str):
    """Log an error message."""
    logger.error(message)


def log_critical(logger: logging.Logger, message: str):
    """Log a critical message."""
    logger.critical(message)


def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hex digest.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = compute_sha256(file_path)
    return actual_checksum == expected_checksum


def get_version() -> str:
    """Get the current version of the project."""
    return "0.1.0"


def get_timestamp() -> str:
    """Get the current timestamp as a string."""
    return datetime.now().isoformat()
