"""
Utility functions for logging, error handling, and result checksumming.

This module provides centralized utilities used across the llmXive pipeline:
- setup_logging: Configures the application logging system.
- compute_checksum: Generates SHA-256 checksums for data integrity verification.
- log_error: Standardized error logging wrapper.
- safe_exit: Graceful process termination with status codes.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Union, Optional
from config import load_config

# Constants
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CHECKSUM_ALGORITHM = "sha256"


def setup_logging(log_level: Optional[str] = None, log_file: Optional[Union[str, Path]] = None) -> logging.Logger:
    """
    Configures the root logger and returns a named logger for the current module.
    
    Args:
        log_level: Optional string level (e.g., 'DEBUG', 'INFO'). If None, loads from config.
        log_file: Optional path to a log file. If None, logs only to console.
    
    Returns:
        logging.Logger: The configured logger instance.
    """
    # Load config for defaults if not provided
    if log_level is None:
        try:
            config = load_config()
            log_level = config.get("logging", {}).get("level", "INFO")
        except Exception:
            log_level = "INFO"

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure root handler
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers to avoid duplicates in repeated calls
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        root_logger.addHandler(file_handler)

    return logging.getLogger(__name__)


def compute_checksum(file_path: Union[str, Path], algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Computes the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        str: Hexadecimal digest of the file.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {path}")
    
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    with open(path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Logs an exception with standardized context and traceback information.
    
    Args:
        logger: The logger instance to use.
        error: The exception object to log.
        context: Optional dictionary of contextual metadata (e.g., {'network_id': 'snap_123'}).
    """
    error_msg = str(error)
    error_type = type(error).__name__
    
    log_entry = {
        "type": error_type,
        "message": error_msg,
        "context": context or {}
    }
    
    # Log at ERROR level
    logger.error(f"Error occurred: {error_type} - {error_msg}", exc_info=True)
    
    # Also log structured JSON for parsing if needed
    logger.debug(f"Structured error details: {json.dumps(log_entry)}")


def safe_exit(logger: logging.Logger, code: int = 0, message: Optional[str] = None) -> None:
    """
    Performs a graceful exit, logging the final status.
    
    Args:
        logger: The logger instance to use.
        code: Exit code (0 for success, non-zero for failure).
        message: Optional message to log before exiting.
    """
    if message:
        if code == 0:
            logger.info(message)
        else:
            logger.error(message)
    
    logger.info(f"Exiting with code {code}")
    sys.exit(code)
