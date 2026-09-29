import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import yaml

class FatalError(Exception):
    """Raised when a critical failure occurs that prevents pipeline execution."""
    pass

class IntegrityError(Exception):
    """Raised when data integrity checks fail (e.g., checksum mismatch)."""
    pass

def setup_logging(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up logging for a module.
    
    Args:
        name: Module name (e.g., "synthetic_generator")
        level: Log level string (e.g., "INFO", "DEBUG"). Defaults to "INFO".
    
    Returns:
        Configured logger instance.
    
    Raises:
        ValueError: If the log level is invalid.
    """
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    if level is None:
        level = "INFO"
    
    upper_level = level.upper()
    if upper_level not in log_level_map:
        raise ValueError(f"Invalid log level: {level}. Must be one of {list(log_level_map.keys())}")
    
    numeric_level = log_level_map[upper_level]
    
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def read_csv_strict(file_path: Path) -> pd.DataFrame:
    """Read CSV with strict error handling."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        raise IntegrityError(f"Failed to read CSV {file_path}: {e}")

def write_csv_strict(df: pd.DataFrame, file_path: Path) -> None:
    """Write DataFrame to CSV with strict error handling."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(file_path, index=False)
    except Exception as e:
        raise IOError(f"Failed to write CSV {file_path}: {e}")

def read_parquet_strict(file_path: Path) -> pd.DataFrame:
    """Read Parquet with strict error handling."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        return pd.read_parquet(file_path)
    except Exception as e:
        raise IntegrityError(f"Failed to read Parquet {file_path}: {e}")

def write_parquet_strict(df: pd.DataFrame, file_path: Path) -> None:
    """Write DataFrame to Parquet with strict error handling."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(file_path, index=False)
    except Exception as e:
        raise IOError(f"Failed to write Parquet {file_path}: {e}")

def load_json_strict(file_path: Path) -> Dict[str, Any]:
    """Load JSON with strict error handling."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise IntegrityError(f"Failed to parse JSON {file_path}: {e}")

def write_json_strict(data: Dict[str, Any], file_path: Path) -> None:
    """Write dictionary to JSON with strict error handling."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise IOError(f"Failed to write JSON {file_path}: {e}")

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load YAML file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        with open(file_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise IntegrityError(f"Failed to load YAML {file_path}: {e}")
