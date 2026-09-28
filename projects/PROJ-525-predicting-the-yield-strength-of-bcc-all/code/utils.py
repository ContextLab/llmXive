import hashlib
import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union

def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one."""
    return logging.getLogger(name)

def compute_sha256(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def verify_sha256(file_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify a file's SHA-256 hash against an expected value."""
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def compute_directory_checksum(dir_path: Union[str, Path]) -> str:
    """
    Compute a checksum for a directory by hashing the sorted list of 
    file paths and their individual hashes.
    """
    path = Path(dir_path)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    hasher = hashlib.sha256()
    files = sorted([str(f.relative_to(path)) for f in path.rglob("*") if f.is_file()])
    
    for rel_path in files:
        full_path = path / rel_path
        file_hash = compute_sha256(full_path)
        hasher.update(f"{rel_path}:{file_hash}".encode('utf-8'))
    
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

def handle_error(e: Exception, logger: Optional[logging.Logger] = None) -> None:
    """Handle an error by logging and potentially raising a specific exception."""
    if logger:
        logger.error(f"Error occurred: {e}", exc_info=True)
    else:
        print(f"Error occurred: {e}", file=sys.stderr)
    raise e

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning a default if division by zero occurs."""
    if denominator == 0:
        return default
    return numerator / denominator

def format_bytes(size: int) -> str:
    """Format bytes into a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"
