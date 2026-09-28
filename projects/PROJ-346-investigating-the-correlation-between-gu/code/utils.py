import logging
import sys
import os
import time
import json
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any

# Setup basic logging configuration if not already done
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def get_project_root_path() -> Path:
    """Return the project root path."""
    # Assuming the project root is the parent of the 'code' directory
    # If running from code/, go up one level. If running from root, stay.
    current = Path(__file__).resolve()
    if current.name == 'utils.py':
        return current.parent.parent
    return current.parent

def get_code_path() -> Path:
    """Return the code directory path."""
    return get_project_root_path() / "code"

def get_data_path() -> Path:
    """Return the data directory path."""
    return get_project_root_path() / "data"

def get_data_raw_path() -> Path:
    """Return the raw data directory path."""
    return get_data_path() / "raw"

def get_data_processed_path(root: Optional[Path] = None, sub_dir: Optional[str] = None) -> Path:
    """
    Return the processed data directory path.
    Handles flexible calling patterns:
    - get_data_processed_path()
    - get_data_processed_path(root)
    - get_data_processed_path(root, sub_dir)
    """
    if root is None:
        base = get_data_path()
    else:
        base = Path(root)
    
    processed = base / "processed"
    if sub_dir:
        processed = processed / sub_dir
    return processed

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
    return get_data_path() / "figures"

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with the given name."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

def write_json_log(data: Dict[str, Any], path: Path) -> None:
    """Write a dictionary to a JSON file."""
    ensure_directory(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_json_log(path: Path) -> Dict[str, Any]:
    """Read a JSON file into a dictionary."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def compute_file_hash(path: Path) -> str:
    """Compute the SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_retry_session(max_retries: int = 3, backoff_factor: float = 1.0):
    """
    Get a requests session with retry logic.
    Note: 'requests' must be installed.
    """
    try:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
    except ImportError:
        raise ImportError("The 'requests' library is required for retry logic.")

    session = requests.Session()
    retry = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_data_with_retry(url: str, session=None, **kwargs):
    """Load data from a URL with retry logic."""
    if session is None:
        session = get_retry_session()
    
    attempt = 0
    while attempt < 3:
        try:
            response = session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            attempt += 1
            if attempt == 3:
                raise e
            time.sleep(2 ** attempt) # Exponential backoff

def get_logger(name: str) -> logging.Logger:
    """Alias for setup_logger."""
    return setup_logger(name)

def filter_low_read_samples(df, threshold: int = 10000) -> pd.DataFrame:
    """Filter out samples with read counts below a threshold."""
    import pandas as pd
    if 'read_count' not in df.columns:
        return df
    return df[df['read_count'] >= threshold]

def filter_rare_taxa(df, abundance_threshold: float = 0.001) -> pd.DataFrame:
    """Filter out taxa with relative abundance below a threshold."""
    import pandas as pd
    if 'relative_abundance' not in df.columns:
        return df
    return df[df['relative_abundance'] >= abundance_threshold]

def get_age_group(age: float, groups: Dict[str, tuple] = None) -> str:
    """Categorize age into predefined groups."""
    if groups is None:
        groups = {
            "young": (0, 40),
            "middle": (40, 60),
            "senior": (60, 120)
        }
    for group, (low, high) in groups.items():
        if low <= age < high:
            return group
    return "unknown"

def sanitize_url(url: str) -> str:
    """Sanitize a URL string."""
    # Basic sanitization: ensure it starts with http
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def sanitize_file_path(path: str) -> str:
    """Sanitize a file path string."""
    # Prevent directory traversal
    if '..' in path:
        raise ValueError("Invalid path: directory traversal detected")
    return path
