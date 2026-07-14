"""
Utility functions for logging, file I/O helpers, and checksum recording.

This module provides:
- setup_logging: Configures a consistent logging format for the project.
- save_json: Safely writes a Python object to a JSON file.
- load_json: Loads a JSON file into a Python object.
- compute_file_checksum: Calculates SHA-256 checksum of a file.
- record_checksums: Records checksums of a list of files to a manifest.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Default log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Union[str, Path]] = None,
    name: str = "llmXive"
) -> logging.Logger:
    """
    Configures and returns a logger with the specified level and format.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If provided, logs are written to this file.
        name: Name of the logger.
    
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def save_json(
    data: Dict[str, Any],
    output_path: Union[str, Path],
    ensure_dir: bool = True
) -> None:
    """
    Saves a Python object as a JSON file.
    
    Args:
        data: The dictionary or object to save.
        output_path: Path to the output JSON file.
        ensure_dir: If True, creates parent directories if they don't exist.
    
    Raises:
        TypeError: If data is not JSON serializable.
        OSError: If the file cannot be written.
    """
    path = Path(output_path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)


def load_json(input_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Loads a JSON file into a Python dictionary.
    
    Args:
        input_path: Path to the input JSON file.
    
    Returns:
        Dictionary containing the JSON data.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(input_path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Computes the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: 'sha256').
    
    Returns:
        Hexadecimal string of the checksum.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    hash_func = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def record_checksums(
    file_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Computes checksums for a list of files and saves them to a manifest JSON.
    
    Args:
        file_paths: List of file paths to checksum.
        output_path: Path to the output manifest JSON file.
        algorithm: Hash algorithm to use.
    
    Returns:
        Dictionary mapping file paths to their checksums.
    """
    checksums: Dict[str, str] = {}
    for file_path in file_paths:
        path_str = str(file_path)
        try:
            checksums[path_str] = compute_file_checksum(file_path, algorithm)
        except FileNotFoundError:
            checksums[path_str] = "ERROR: FILE_NOT_FOUND"
        except Exception as e:
            checksums[path_str] = f"ERROR: {str(e)}"
    
    save_json(checksums, output_path)
    return checksums