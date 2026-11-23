import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

import pandas as pd


def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger with console and optional file output.

    Args:
        name: The name of the logger.
        log_file: Optional path to a log file. If None, only console output is used.
        level: Logging level (default: INFO).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if they already exist (useful for re-running in same session)
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def calculate_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        Hexadecimal digest of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


def parse_date_string(date_str: str, date_format: str = '%Y-%m-%d') -> datetime:
    """
    Parse a date string into a datetime object.

    Args:
        date_str: The date string to parse.
        date_format: The expected format of the date string (default: '%Y-%m-%d').

    Returns:
        A datetime object.

    Raises:
        ValueError: If the string cannot be parsed with the given format.
    """
    try:
        return datetime.strptime(date_str, date_format)
    except ValueError:
        raise ValueError(f"Could not parse date string '{date_str}' with format '{date_format}'")


def normalize_date_column(df: pd.DataFrame, date_column: str = 'date', target_format: str = '%Y-%m-%d') -> pd.DataFrame:
    """
    Ensure a date column in a DataFrame is in datetime format and optionally formatted as a string.

    Args:
        df: The input DataFrame.
        date_column: The name of the column containing dates.
        target_format: The format string for output (if string conversion is needed).

    Returns:
        The DataFrame with the date column converted to datetime.
    """
    if date_column not in df.columns:
        raise KeyError(f"Date column '{date_column}' not found in DataFrame.")

    # Convert to datetime, coercing errors to NaT
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')

    # Check for any NaT values that couldn't be parsed
    if df[date_column].isna().any():
        raise ValueError(f"Failed to parse some values in column '{date_column}'. Check input format.")

    return df


def write_json_log(log_path: Union[str, Path], data: List[Dict[str, Any]], mode: str = 'append') -> None:
    """
    Write a list of log entries to a JSON file.

    Args:
        log_path: Path to the log file.
        data: List of dictionaries to write.
        mode: 'append' or 'overwrite'. If 'append', existing entries are loaded and merged.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    existing_data = []
    if mode == 'append' and log_path.exists():
        try:
            with open(log_path, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    if not isinstance(existing_data, list):
                        existing_data = []
        except (json.JSONDecodeError, IOError):
            existing_data = []

    combined_data = existing_data + data

    with open(log_path, 'w') as f:
        json.dump(combined_data, f, indent=2, default=str)


def validate_date_range(df: pd.DataFrame, date_column: str = 'date', min_date: Optional[str] = None, max_date: Optional[str] = None) -> bool:
    """
    Validate that dates in a DataFrame fall within a specified range.

    Args:
        df: The input DataFrame.
        date_column: The name of the date column.
        min_date: Optional minimum date string (YYYY-MM-DD).
        max_date: Optional maximum date string (YYYY-MM-DD).

    Returns:
        True if all dates are within the range, False otherwise.
    """
    if date_column not in df.columns:
        raise KeyError(f"Date column '{date_column}' not found in DataFrame.")

    dates = pd.to_datetime(df[date_column])
    min_dt = pd.to_datetime(min_date) if min_date else None
    max_dt = pd.to_datetime(max_date) if max_date else None

    if min_dt is not None and (dates < min_dt).any():
        return False
    if max_dt is not None and (dates > max_dt).any():
        return False

    return True

# Import sys here to ensure it's available for the logger setup
import sys