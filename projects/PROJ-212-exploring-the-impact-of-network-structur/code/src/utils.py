import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Union, Optional

logger = logging.getLogger(__name__)

def setup_logging(level: int = logging.INFO, log_file: Optional[Union[str, Path]] = None) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs to stderr.

    Returns:
        The root logger instance.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger

def compute_checksum(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_error(error: Exception, context: str = "") -> None:
    """
    Log an error with optional context.

    Args:
        error: The exception object.
        context: Additional context string.
    """
    msg = f"Error: {str(error)}"
    if context:
        msg = f"{context}: {msg}"
    logger.error(msg, exc_info=True)

def safe_exit(code: int = 0) -> None:
    """
    Safely exit the application.

    Args:
        code: Exit code (0 for success, non-zero for failure).
    """
    logger.info(f"Exiting with code {code}")
    sys.exit(code)

# Added import for numpy which is used in topology.py degree_std calculation
import numpy as np
