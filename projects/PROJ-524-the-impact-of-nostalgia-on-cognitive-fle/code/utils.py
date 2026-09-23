"""
Utility functions for logging, checksums, and versioning.
"""
import os
import logging
import hashlib
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

# Logging configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

def setup_logging(log_level: Optional[int] = None) -> logging.Logger:
    """
    Configure and return the root logger.
    """
    level = log_level or getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper(), DEFAULT_LOG_LEVEL)
    logging.basicConfig(level=level, format=LOG_FORMAT)
    return logging.getLogger()

def log_info(msg: str) -> None:
    """Log an info message."""
    logging.info(msg)

def log_warning(msg: str) -> None:
    """Log a warning message."""
    logging.warning(msg)

def log_error(msg: str) -> None:
    """Log an error message."""
    logging.error(msg)

def log_critical(msg: str) -> None:
    """Log a critical message."""
    logging.critical(msg)

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.
    Returns the hex digest string.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.
    Returns True if they match, False otherwise.
    """
    try:
        actual = compute_sha256(file_path)
        return actual.lower() == expected_checksum.lower()
    except FileNotFoundError:
        return False

def get_version() -> str:
    """
    Get the current version from a version file or return a default.
    """
    version_file = Path('VERSION')
    if version_file.exists():
        return version_file.read_text().strip()
    return "0.1.0"

def get_timestamp() -> str:
    """Get the current timestamp as an ISO format string."""
    return datetime.now().isoformat()

def save_json(data: dict, file_path: str) -> None:
    """Save a dictionary to a JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def load_json(file_path: str) -> dict:
    """Load a dictionary from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)
