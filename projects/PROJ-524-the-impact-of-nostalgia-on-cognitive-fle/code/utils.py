import os
import logging
import hashlib
from pathlib import Path
from datetime import datetime
import json

logger = None

def setup_logging(level: str = 'INFO') -> logging.Logger:
    """
    Setup the global logger.
    """
    global logger
    if logger is None:
        logging.basicConfig(
            level=getattr(logging, level.upper(), logging.INFO),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger('llmXive')
    return logger

def log_info(msg: str):
    if logger:
        logger.info(msg)

def log_warning(msg: str):
    if logger:
        logger.warning(msg)

def log_error(msg: str):
    if logger:
        logger.error(msg)

def log_critical(msg: str):
    if logger:
        logger.critical(msg)

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual = compute_sha256(file_path)
    return actual == expected_checksum

def get_version() -> str:
    """Return a simple version string."""
    return "0.1.0"

def get_timestamp() -> str:
    """Return current ISO timestamp."""
    return datetime.now().isoformat()
