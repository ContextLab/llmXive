"""
Logging utilities for standardized experiment logging and checksum generation.

This module provides:
- Standardized logging configuration for experiment runs.
- Checksum generation for data files to ensure reproducibility.
"""

import hashlib
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

def configure_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    experiment_name: Optional[str] = None
) -> logging.Logger:
    """
    Configure standardized logging for experiment runs.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, logs only to console.
        experiment_name: Optional name for the experiment, used in log messages.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if experiment_name:
        logger.info(f"Starting experiment: {experiment_name}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")

    return logger

def generate_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Generate a cryptographic checksum for a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)

    # Read file in chunks to handle large files
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

def write_checksum_file(
    file_path: str,
    output_path: str,
    algorithm: str = "sha256"
) -> None:
    """
    Generate a checksum for a file and write it to a checksum file.

    The output format is: <checksum>  <filename>
    (matching standard checksum file formats)

    Args:
        file_path: Path to the file to checksum.
        output_path: Path to write the checksum file.
        algorithm: Hash algorithm to use.
    """
    checksum = generate_checksum(file_path, algorithm)
    filename = os.path.basename(file_path)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(f"{checksum}  {filename}\n")

def log_experiment_metadata(
    logger: logging.Logger,
    metadata: Dict[str, Any],
    output_path: Optional[str] = None
) -> None:
    """
    Log experiment metadata in a structured format.

    Args:
        logger: Logger instance to use.
        metadata: Dictionary of metadata key-value pairs.
        output_path: Optional path to write metadata as JSON.
    """
    logger.info("Experiment Metadata:")
    for key, value in metadata.items():
        logger.info(f"  {key}: {value}")

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        logger.info(f"Metadata written to: {output_path}")

def validate_checksum(file_path: str, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Validate a file's checksum against an expected value.

    Args:
        file_path: Path to the file to validate.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual_checksum = generate_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()
