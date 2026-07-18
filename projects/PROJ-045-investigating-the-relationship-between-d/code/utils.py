"""
Utility functions for logging, configuration, and file operations.
"""

import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Configure logging for the project.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config.yaml file. Defaults to 'config.yaml' in project root.

    Returns:
        Dictionary containing configuration values.
    """
    if config_path is None:
        config_path = Path("config.yaml")

    if not config_path.exists():
        logging.warning(f"Config file {config_path} not found. Using defaults.")
        return {}

    with open(config_path, "r") as f:
        return yaml.safe_load(f) or {}

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum == expected_checksum
