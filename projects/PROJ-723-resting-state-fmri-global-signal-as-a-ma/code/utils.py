"""
Utility functions for logging, file I/O, and error handling.
"""
import logging
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import time
from functools import wraps

from config import ensure_directories

# Logger setup
logger = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get or create a logger instance."""
    global logger
    if logger is None:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    return logger

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure the root logging settings."""
    global logger
    logger = get_logger()
    logger.setLevel(log_level)

def read_json(path: Union[str, Path]) -> Dict[str, Any]:
    """Read a JSON file and return its contents."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(path: Union[str, Path], data: Dict[str, Any]) -> None:
    """Write data to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)

def read_csv(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read a CSV file into a list of dictionaries."""
    import csv
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_csv(path: Union[str, Path], data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    """Write a list of dictionaries to a CSV file."""
    import csv
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not data:
        # Create empty file with headers if provided, otherwise just empty file
        with open(path, 'w', encoding='utf-8') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def read_text(path: Union[str, Path]) -> str:
    """Read a text file and return its contents."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_text(path: Union[str, Path], content: str) -> None:
    """Write content to a text file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def file_exists(path: Union[str, Path]) -> bool:
    """Check if a file exists."""
    return Path(path).exists()

def ensure_file_directory(path: Union[str, Path]) -> Path:
    """Ensure the directory for a file path exists."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator

def validate_required_keys(data: Dict[str, Any], required_keys: List[str]) -> None:
    """Validate that a dictionary contains all required keys."""
    missing = [key for key in required_keys if key not in data]
    if missing:
        raise ValueError(f"Missing required keys: {missing}")

def log_execution_time(func):
    """Decorator to log the execution time of a function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        logger.info(f"Function '{func.__name__}' executed in {elapsed:.4f} seconds")
        return result
    return wrapper
