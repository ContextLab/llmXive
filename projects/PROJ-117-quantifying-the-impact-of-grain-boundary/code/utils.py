import hashlib
import logging
import os
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

# Standardized logging format configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the project with a standardized format.
    
    Args:
        log_file: Optional path to a log file. If provided, logs are written to both
                  stdout and the file.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        Configured logger instance named "llmXive".
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    # Prevent adding duplicate handlers if function is called multiple times
    if logger.handlers:
        return logger

    # Create formatter with standardized settings
    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
    
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def set_random_seed(seed: int = 42) -> None:
    """
    Set random seed for reproducibility across numpy, random, and environment.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: numpy seed is typically set in scripts that import numpy directly
    # to avoid circular imports in this utility module.

def load_metadata(metadata_path: str) -> Dict[str, Any]:
    """
    Load metadata from a YAML file.
    
    Args:
        metadata_path: Path to the metadata YAML file.
    
    Returns:
        Dictionary containing metadata, or empty dict if file doesn't exist.
    """
    if not os.path.exists(metadata_path):
        return {}
    with open(metadata_path, "r") as f:
        return yaml.safe_load(f) or {}

def update_metadata_entry(metadata_path: str, key: str, value: Any) -> None:
    """
    Update or add an entry in the metadata YAML file.
    
    Args:
        metadata_path: Path to the metadata YAML file.
        key: The key to update or add.
        value: The value to assign to the key.
    """
    metadata = load_metadata(metadata_path)
    metadata[key] = value
    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False)

def save_metadata(metadata: Dict[str, Any], metadata_path: str) -> None:
    """
    Save metadata to a YAML file.
    
    Args:
        metadata: Dictionary to save.
        metadata_path: Path to the output YAML file.
    """
    Path(metadata_path).parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_path, "w") as f:
        yaml.dump(metadata, f, default_flow_style=False)