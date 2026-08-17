"""
Utility functions for logging, configuration, and checksumming.
"""
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

def setup_logging(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Setup a logger with timestamp and level.
    Handles the case where log_level is passed as a string like '__main__' incorrectly.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Default level
    level = logging.INFO
    if log_level:
        try:
            # Ensure log_level is a valid string like 'INFO', 'DEBUG', etc.
            # If it's something weird like '__main__', ignore it and use default
            if log_level.upper() in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                level = getattr(logging, log_level.upper())
            else:
                # If invalid level string, log warning and use default
                logging.warning(f"Invalid log level '{log_level}', using INFO")
        except AttributeError:
            logging.warning(f"Invalid log level '{log_level}', using INFO")
    
    logger.setLevel(level)
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    
    return logger

def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load configuration from a YAML file or environment variables.
    Returns a dictionary.
    """
    import yaml
    if config_path is None:
        config_path = os.getenv("PROJECT_CONFIG", "config.yaml")
    
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute SHA-256 checksum of a file.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify file checksum against expected value.
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum
