"""
Utility functions for the pipeline.
Handles logging, checksums, and custom exceptions.
"""
import hashlib
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union

def setup_logger(name: str, log_file: Optional[Union[str, Path]] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with console and optional file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one if it doesn't exist."""
    return logging.getLogger(name)

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_sha256(file_path: Path, expected_hash: str) -> bool:
    """Verify the SHA256 hash of a file against an expected value."""
    return compute_sha256(file_path) == expected_hash.lower()

def compute_directory_checksum(dir_path: Path) -> str:
    """Compute a checksum for a directory by hashing all file checksums."""
    import hashlib
    hasher = hashlib.sha256()
    for root, _, files in sorted(os.walk(dir_path)):
        for filename in sorted(files):
            if filename == ".gitkeep":
                continue
            filepath = Path(root) / filename
            try:
                file_hash = compute_sha256(filepath)
                hasher.update(file_hash.encode())
            except (OSError, IOError):
                continue
    return hasher.hexdigest()

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataIntegrityError(PipelineError):
    """Exception raised when data integrity checks fail."""
    pass

class DataScarcityError(PipelineError):
    """Exception raised when insufficient data is found."""
    pass

class ConfigurationError(PipelineError):
    """Exception raised when configuration is invalid."""
    pass

class ValidationError(PipelineError):
    """Exception raised when validation fails."""
    pass

def handle_error(error: Exception, logger: Optional[logging.Logger] = None) -> None:
    """Handle an error by logging it and optionally raising."""
    msg = str(error)
    if logger:
        logger.error(msg)
    else:
        print(f"ERROR: {msg}", file=sys.stderr)

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning a default if division by zero occurs."""
    if denominator == 0:
        return default
    return numerator / denominator

def format_bytes(num_bytes: int) -> str:
    """Format a byte count into a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"
