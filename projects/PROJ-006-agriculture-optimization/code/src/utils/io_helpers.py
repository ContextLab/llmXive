"""
I/O Helper utilities for strict CSV/Parquet I/O and checksum verification.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pandas as pd
import yaml


class FatalError(Exception):
    """Exception raised for fatal errors that should halt execution."""
    pass


class IntegrityError(Exception):
    """Exception raised for data integrity failures (e.g., checksum mismatch)."""
    pass


def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """
    Set up a logger with the given name and level.

    Args:
        name: The name of the logger (typically __name__).
        level: The logging level as a string (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        A configured logger instance.

    Raises:
        ValueError: If the provided level is invalid.
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if level.upper() not in valid_levels:
        raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")

    logger = logging.getLogger(name)
    logger.setLevel(level.upper())

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level.upper())
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        FatalError: If the hash computation fails.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hash computation: {file_path}")

    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        raise FatalError(f"Failed to compute hash for {file_path}: {e}")


def read_csv_strict(file_path: Union[str, Path], expected_columns: Optional[list] = None) -> pd.DataFrame:
    """
    Read a CSV file with strict validation.

    Args:
        file_path: Path to the CSV file.
        expected_columns: Optional list of expected column names.

    Returns:
        DataFrame containing the CSV data.

    Raises:
        FileNotFoundError: If the file does not exist.
        FatalError: If the file cannot be read or validation fails.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise FatalError(f"Failed to read CSV {file_path}: {e}")

    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise FatalError(f"CSV {file_path} missing expected columns: {missing}")

    return df


def write_csv_strict(df: pd.DataFrame, file_path: Union[str, Path], index: bool = False) -> str:
    """
    Write a DataFrame to a CSV file with integrity verification.

    Args:
        df: DataFrame to write.
        file_path: Destination path.
        index: Whether to write the index (default: False).

    Returns:
        The SHA256 hash of the written file.

    Raises:
        FatalError: If the write fails or the file cannot be verified.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_csv(file_path, index=index)
    except Exception as e:
        raise FatalError(f"Failed to write CSV {file_path}: {e}")

    if not file_path.exists():
        raise FatalError(f"CSV write verification failed: {file_path} does not exist.")

    return compute_file_hash(file_path)


def read_parquet_strict(file_path: Union[str, Path], expected_columns: Optional[list] = None) -> pd.DataFrame:
    """
    Read a Parquet file with strict validation.

    Args:
        file_path: Path to the Parquet file.
        expected_columns: Optional list of expected column names.

    Returns:
        DataFrame containing the Parquet data.

    Raises:
        FileNotFoundError: If the file does not exist.
        FatalError: If the file cannot be read or validation fails.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")

    try:
        df = pd.read_parquet(file_path)
    except Exception as e:
        raise FatalError(f"Failed to read Parquet {file_path}: {e}")

    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise FatalError(f"Parquet {file_path} missing expected columns: {missing}")

    return df


def write_parquet_strict(df: pd.DataFrame, file_path: Union[str, Path], index: bool = False) -> str:
    """
    Write a DataFrame to a Parquet file with integrity verification.

    Args:
        df: DataFrame to write.
        file_path: Destination path.
        index: Whether to write the index (default: False).

    Returns:
        The SHA256 hash of the written file.

    Raises:
        FatalError: If the write fails or the file cannot be verified.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_parquet(file_path, index=index)
    except Exception as e:
        raise FatalError(f"Failed to write Parquet {file_path}: {e}")

    if not file_path.exists():
        raise FatalError(f"Parquet write verification failed: {file_path} does not exist.")

    return compute_file_hash(file_path)


def load_json_strict(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file with strict validation.

    Args:
        file_path: Path to the JSON file.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        FatalError: If the file cannot be read or parsed.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FatalError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise FatalError(f"Failed to read JSON {file_path}: {e}")


def write_json_strict(data: Dict[str, Any], file_path: Union[str, Path], indent: int = 2) -> str:
    """
    Write data to a JSON file with integrity verification.

    Args:
        data: Dictionary to write.
        file_path: Destination path.
        indent: Indentation level for pretty printing.

    Returns:
        The SHA256 hash of the written file.

    Raises:
        FatalError: If the write fails or the file cannot be verified.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        raise FatalError(f"Failed to write JSON {file_path}: {e}")

    if not file_path.exists():
        raise FatalError(f"JSON write verification failed: {file_path} does not exist.")

    return compute_file_hash(file_path)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Parsed YAML data.

    Raises:
        FileNotFoundError: If the file does not exist.
        FatalError: If the file cannot be read or parsed.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise FatalError(f"Invalid YAML in {file_path}: {e}")
    except Exception as e:
        raise FatalError(f"Failed to read YAML {file_path}: {e}")