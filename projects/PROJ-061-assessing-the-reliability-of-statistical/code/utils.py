import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def compute_file_checksum(file_path: Union[str, Path]) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_file_directory(file_path: Union[str, Path]) -> None:
    """Ensure the directory for a file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def safe_json_load(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Safely load a JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}")

def safe_json_save(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Safely save data to a JSON file."""
    ensure_file_directory(file_path)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def record_checksums(checksums: Dict[str, str], file_path: Union[str, Path]) -> None:
    """Record checksums to a JSON file."""
    existing = safe_json_load(file_path)
    existing.update(checksums)
    safe_json_save(existing, file_path)

def handle_missing_values(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """
    Perform listwise deletion (drop rows with any missing values) on the input DataFrame.
    
    This implements the logic required for T016:
    - Drops any row containing at least one NaN.
    - Logs the number of dropped rows if a logger is provided.
    - Returns the cleaned DataFrame.
    """
    if logger is None:
        logger = logging.getLogger("llmXive")

    original_shape = df.shape
    # Drop rows with any missing values (listwise deletion)
    cleaned_df = df.dropna()
    cleaned_shape = cleaned_df.shape

    dropped_count = original_shape[0] - cleaned_shape[0]
    
    if dropped_count > 0:
        logger.info(f"Listwise deletion: Removed {dropped_count} rows with missing values "
                    f"(Original N={original_shape[0]}, Cleaned N={cleaned_shape[0]})")
    else:
        logger.info("No missing values found; no rows dropped.")

    return cleaned_df
