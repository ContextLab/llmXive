import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import yaml

logger = logging.getLogger(__name__)

class FatalError(Exception):
    """Exception raised for fatal errors that should stop execution."""
    pass

class IntegrityError(Exception):
    """Exception raised for data integrity issues."""
    pass

def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the application."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def read_csv_strict(file_path: Path) -> pd.DataFrame:
    """Read a CSV file strictly, raising errors on issues."""
    if not file_path.exists():
        raise FatalError(f"File not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise FatalError(f"Error reading CSV {file_path}: {e}")

def write_csv_strict(df: pd.DataFrame, file_path: Path) -> None:
    """Write a DataFrame to CSV strictly."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_csv(file_path, index=False)
    except Exception as e:
        raise FatalError(f"Error writing CSV {file_path}: {e}")

def read_parquet_strict(file_path: Path) -> pd.DataFrame:
    """Read a Parquet file strictly."""
    if not file_path.exists():
        raise FatalError(f"File not found: {file_path}")
    
    try:
        df = pd.read_parquet(file_path)
        return df
    except Exception as e:
        raise FatalError(f"Error reading Parquet {file_path}: {e}")

def write_parquet_strict(df: pd.DataFrame, file_path: Path) -> None:
    """Write a DataFrame to Parquet strictly."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(file_path, index=False)
    except Exception as e:
        raise FatalError(f"Error writing Parquet {file_path}: {e}")

def load_json_strict(file_path: Path) -> Dict[str, Any]:
    """Load a JSON file strictly."""
    if not file_path.exists():
        raise FatalError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise FatalError(f"Error reading JSON {file_path}: {e}")

def write_json_strict(data: Dict[str, Any], file_path: Path) -> None:
    """Write data to a JSON file strictly."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        raise FatalError(f"Error writing JSON {file_path}: {e}")

def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load a YAML file."""
    if not file_path.exists():
        raise FatalError(f"File not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise FatalError(f"Error reading YAML {file_path}: {e}")
