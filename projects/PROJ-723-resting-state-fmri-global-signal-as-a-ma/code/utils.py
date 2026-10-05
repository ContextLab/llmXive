"""
Utility functions for logging, file I/O, and error handling.
"""
import logging
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Create and return a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def setup_logging(log_file: Optional[str] = None) -> None:
    """Configure logging to file and/or console."""
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

def read_json(filepath: str) -> Dict:
    """Read a JSON file and return a dictionary."""
    with open(filepath, 'r') as f:
        return json.load(f)

def write_json(filepath: str, data: Dict) -> None:
    """Write a dictionary to a JSON file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def read_csv(filepath: str) -> pd.DataFrame:
    """Read a CSV file and return a DataFrame."""
    return pd.read_csv(filepath)

def write_csv(filepath: str, df: pd.DataFrame) -> None:
    """Write a DataFrame to a CSV file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)

def read_text(filepath: str) -> str:
    """Read a text file and return its contents."""
    with open(filepath, 'r') as f:
        return f.read()

def write_text(filepath: str, content: str) -> None:
    """Write a string to a text file."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w') as f:
        f.write(content)

def file_exists(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()

def ensure_file_directory(filepath: str) -> None:
    """Ensure the directory for a file exists."""
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if b == 0:
        return default
    return a / b

def validate_required_keys(data: Dict, required_keys: List[str]) -> bool:
    """Check if all required keys are present in a dictionary."""
    return all(key in data for key in required_keys)

def log_execution_time(start_time: float, end_time: float, task_name: str) -> None:
    """Log the execution time of a task."""
    duration = end_time - start_time
    logger = get_logger()
    logger.info(f"{task_name} executed in {duration:.2f} seconds")
