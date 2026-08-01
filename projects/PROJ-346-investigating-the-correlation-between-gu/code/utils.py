import logging
import sys
import os
import time
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
READ_THRESHOLD = 10000
ABUNDANCE_FILTER = 0.001
AGE_STRATA = {
    "young": "<40",
    "middle": "40-60",
    "old": ">=60"
}

def get_project_root_path() -> Path:
    """Return the project root directory."""
    # Assuming the code is run from the project root or code directory
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def get_code_path() -> Path:
    """Return the code directory path."""
    return get_project_root_path() / "code"

def get_data_path() -> Path:
    """Return the data directory path."""
    return get_project_root_path() / "data"

def get_data_raw_path() -> Path:
    """Return the raw data directory path."""
    return get_data_path() / "raw"

def get_data_processed_path() -> Path:
    """Return the processed data directory path."""
    return get_data_path() / "processed"

def get_data_qc_path() -> Path:
    """Return the QC data directory path."""
    return get_data_path() / "qc"

def get_specs_path() -> Path:
    """Return the specs directory path."""
    return get_project_root_path() / "specs"

def get_contracts_path() -> Path:
    """Return the contracts directory path."""
    return get_project_root_path() / "contracts"

def get_figures_path() -> Path:
    """Return the figures directory path."""
    return get_project_root_path() / "figures"

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up and return a logger with standard formatting."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one."""
    return logging.getLogger(name)

def write_json_log(data: Dict[str, Any], file_path: Path) -> None:
    """Write a dictionary to a JSON file."""
    ensure_directory(file_path.parent)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def read_json_log(file_path: Path) -> Dict[str, Any]:
    """Read a JSON file and return its contents."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_dataframe_columns(df, required_columns: list) -> bool:
    """Validate that a DataFrame contains all required columns."""
    return all(col in df.columns for col in required_columns)

def sanitize_url(url: str) -> str:
    """Sanitize a URL string."""
    # Basic sanitization to prevent injection
    allowed_schemes = ['http', 'https']
    if not url.startswith(tuple(f'{s}://' for s in allowed_schemes)):
        raise ValueError(f"Invalid URL scheme: {url}")
    return url

def sanitize_file_path(path: str) -> str:
    """Sanitize a file path string."""
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        path = path.replace(char, '')
    return path

def get_retry_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_data_with_retry(url: str, timeout: int = 30) -> bytes:
    """Load data from a URL with retry logic."""
    session = get_retry_session()
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        logger = get_logger("utils")
        logger.error(f"Failed to load data from {url} after retries: {e}")
        raise

def compute_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """Compute the hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def filter_low_read_samples(df, read_column: str, threshold: int = READ_THRESHOLD):
    """Filter out samples with read counts below threshold."""
    return df[df[read_column] >= threshold]

def filter_rare_taxa(df, abundance_column: str, threshold: float = ABUNDANCE_FILTER):
    """Filter out taxa with abundance below threshold."""
    return df[df[abundance_column] >= threshold]

def get_age_group(age: float) -> str:
    """Categorize age into predefined strata."""
    if age < 40:
        return AGE_STRATA["young"]
    elif age < 60:
        return AGE_STRATA["middle"]
    else:
        return AGE_STRATA["old"]