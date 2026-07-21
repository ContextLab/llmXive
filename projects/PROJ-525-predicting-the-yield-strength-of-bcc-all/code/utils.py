"""
Utility functions for logging, checksumming (SHA-256), and error handling.

This module provides centralized infrastructure for:
- Configuring logging with file and console handlers
- Computing SHA-256 checksums for data integrity verification
- Custom exception classes for consistent error handling
"""

import hashlib
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

# ---------------------------------------------------------------------------
# Logging Infrastructure
# ---------------------------------------------------------------------------

def setup_logger(
    name: str,
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
    include_timestamp: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with optional file and console handlers.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to log file. If None, only console handler is used.
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        include_timestamp: Whether to include timestamps in log format
    
    Returns:
        Configured logger instance
    
    Example:
        logger = setup_logger(__name__, "data/logs/pipeline.log", logging.DEBUG)
        logger.info("Pipeline started")
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    if include_timestamp:
        date_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            f"%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt=date_fmt
        )
    else:
        formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger by name, creating one if it doesn't exist.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Default setup if no handlers exist
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

# ---------------------------------------------------------------------------
# Checksumming Infrastructure (SHA-256)
# ---------------------------------------------------------------------------

def compute_sha256(file_path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        chunk_size: Size of chunks to read (default 8KB for memory efficiency)
    
    Returns:
        Hexadecimal string of the SHA-256 hash
    
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def verify_sha256(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's SHA-256 checksum against an expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA-256 hex string
    
    Returns:
        True if checksum matches, False otherwise
    
    Raises:
        FileNotFoundError: If the file does not exist
    """
    computed = compute_sha256(file_path)
    return computed.lower() == expected_checksum.lower()

def compute_directory_checksum(dir_path: Union[str, Path], pattern: str = "*") -> str:
    """
    Compute a combined checksum for all files in a directory.
    
    The checksum is computed by hashing the sorted list of (filename, file_hash) pairs.
    
    Args:
        dir_path: Path to the directory
        pattern: Glob pattern for files to include (default: all files)
    
    Returns:
        Hexadecimal string of the combined SHA-256 hash
    
    Raises:
        NotADirectoryError: If the path is not a directory
    """
    dir_path = Path(dir_path)
    
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")
    
    # Get all files matching pattern, sorted for reproducibility
    files = sorted(dir_path.glob(pattern))
    
    combined_hash = hashlib.sha256()
    
    for file_path in files:
        if file_path.is_file():
            # Include relative path and file hash
            rel_path = file_path.relative_to(dir_path)
            file_hash = compute_sha256(file_path)
            entry = f"{rel_path}:{file_hash}\n"
            combined_hash.update(entry.encode('utf-8'))
    
    return combined_hash.hexdigest()

# ---------------------------------------------------------------------------
# Error Handling Infrastructure
# ---------------------------------------------------------------------------

class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    
    def __init__(self, message: str, code: str = "PIPELINE_ERROR"):
        self.message = message
        self.code = code
        self.timestamp = datetime.now().isoformat()
        super().__init__(f"[{self.code}] {message}")

class DataIntegrityError(PipelineError):
    """Raised when data integrity checks fail (e.g., checksum mismatch)."""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        self.file_path = file_path
        super().__init__(message, code="DATA_INTEGRITY")

class DataScarcityError(PipelineError):
    """Raised when insufficient data is available for processing."""
    
    def __init__(self, message: str, count: int = 0, threshold: int = 0):
        self.count = count
        self.threshold = threshold
        super().__init__(message, code="DATA_SCARCITY")

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, key: Optional[str] = None):
        self.key = key
        super().__init__(message, code="CONFIG_ERROR")

class ValidationError(PipelineError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[str] = None):
        self.field = field
        self.value = value
        super().__init__(message, code="VALIDATION_ERROR")

def handle_error(
    logger: Optional[logging.Logger] = None,
    error: Optional[Exception] = None,
    exit_on_error: bool = True
) -> None:
    """
    Handle errors with consistent logging and optional exit.
    
    Args:
        logger: Logger instance (creates default if None)
        error: Exception instance to handle (if None, uses current exception)
        exit_on_error: Whether to exit the program after handling
    
    Example:
        try:
            risky_operation()
        except Exception as e:
            handle_error(logger, e, exit_on_error=True)
    """
    if logger is None:
        logger = get_logger(__name__)
    
    if error is None:
        import sys
        exc_type, exc_value, exc_tb = sys.exc_info()
        if exc_value is None:
            return
        error = exc_value
    
    error_type = type(error).__name__
    error_msg = str(error)
    
    if isinstance(error, PipelineError):
        logger.error(f"{error.code} - {error_msg}")
    else:
        logger.error(f"{error_type} - {error_msg}")
    
    if exit_on_error:
        sys.exit(1)

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory
    
    Returns:
        The Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning a default value on division by zero.
    
    Args:
        numerator: The numerator
        denominator: The denominator
        default: Value to return if denominator is zero
    
    Returns:
        The result of division or the default value
    """
    if denominator == 0:
        return default
    return numerator / denominator

def format_bytes(num_bytes: int) -> str:
    """
    Format a byte count into a human-readable string.
    
    Args:
        num_bytes: Number of bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"