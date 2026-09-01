"""
I/O Helpers for the llmXive agriculture optimization pipeline.
Provides strict CSV/Parquet I/O, checksum verification, and logging utilities.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

import pandas as pd
import yaml


class FatalError(Exception):
    """Raised when a non-recoverable error occurs (e.g., missing credentials)."""
    pass


class IntegrityError(Exception):
    """Raised when file integrity checks fail."""
    pass


def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger with the given name and level.

    Args:
        name: Name of the logger (usually __name__).
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Configured logger instance.

    Raises:
        ValueError: If the provided level is invalid.
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    level_upper = level.upper()
    if level_upper not in valid_levels:
        raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level_upper))

    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level_upper))
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot compute hash: file not found at {path}")

    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def read_csv_strict(file_path: Union[str, Path], expected_columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Read a CSV file strictly, verifying existence and optionally column schema.

    Args:
        file_path: Path to the CSV file.
        expected_columns: Optional list of required column names.

    Returns:
        DataFrame containing the CSV data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If expected columns are missing.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(path)

    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing required columns: {missing}")

    return df


def write_csv_strict(df: pd.DataFrame, file_path: Union[str, Path]) -> str:
    """
    Write a DataFrame to CSV strictly, creating parent directories if needed.

    Args:
        df: DataFrame to write.
        file_path: Destination path.

    Returns:
        The absolute path of the written file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return str(path)


def read_parquet_strict(file_path: Union[str, Path]) -> pd.DataFrame:
    """Read a Parquet file strictly."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {path}")
    return pd.read_parquet(path)


def write_parquet_strict(df: pd.DataFrame, file_path: Union[str, Path]) -> str:
    """Write a DataFrame to Parquet strictly."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return str(path)


def load_json_strict(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a JSON file strictly."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_strict(data: Dict[str, Any], file_path: Union[str, Path]) -> str:
    """Write a dictionary to JSON strictly."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    return str(path)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
