"""
Utility functions for logging, file I/O, and error handling.
"""
import logging
import os
import sys
import json
import csv
from pathlib import Path
from typing import Optional, Any, Dict, List, Union
from datetime import datetime

# Global logger instance
_logger_instance: Optional[logging.Logger] = None

def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger("llmXive")
        _logger_instance.setLevel(logging.INFO)
        if not _logger_instance.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger_instance.addHandler(handler)
    return logging.getLogger(name)

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """Setup logging configuration."""
    logger = get_logger(__name__)
    logger.setLevel(level)
    
    if log_file:
        ensure_directories([log_file.parent])
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(file_handler)

def ensure_directories(paths: List[Union[str, Path]]) -> None:
    """Ensure all given paths exist as directories."""
    for path in paths:
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)

def write_json(file_path: Union[str, Path], data: Any) -> None:
    """Write data to a JSON file."""
    p = Path(file_path)
    ensure_directories([p.parent])
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Read data from a JSON file."""
    p = Path(file_path)
    if not p.exists():
        return {}
    with open(p, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_csv(file_path: Union[str, Path], data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    """Write a list of dictionaries to a CSV file."""
    p = Path(file_path)
    ensure_directories([p.parent])
    
    if not data:
        # Write empty file with headers if provided
        with open(p, 'w', newline='', encoding='utf-8') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(p, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def read_csv(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read a CSV file into a list of dictionaries."""
    p = Path(file_path)
    if not p.exists():
        return []
    
    with open(p, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_delete(file_path: Union[str, Path]) -> bool:
    """Safely delete a file if it exists."""
    p = Path(file_path)
    if p.exists():
        try:
            p.unlink()
            return True
        except Exception as e:
            logger = get_logger(__name__)
            logger.warning(f"Failed to delete {p}: {e}")
            return False
    return False

def handle_error(error: Exception, context: str = "") -> None:
    """Handle an error by logging it and optionally raising."""
    logger = get_logger(__name__)
    logger.error(f"{context}: {str(error)}", exc_info=True)

def validate_file_exists(file_path: Union[str, Path], description: str = "File") -> None:
    """Validate that a file exists, raising an error if not."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(f"{description} not found: {p}")
