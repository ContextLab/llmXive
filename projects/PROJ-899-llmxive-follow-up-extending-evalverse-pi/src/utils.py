"""
Utility functions for logging, error handling, and file I/O.
"""
import logging
import os
import sys
import json
import csv
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def ensure_directories(*paths: Path) -> None:
    """Ensure directories exist."""
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)

def write_json(data: Dict[str, Any], path: Path) -> None:
    """Write data to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def read_json(path: Path) -> Optional[Dict[str, Any]]:
    """Read data from JSON file."""
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)

def write_csv(data: List[Dict[str, Any]], path: Path) -> None:
    """Write data to CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not data:
        return
    
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

def read_csv(path: Path) -> List[Dict[str, Any]]:
    """Read data from CSV file."""
    if not path.exists():
        return []
    with open(path, "r") as f:
        return list(csv.DictReader(f))

def safe_delete(path: Path) -> bool:
    """Safely delete a file or directory."""
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        logging.error(f"Failed to delete {path}: {e}")
        return False

def handle_error(error: Exception, context: str = "") -> None:
    """Handle and log an error."""
    logging.error(f"{context}: {str(error)}", exc_info=True)

def validate_file_exists(path: Path, description: str = "file") -> bool:
    """Validate that a file exists."""
    if not path.exists():
        logging.error(f"{description} not found: {path}")
        return False
    return True

def get_timestamp_filename(prefix: str = "output", extension: str = ".csv") -> str:
    """Generate a filename with timestamp."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}{extension}"

def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
