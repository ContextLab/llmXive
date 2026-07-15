import logging
import csv
import os
from typing import Dict, Any, List

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Setup logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    if not logger.handlers:
        logger.addHandler(ch)
    
    return logger

def write_csv_row(filepath: str, row: Dict[str, Any], fieldnames: List[str]) -> None:
    """Write a single row to CSV, creating file if necessary."""
    file_exists = os.path.exists(filepath)
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def format_error(error: Exception) -> str:
    """Format exception for logging."""
    return f"{type(error).__name__}: {str(error)}"
