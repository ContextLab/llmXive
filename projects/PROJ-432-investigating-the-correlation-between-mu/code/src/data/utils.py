"""
Utility functions for data processing, logging, checksums, and date parsing.
"""
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.

    Args:
        name: Logger name (usually __name__).
        log_file: Optional path to log file.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def calculate_file_checksum(
    file_path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).
        chunk_size: Size of chunks to read.

    Returns:
        Hexadecimal checksum string.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def parse_date_string(
    date_str: str,
    formats: Optional[list] = None,
) -> datetime:
    """
    Parse a date string using multiple possible formats.

    Args:
        date_str: The date string to parse.
        formats: List of date formats to try. Defaults to common formats.

    Returns:
        Parsed datetime object.

    Raises:
        ValueError: If no format matches the input string.
    """
    if formats is None:
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y-%m-%d %H:%M:%S",
            "%Y/%m/%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    raise ValueError(
        f"Unable to parse date string '{date_str}' with provided formats: {formats}"
    )


def normalize_date_column(
    df: pd.DataFrame,
    date_column: str = "date",
    target_format: str = "%Y-%m-%d",
) -> pd.DataFrame:
    """
    Normalize a date column in a DataFrame to a standard format.

    Args:
        df: Input DataFrame.
        date_column: Name of the date column.
        target_format: Target date format string.

    Returns:
        DataFrame with normalized date column.

    Raises:
        ValueError: If the date column is missing or contains invalid dates.
    """
    if date_column not in df.columns:
        raise ValueError(f"Date column '{date_column}' not found in DataFrame")

    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors="raise")
    df[date_column] = df[date_column].dt.strftime(target_format)

    return df


def write_json_log(
    log_file: Union[str, Path],
    entry: Dict[str, Any],
    append: bool = True,
) -> None:
    """
    Write a JSON entry to a log file. Supports appending to a JSON array.

    Args:
        log_file: Path to the log file.
        entry: Dictionary entry to log.
        append: If True, append to existing JSON array; otherwise overwrite.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entries = []
    if append and log_path.exists():
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    entries = json.loads(content)
                    if not isinstance(entries, list):
                        entries = [entries]
        except (json.JSONDecodeError, IOError):
            entries = []

    entries.append(entry)

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, default=str)


def validate_date_range(
    df: pd.DataFrame,
    date_column: str = "date",
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
) -> bool:
    """
    Validate that all dates in a DataFrame fall within a specified range.

    Args:
        df: Input DataFrame.
        date_column: Name of the date column.
        min_date: Minimum allowed date (YYYY-MM-DD).
        max_date: Maximum allowed date (YYYY-MM-DD).

    Returns:
        True if all dates are within range, False otherwise.
    """
    if date_column not in df.columns:
        return False

    dates = pd.to_datetime(df[date_column], errors="coerce")

    if min_date:
        min_dt = pd.to_datetime(min_date)
        if (dates < min_dt).any():
            return False

    if max_date:
        max_dt = pd.to_datetime(max_date)
        if (dates > max_dt).any():
            return False

    return True