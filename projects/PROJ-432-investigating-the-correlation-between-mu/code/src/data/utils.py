"""
Utility functions for data processing, logging, checksums, and date handling.

This module provides shared utilities used across the data ingestion and 
preprocessing pipeline.
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd


def setup_logger(
    name: str,
    log_file: Optional[Union[str, Path]] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        log_file: Path to log file. If None, only console output is used.
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def calculate_file_checksum(
    file_path: Union[str, Path], algorithm: str = "sha256"
) -> str:
    """
    Calculate the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hexadecimal checksum string
    
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        hash_obj = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    
    return hash_obj.hexdigest()


def parse_date_string(
    date_str: str, formats: Optional[List[str]] = None
) -> datetime:
    """
    Parse a date string into a datetime object using multiple formats.
    
    Args:
        date_str: Date string to parse
        formats: List of format strings to try. If None, uses common formats.
    
    Returns:
        Parsed datetime object
    
    Raises:
        ValueError: If the date string cannot be parsed with any format
    """
    if formats is None:
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
        ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Unable to parse date string: {date_str}")


def normalize_date_column(
    df: pd.DataFrame,
    date_column: str,
    output_column: Optional[str] = None,
) -> pd.DataFrame:
    """
    Convert a date column in a DataFrame to datetime64[ns] type.
    
    Args:
        df: Input DataFrame
        date_column: Name of the column to normalize
        output_column: Name of the output column. If None, overwrites date_column.
    
    Returns:
        DataFrame with normalized date column
    
    Raises:
        ValueError: If the column does not exist or cannot be converted
    """
    if date_column not in df.columns:
        raise ValueError(f"Column '{date_column}' not found in DataFrame")
    
    result_df = df.copy()
    target_col = output_column if output_column else date_column
    
    try:
        result_df[target_col] = pd.to_datetime(result_df[date_column])
    except Exception as e:
        raise ValueError(
            f"Failed to convert column '{date_column}' to datetime: {e}"
        ) from e
    
    return result_df


def write_json_log(
    log_file: Union[str, Path],
    entries: List[Dict[str, Any]],
    mode: str = "a",
) -> None:
    """
    Write a list of log entries to a JSON file.
    
    Args:
        log_file: Path to the log file
        entries: List of dictionaries to write as JSON
        mode: File mode ('w' for overwrite, 'a' for append)
    
    Note:
        If mode is 'a' and the file exists, entries are appended as a 
        JSON array. If the file is empty or doesn't exist, a new array is created.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing entries if appending
    existing_entries: List[Dict[str, Any]] = []
    if mode == "a" and log_path.exists() and log_path.stat().st_size > 0:
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing_entries = json.loads(content)
                    if not isinstance(existing_entries, list):
                        existing_entries = [existing_entries]
        except json.JSONDecodeError:
            # If file is corrupted, start fresh
            existing_entries = []
    
    # Combine entries
    all_entries = existing_entries + entries
    
    # Write back
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, indent=2)


def validate_date_range(
    start_date: Union[str, datetime],
    end_date: Union[str, datetime],
    min_days: Optional[int] = None,
    max_days: Optional[int] = None,
) -> bool:
    """
    Validate that a date range is within specified bounds.
    
    Args:
        start_date: Start date (string or datetime)
        end_date: End date (string or datetime)
        min_days: Minimum number of days required in the range
        max_days: Maximum number of days allowed in the range
    
    Returns:
        True if the range is valid, False otherwise
    
    Raises:
        ValueError: If dates cannot be parsed
    """
    # Parse dates if strings
    if isinstance(start_date, str):
        start_date = parse_date_string(start_date)
    if isinstance(end_date, str):
        end_date = parse_date_string(end_date)
    
    if start_date > end_date:
        return False
    
    delta = (end_date - start_date).days
    
    if min_days is not None and delta < min_days:
        return False
    
    if max_days is not None and delta > max_days:
        return False
    
    return True