"""
Utility module for llmXive project: PROJ-524-the-impact-of-nostalgia-on-cognitive-fle.

Provides:
- SHA-256 checksum helpers for file integrity verification
- Centralized logging setup
- Versioning logic
"""
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

# Project constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = PROJECT_ROOT / "data" / "logs" / "pipeline.log"
VERSION = "0.1.0"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    name: str = "llmXive"
) -> logging.Logger:
    """
    Configure and return a project logger with both file and console handlers.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Path to log file. Defaults to data/logs/pipeline.log relative to project root.
        name: Logger name.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Ensure log directory exists
    if log_file is None:
        log_file = LOG_FILE
    else:
        log_file = Path(log_file)
        
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (IOError, PermissionError) as e:
        print(f"Warning: Could not create log file {log_file}: {e}", file=sys.stderr)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        chunk_size: Size of chunks to read (default 8KB).
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
        
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
            
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's SHA-256 checksum against an expected value.
    
    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hex string.
        
    Returns:
        True if checksums match, False otherwise.
    """
    try:
        actual_checksum = compute_sha256(file_path)
        return actual_checksum.lower() == expected_checksum.lower()
    except (FileNotFoundError, ValueError) as e:
        logging.getLogger(__name__).error(f"Checksum verification failed: {e}")
        return False


def get_version() -> str:
    """Return the current project version string."""
    return VERSION


def get_timestamp() -> str:
    """Return current timestamp in ISO format."""
    return datetime.now().isoformat()


# Initialize default logger for module-level use
_logger = setup_logging()

def log_debug(msg: str):
    _logger.debug(msg)

def log_info(msg: str):
    _logger.info(msg)

def log_warning(msg: str):
    _logger.warning(msg)

def log_error(msg: str):
    _logger.error(msg)

def log_critical(msg: str):
    _logger.critical(msg)