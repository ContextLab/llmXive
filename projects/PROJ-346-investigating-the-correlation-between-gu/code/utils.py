import logging
import sys
import os
import time
import json
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
MAX_BENCHMARK_SAMPLES = 1000
READ_THRESHOLD = 10000
ABUNDANCE_FILTER = 0.001
AGE_STRATA = [40, 60]

def get_project_root_path() -> Path:
    """Get the project root directory."""
    # Assume the project root is two levels up from code/utils.py
    # projects/PROJ-346/.../code/utils.py -> projects/PROJ-346
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def get_code_path() -> Path:
    """Get the code directory."""
    return get_project_root_path() / "code"

def get_data_path() -> Path:
    """Get the data directory."""
    return get_project_root_path() / "data"

def get_data_raw_path() -> Path:
    """Get the raw data directory."""
    return get_data_path() / "raw"

def get_data_processed_path(root: Optional[Path] = None, sub_dir: Optional[str] = None) -> Path:
    """
    Get the processed data directory.
    
    Accepts flexible arguments to support multiple call signatures:
    - get_data_processed_path()
    - get_data_processed_path(root)
    - get_data_processed_path(root, sub_dir)
    
    Args:
        root: Optional root path. If None, uses project root.
        sub_dir: Optional subdirectory name within processed.
    
    Returns:
        Path object for the processed directory.
    """
    base = root if root is not None else get_project_root_path()
    processed_dir = base / "data" / "processed"
    
    if sub_dir:
        processed_dir = processed_dir / sub_dir
        
    return processed_dir

def get_data_qc_path() -> Path:
    """Get the QC data directory."""
    return get_data_path() / "qc"

def get_specs_path() -> Path:
    """Get the specs directory."""
    return get_project_root_path() / "specs"

def get_contracts_path() -> Path:
    """Get the contracts directory."""
    return get_project_root_path() / "contracts"

def get_figures_path() -> Path:
    """Get the figures directory."""
    return get_project_root_path() / "figures"

def ensure_directory(path: Path):
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    """Set up a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        if log_file:
            ensure_directory(Path(log_file).parent)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
    return logger

def write_json_log(data: Dict[str, Any], path: Path):
    """Write data to a JSON file."""
    ensure_directory(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_json_log(path: Path) -> Dict[str, Any]:
    """Read data from a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_retry_session(retries: int = 3, backoff_factor: float = 1.0) -> requests.Session:
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

def load_data_with_retry(url: str, timeout: int = 30) -> Optional[requests.Response]:
    """Load data from a URL with retry logic."""
    session = get_retry_session()
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except Exception as e:
        logging.error(f"Failed to load data from {url}: {e}")
        return None

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def filter_low_read_samples(df, column: str = 'read_count', threshold: int = READ_THRESHOLD):
    """Filter samples with read counts below threshold."""
    return df[df[column] >= threshold]

def filter_rare_taxa(df, column: str = 'relative_abundance', threshold: float = ABUNDANCE_FILTER):
    """Filter taxa with relative abundance below threshold."""
    return df[df[column] >= threshold]

def get_age_group(age: float, strata: List[int] = AGE_STRATA) -> str:
    """Categorize age into groups."""
    if age < strata[0]:
        return "young"
    elif age < strata[1]:
        return "middle_aged"
    else:
        return "elderly"

def sanitize_url(url: str) -> str:
    """Sanitize a URL string."""
    # Basic validation
    if not url.startswith(('http://', 'https://')):
        raise ValueError(f"Invalid URL scheme: {url}")
    return url

def sanitize_file_path(path: str) -> Path:
    """Sanitize a file path string."""
    p = Path(path)
    if p.is_absolute():
        # If absolute, make it relative to project root if possible, or raise
        # For safety, we just ensure it's a Path object
        pass
    return p
