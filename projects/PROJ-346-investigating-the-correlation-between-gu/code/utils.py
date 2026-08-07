import logging
import sys
import os
import time
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration for project paths
# We assume the project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
FIGURES_DIR = PROJECT_ROOT / "figures"
SPECS_DIR = PROJECT_ROOT / "specs"

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with a specific name and level."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def get_project_root_path() -> Path:
    """Return the project root path."""
    return PROJECT_ROOT

def get_code_path() -> Path:
    """Return the code directory path."""
    return CODE_DIR

def get_data_path(sub_dir: Optional[str] = None) -> Path:
    """Return the data directory path."""
    if sub_dir:
        return DATA_DIR / sub_dir
    return DATA_DIR

def get_data_raw_path(filename: Optional[str] = None) -> Path:
    """Return the raw data directory path or a specific file path."""
    raw_dir = DATA_DIR / "raw"
    if filename:
        return raw_dir / filename
    return raw_dir

def get_data_processed_path(root: Optional[Path] = None, sub_dir: Optional[str] = None) -> Path:
    """
    Return the processed data directory path.
    Handles multiple calling conventions:
    1. get_data_processed_path()
    2. get_data_processed_path(root)
    3. get_data_processed_path(root, sub_dir)
    """
    # Determine base processed directory
    base_processed = DATA_DIR / "processed"
    
    # Handle arguments flexibly
    if root is not None:
        # If root is provided, use it as the base for the processed dir
        # But we still want to respect the global DATA_DIR structure usually
        # However, to support the signature (root, sub_dir), we treat 'root' as the parent of 'processed'
        # if it looks like a path, otherwise treat it as a sub_dir if sub_dir is None
        if isinstance(root, str) and not Path(root).is_absolute():
            # Likely passed as a sub_dir by mistake or convention
            if sub_dir is None:
                return base_processed / root
            else:
                return base_processed / root / sub_dir
        elif isinstance(root, Path):
            if sub_dir:
                return root / "processed" / sub_dir
            else:
                return root / "processed"
        else:
            # Fallback to default if type is unexpected
            pass
    
    # Default behavior: return base_processed or base_processed/sub_dir
    if sub_dir:
        return base_processed / sub_dir
    return base_processed

def get_data_qc_path(filename: Optional[str] = None) -> Path:
    """Return the QC data directory path or a specific file path."""
    qc_dir = DATA_DIR / "qc"
    if filename:
        return qc_dir / filename
    return qc_dir

def get_specs_path() -> Path:
    """Return the specs directory path."""
    return SPECS_DIR

def get_contracts_path() -> Path:
    """Return the contracts directory path."""
    return CONTRACTS_DIR

def get_figures_path() -> Path:
    """Return the figures directory path."""
    return FIGURES_DIR

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

def write_json_log(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """Write a dictionary to a JSON file."""
    p = Path(path)
    ensure_directory(p.parent)
    with open(p, 'w') as f:
        json.dump(data, f, indent=2)

def read_json_log(path: Union[str, Path]) -> Dict[str, Any]:
    """Read a JSON file into a dictionary."""
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, 'r') as f:
        return json.load(f)

def compute_file_hash(path: Union[str, Path]) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

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

def load_data_with_retry(url: str, session: Optional[requests.Session] = None) -> Optional[requests.Response]:
    """Load data from a URL with retry logic."""
    if session is None:
        session = get_retry_session()
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response
    except Exception as e:
        logger = setup_logger("utils")
        logger.error(f"Failed to load data from {url}: {e}")
        return None

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return setup_logger(name)

# Utility functions for filtering (from T004)
def filter_low_read_samples(df: pd.DataFrame, threshold: int = 10000) -> pd.DataFrame:
    """Filter samples with read counts below threshold."""
    if 'read_count' in df.columns:
        return df[df['read_count'] >= threshold]
    return df

def filter_rare_taxa(df: pd.DataFrame, threshold: float = 0.001) -> pd.DataFrame:
    """Filter taxa with relative abundance below threshold."""
    if 'relative_abundance' in df.columns:
        return df[df['relative_abundance'] >= threshold]
    return df

def get_age_group(age: float) -> str:
    """Categorize age into groups."""
    if age < 40:
        return "<40"
    elif age < 60:
        return "40-<60"
    else:
        return "≥60"

def sanitize_url(url: str) -> str:
    """Sanitize a URL string."""
    # Basic sanitization
    return url.strip()

def sanitize_file_path(path: str) -> str:
    """Sanitize a file path string."""
    # Basic sanitization
    return path.strip()

# Import pandas here to avoid circular imports if this file is imported before pandas is available in some contexts
# However, since this is a utility file, we assume pandas is available in the environment.
# To be safe, we can import inside functions if needed, but for type hints we need it at top level if used in signatures.
# We will use type: ignore for pandas if it's not strictly needed in signatures.
import pandas as pd