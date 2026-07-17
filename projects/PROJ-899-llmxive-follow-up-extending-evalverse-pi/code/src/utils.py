"""
Utility functions for logging, error handling, and file I/O helpers.

This module provides centralized utilities used across the llmXive pipeline
for consistent logging, robust file operations, and safe data handling.
"""

import logging
import os
import sys
import json
import csv
import shutil
from pathlib import Path
from typing import Optional, Any, Dict, List, Union, Callable
from datetime import datetime

# Import config utilities to ensure paths are handled consistently
from src.config import get_project_root, get_data_root, get_state_root

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}

def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    console: bool = True
) -> None:
    """
    Configure the root logger with specified settings.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to log file. If None, no file handler is added.
        console: If True, add a console handler.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a named logger.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
    
    Returns:
        Configured logger instance
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Inherit settings from root logger
            logger.setLevel(logging.getLogger().level)
        _loggers[name] = logger
    return _loggers[name]

def ensure_directories(*paths: Union[str, Path]) -> List[Path]:
    """
    Ensure that the specified directories exist, creating them if necessary.
    
    Args:
        *paths: One or more path strings or Path objects
    
    Returns:
        List of created/verified Path objects
    """
    created_paths = []
    for path in paths:
        path_obj = Path(path)
        if not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
            created_paths.append(path_obj)
        elif not path_obj.is_dir():
            raise ValueError(f"Path exists but is not a directory: {path_obj}")
    return created_paths

def write_json(
    data: Any,
    file_path: Union[str, Path],
    indent: int = 2,
    ensure_dir: bool = True
) -> Path:
    """
    Write data to a JSON file.
    
    Args:
        data: Data to serialize to JSON
        file_path: Target file path
        indent: JSON indentation level
        ensure_dir: If True, create parent directories if they don't exist
    
    Returns:
        Path object of the written file
    
    Raises:
        TypeError: If data is not JSON serializable
        IOError: If write fails
    """
    path = Path(file_path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, default=str)
    
    return path

def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Parsed data as dictionary
    
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_csv(
    data: List[Dict[str, Any]],
    file_path: Union[str, Path],
    fieldnames: Optional[List[str]] = None,
    ensure_dir: bool = True
) -> Path:
    """
    Write a list of dictionaries to a CSV file.
    
    Args:
        data: List of row dictionaries
        file_path: Target file path
        fieldnames: Optional list of column names. If None, derived from first dict keys.
        ensure_dir: If True, create parent directories if they don't exist
    
    Returns:
        Path object of the written file
    
    Raises:
        ValueError: If data is empty and fieldnames not provided
        IOError: If write fails
    """
    path = Path(file_path)
    if ensure_dir:
        path.parent.mkdir(parents=True, exist_ok=True)
    
    if not data:
        if not fieldnames:
            raise ValueError("Cannot write empty CSV without fieldnames")
        # Write empty file with headers
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        return path
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    return path

def read_csv(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Read a CSV file into a list of dictionaries.
    
    Args:
        file_path: Path to CSV file
    
    Returns:
        List of row dictionaries
    
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If read fails
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_delete(path: Union[str, Path], recursive: bool = True) -> bool:
    """
    Safely delete a file or directory.
    
    Args:
        path: Path to file or directory
        recursive: If True and path is a directory, delete recursively
    
    Returns:
        True if deletion was successful, False if path didn't exist
    
    Raises:
        PermissionError: If deletion is not permitted
        OSError: If deletion fails for other reasons
    """
    path_obj = Path(path)
    if not path_obj.exists():
        return False
    
    if path_obj.is_dir() and recursive:
        shutil.rmtree(path_obj)
    else:
        if path_obj.is_dir() and not recursive:
            raise OSError(f"Cannot delete directory without recursive=True: {path_obj}")
        path_obj.unlink()
    
    return True

def handle_error(
    error: Exception,
    logger: Optional[logging.Logger] = None,
    context: Optional[str] = None,
    raise_on_error: bool = True
) -> None:
    """
    Handle an error by logging it and optionally raising it.
    
    Args:
        error: The exception to handle
        logger: Logger instance. If None, uses root logger.
        context: Optional context string to add to the log message
        raise_on_error: If True, re-raise the exception after logging
    
    Raises:
        The original exception if raise_on_error is True
    """
    log = logger or logging.getLogger(__name__)
    msg = str(error)
    if context:
        msg = f"{context}: {msg}"
    
    log.error(msg, exc_info=True)
    
    if raise_on_error:
        raise error

def validate_file_exists(
    file_path: Union[str, Path],
    logger: Optional[logging.Logger] = None,
    raise_on_missing: bool = True
) -> bool:
    """
    Validate that a file exists at the specified path.
    
    Args:
        file_path: Path to validate
        logger: Logger instance for error messages
        raise_on_missing: If True, raise FileNotFoundError if missing
    
    Returns:
        True if file exists, False otherwise
    
    Raises:
        FileNotFoundError: If file doesn't exist and raise_on_missing is True
    """
    path = Path(file_path)
    if not path.exists():
        msg = f"File not found: {path}"
        if logger:
            logger.error(msg)
        if raise_on_missing:
            raise FileNotFoundError(msg)
        return False
    
    if not path.is_file():
        msg = f"Path exists but is not a file: {path}"
        if logger:
            logger.error(msg)
        if raise_on_missing:
            raise ValueError(msg)
        return False
    
    return True

def get_timestamp_filename(prefix: str = "", suffix: str = "") -> str:
    """
    Generate a filename with a timestamp.
    
    Args:
        prefix: Optional prefix string
        suffix: Optional suffix string (e.g., .csv, .json)
    
    Returns:
        Filename string with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}{timestamp}{suffix}"

def format_size(size_bytes: int) -> str:
    """
    Format a byte size into a human-readable string.
    
    Args:
        size_bytes: Size in bytes
    
    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"