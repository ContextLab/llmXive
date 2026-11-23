"""
Utility functions for the llmXive pipeline.
"""

import os
import json
import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

logger: Optional[logging.Logger] = None

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure the global logger for the pipeline.
    
    Args:
        level: Logging level (INFO, DEBUG, WARNING, ERROR).
        
    Returns:
        The configured logger instance.
    """
    global logger
    if logger is None:
        logger = logging.getLogger("llmXive")
        logger.setLevel(level)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
    
    return logger

def get_timestamp() -> str:
    """Return the current timestamp as an ISO format string."""
    return datetime.now().isoformat()

def log_info(msg: str) -> None:
    """Log an info message."""
    if logger:
        logger.info(msg)
    else:
        print(f"INFO: {msg}")

def log_warning(msg: str) -> None:
    """Log a warning message."""
    if logger:
        logger.warning(msg)
    else:
        print(f"WARNING: {msg}")

def log_error(msg: str) -> None:
    """Log an error message."""
    if logger:
        logger.error(msg)
    else:
        print(f"ERROR: {msg}")

def compute_checksum(filepath: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal digest of the file.
    """
    hash_func = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def ensure_dirs(paths: List[Path]) -> None:
    """Ensure that a list of directories exists."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

def save_json(data: Dict[str, Any], filepath: Path) -> None:
    """Save a dictionary to a JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(filepath: Path) -> Dict[str, Any]:
    """Load a dictionary from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)
