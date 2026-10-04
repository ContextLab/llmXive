import os
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Sets up logging configuration for the project.
    
    Args:
        level: Logging level (default: INFO)
        
    Returns:
        Logger instance
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=level, format=log_format)
    return logging.getLogger(__name__)

def get_timestamp() -> str:
    """Returns current timestamp in ISO format."""
    return datetime.now().isoformat()

def calculate_checksum(file_path: str) -> str:
    """
    Calculates SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the checksum
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def log_info(msg: str, logger: Optional[logging.Logger] = None):
    """Logs an info message."""
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.info(msg)

def log_warning(msg: str, logger: Optional[logging.Logger] = None):
    """Logs a warning message."""
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.warning(msg)

def log_error(msg: str, logger: Optional[logging.Logger] = None):
    """Logs an error message."""
    if logger is None:
        logger = logging.getLogger(__name__)
    logger.error(msg)

def save_json(data: Dict[str, Any], file_path: str) -> None:
    """Saves a dictionary to a JSON file."""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(file_path: str) -> Dict[str, Any]:
    """Loads a dictionary from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)
