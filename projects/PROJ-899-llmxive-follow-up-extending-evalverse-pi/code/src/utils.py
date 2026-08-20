import logging
import os
import sys
import json
import csv
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.config import get_project_root, get_data_root

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Setup basic logging configuration."""
    logging.basicConfig(level=log_level, format=LOG_FORMAT)
    return logging.getLogger(__name__)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def ensure_directories(base_dir: Optional[str] = None) -> None:
    """Ensure required directories exist."""
    if base_dir is None:
        base_dir = get_data_root()
    
    dirs = [
        os.path.join(base_dir, "raw"),
        os.path.join(base_dir, "processed"),
        os.path.join(base_dir, "results"),
        os.path.join(get_project_root(), "state"),
        os.path.join(get_project_root(), "reports"),
        os.path.join(get_project_root(), "figures")
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def write_json(path: str, data: Any) -> None:
    """Write data to a JSON file."""
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def read_json(path: str) -> Any:
    """Read data from a JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_csv(path: str, data: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    """Write a list of dicts to a CSV file."""
    if not data:
        # Write empty file with headers if possible
        with open(path, 'w', newline='', encoding='utf-8') as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            else:
                f.write("")
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def read_csv(path: str) -> List[Dict[str, Any]]:
    """Read a CSV file into a list of dicts."""
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_delete(path: str) -> None:
    """Safely delete a file if it exists."""
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Could not delete {path}: {e}")

def handle_error(e: Exception) -> None:
    """Handle error logging."""
    logger = get_logger()
    logger.error(f"Error: {e}", exc_info=True)
    raise e

def validate_file_exists(path: str) -> bool:
    """Check if a file exists."""
    return os.path.isfile(path)

def get_timestamp_filename(prefix: str, ext: str = ".txt") -> str:
    """Generate a filename with a timestamp."""
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}{ext}"

def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"
