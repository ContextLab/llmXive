"""
I/O Helpers: Strict CSV/Parquet I/O, checksum verification, and robust logging setup.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import yaml


class FatalError(Exception):
    """Raised when a critical, non-recoverable error occurs."""
    pass


class IntegrityError(Exception):
    """Raised when data integrity checks (checksums, schema) fail."""
    pass


def setup_logging(name: str, level: str = "INFO") -> logging.Logger:
    """
    Configure and return a logger with the given name and level.
    
    Args:
        name: The name of the logger (typically __name__).
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    
    Returns:
        Configured logging.Logger instance.
    
    Raises:
        ValueError: If the provided log level is invalid.
    """
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    level_upper = level.upper()
    
    if level_upper not in valid_levels:
        raise ValueError(f"Invalid log level: {level}. Must be one of {valid_levels}")
    
    logger = logging.getLogger(name)
    if logger.handlers:
        # Avoid duplicate handlers if called multiple times in same process
        return logger
    
    logger.setLevel(level_upper)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level_upper)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    return logger


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic hash of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).
    
    Returns:
        Hexadecimal hash string.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def read_csv_strict(
    file_path: str,
    expected_columns: Optional[List[str]] = None,
    checksum: Optional[str] = None
) -> pd.DataFrame:
    """
    Read a CSV file with strict validation.
    
    Args:
        file_path: Path to the CSV file.
        expected_columns: Optional list of required column names.
        checksum: Optional expected SHA256 checksum.
    
    Returns:
        Pandas DataFrame.
    
    Raises:
        FileNotFoundError: If file missing.
        IntegrityError: If checksum or column validation fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    if checksum:
        actual_hash = compute_file_hash(file_path)
        if actual_hash != checksum:
            raise IntegrityError(
                f"Checksum mismatch for {file_path}. Expected: {checksum}, Got: {actual_hash}"
            )
    
    df = pd.read_csv(file_path)
    
    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise IntegrityError(
                f"CSV missing required columns: {missing}. Found: {list(df.columns)}"
            )
    
    return df


def write_csv_strict(
    df: pd.DataFrame,
    file_path: str,
    include_index: bool = False
) -> str:
    """
    Write a DataFrame to CSV with strict directory creation.
    
    Args:
        df: DataFrame to write.
        file_path: Output path.
        include_index: Whether to include index in output.
    
    Returns:
        The computed SHA256 hash of the written file.
    
    Raises:
        IOError: If write fails.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(path, index=include_index)
    return compute_file_hash(file_path)


def read_parquet_strict(
    file_path: str,
    expected_columns: Optional[List[str]] = None,
    checksum: Optional[str] = None
) -> pd.DataFrame:
    """
    Read a Parquet file with strict validation.
    
    Args:
        file_path: Path to the Parquet file.
        expected_columns: Optional list of required column names.
        checksum: Optional expected SHA256 checksum.
    
    Returns:
        Pandas DataFrame.
    
    Raises:
        FileNotFoundError: If file missing.
        IntegrityError: If checksum or column validation fails.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Parquet file not found: {file_path}")
    
    if checksum:
        actual_hash = compute_file_hash(file_path)
        if actual_hash != checksum:
            raise IntegrityError(
                f"Checksum mismatch for {file_path}. Expected: {checksum}, Got: {actual_hash}"
            )
    
    df = pd.read_parquet(file_path)
    
    if expected_columns:
        missing = set(expected_columns) - set(df.columns)
        if missing:
            raise IntegrityError(
                f"Parquet missing required columns: {missing}. Found: {list(df.columns)}"
            )
    
    return df


def write_parquet_strict(df: pd.DataFrame, file_path: str) -> str:
    """
    Write a DataFrame to Parquet with strict directory creation.
    
    Args:
        df: DataFrame to write.
        file_path: Output path.
    
    Returns:
        The computed SHA256 hash of the written file.
    
    Raises:
        IOError: If write fails.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(path, index=False)
    return compute_file_hash(file_path)


def load_json_strict(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file strictly.
    
    Args:
        file_path: Path to JSON file.
    
    Returns:
        Parsed JSON object (dict).
    
    Raises:
        FileNotFoundError: If file missing.
        json.JSONDecodeError: If invalid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json_strict(data: Dict[str, Any], file_path: str, indent: int = 2) -> str:
    """
    Write data to JSON with strict directory creation.
    
    Args:
        data: Dictionary to write.
        file_path: Output path.
        indent: JSON indentation level.
    
    Returns:
        The computed SHA256 hash of the written file.
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent)
    
    return compute_file_hash(file_path)


def load_yaml(file_path: str) -> Any:
    """
    Load a YAML file.
    
    Args:
        file_path: Path to YAML file.
    
    Returns:
        Parsed YAML object.
    
    Raises:
        FileNotFoundError: If file missing.
        yaml.YAMLError: If invalid YAML.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)