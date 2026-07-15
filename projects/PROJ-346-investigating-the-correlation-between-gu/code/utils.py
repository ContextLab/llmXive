import logging
import sys
import os
import time
import json
import hashlib
import pandas as pd
import numpy as np
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def get_project_root_path() -> Path:
    """Returns the project root path."""
    return Path(__file__).resolve().parent.parent

def get_code_path() -> Path:
    """Returns the code directory path."""
    return get_project_root_path() / "code"

def get_data_path() -> Path:
    """Returns the data directory path."""
    return get_project_root_path() / "data"

def get_data_raw_path() -> Path:
    """Returns the raw data directory path."""
    return get_data_path() / "raw"

def get_data_processed_path() -> Path:
    """Returns the processed data directory path."""
    return get_data_path() / "processed"

def get_data_qc_path() -> Path:
    """Returns the QC data directory path."""
    return get_data_path() / "qc"

def get_specs_path() -> Path:
    """Returns the specs directory path."""
    return get_project_root_path() / "specs"

def get_contracts_path() -> Path:
    """Returns the contracts directory path."""
    return get_project_root_path() / "contracts"

def get_figures_path() -> Path:
    """Returns the figures directory path."""
    return get_project_root_path() / "figures"

def ensure_directory(path: Path) -> None:
    """Ensures the directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str) -> logging.Logger:
    """Sets up a logger for the given name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def get_logger(name: str) -> logging.Logger:
    """Gets or creates a logger."""
    return setup_logger(name)

def write_json_log(path: Path, data: Dict[str, Any]) -> None:
    """Writes data to a JSON log file."""
    ensure_directory(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_json_log(path: Path) -> Dict[str, Any]:
    """Reads data from a JSON log file."""
    with open(path, 'r') as f:
        return json.load(f)

def validate_dataframe_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """Validates that a DataFrame has required columns."""
    return all(col in df.columns for col in required_columns)

def sanitize_url(url: str) -> str:
    """Sanitizes a URL string."""
    # Basic sanitization to prevent injection
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Invalid URL scheme")
    return url

def sanitize_file_path(path: str) -> str:
    """Sanitizes a file path string."""
    # Prevent directory traversal
    if '..' in path:
        raise ValueError("Invalid file path")
    return path

def get_retry_session() -> requests.Session:
    """
    Creates a requests session with retry logic.
    This is a helper for load_data_with_retry.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_data_with_retry(url: str, timeout: int = 30) -> pd.DataFrame:
    """
    Loads data from a URL with retry logic (up to 3 attempts with exponential backoff).
    This implements T006 requirements.
    """
    session = get_retry_session()
    try:
        response = session.get(sanitize_url(url), timeout=timeout)
        response.raise_for_status()
        # Assume CSV for simplicity, can be extended
        return pd.read_csv(pd.io.common.StringIO(response.text))
    except Exception as e:
        raise RuntimeError(f"Failed to load data from {url} after retries: {e}")

def compute_file_hash(path: Path) -> str:
    """Computes the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def filter_low_read_samples(df: pd.DataFrame, threshold: int = 10000) -> pd.DataFrame:
    """
    Filters out samples with total reads below the threshold.
    Implements FR-001 filter: <10k reads.
    """
    if 'total_reads' not in df.columns:
        logging.warning("Column 'total_reads' not found in DataFrame. Skipping read depth filter.")
        return df
    return df[df['total_reads'] >= threshold]

def filter_rare_taxa(df: pd.DataFrame, threshold: float = 0.001) -> pd.DataFrame:
    """
    Filters out taxa with abundance below the threshold.
    Implements FR-001 filter: <0.1% abundance.
    """
    if 'abundance' not in df.columns:
        logging.warning("Column 'abundance' not found in DataFrame. Skipping rare taxa filter.")
        return df
    return df[df['abundance'] >= threshold]

def get_age_group(age: float) -> str:
    """Categorizes age into groups."""
    if age < 40:
        return "<40"
    elif age < 60:
        return "40-<60"
    else:
        return "≥60"
