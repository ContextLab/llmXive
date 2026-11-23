"""
General utility functions for the project.
Provides logging, checksum operations, and custom exceptions.
"""
import hashlib
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with standard formatting.
    
    Args:
        name: Logger name
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get an existing logger or create if it doesn't exist.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hexadecimal hash string
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_sha256(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify a file's SHA-256 hash against an expected value.
    
    Args:
        file_path: Path to the file
        expected_hash: Expected hash value
    
    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()

def compute_directory_checksum(directory_path: Union[str, Path]) -> str:
    """
    Compute a combined checksum for a directory.
    
    Args:
        directory_path: Path to the directory
    
    Returns:
        Combined checksum string
    """
    directory_path = Path(directory_path)
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    
    hasher = hashlib.sha256()
    files = sorted([f for f in directory_path.rglob('*') if f.is_file()])
    
    for file_path in files:
        if file_path.name == ".gitkeep":
            continue
        rel_path = file_path.relative_to(directory_path)
        hasher.update(str(rel_path).encode())
        hasher.update(compute_sha256(file_path).encode())
    
    return hasher.hexdigest()

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataIntegrityError(PipelineError):
    """Exception for data integrity violations."""
    pass

class DataScarcityError(PipelineError):
    """Exception for insufficient data conditions."""
    pass

class ConfigurationError(PipelineError):
    """Exception for configuration errors."""
    pass

class ValidationError(PipelineError):
    """Exception for validation failures."""
    pass

def handle_error(error: Exception, logger: Optional[logging.Logger] = None) -> None:
    """
    Handle and log an error.
    
    Args:
        error: Exception to handle
        logger: Logger to use (creates default if None)
    """
    if logger is None:
        logger = setup_logger("utils")
    
    logger.error(f"Error occurred: {type(error).__name__}: {str(error)}")
    raise error

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to ensure
    
    Returns:
        The path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default on division by zero.
    
    Args:
        numerator: Dividend
        denominator: Divisor
        default: Default value if division by zero
    
    Returns:
        Result of division or default value
    """
    if denominator == 0:
        return default
    return numerator / denominator

def format_bytes(size: int) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size: Size in bytes
    
    Returns:
        Human-readable string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"