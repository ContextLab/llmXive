import logging
import sys
import os
import time
import json
import hashlib
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- Path Helpers ---

def get_project_root_path() -> Path:
    """Return the project root directory."""
    current = Path(__file__).resolve()
    # Assuming utils.py is in code/, root is parent
    return current.parent.parent

def get_code_path() -> Path:
    """Return the code directory."""
    return get_project_root_path() / "code"

def get_data_path() -> Path:
    """Return the data directory."""
    return get_project_root_path() / "data"

def get_data_raw_path() -> Path:
    """Return the data/raw directory."""
    return get_data_path() / "raw"

def get_data_processed_path() -> Path:
    """Return the data/processed directory."""
    return get_data_path() / "processed"

def get_data_qc_path() -> Path:
    """Return the data/qc directory."""
    return get_data_path() / "qc"

def get_specs_path() -> Path:
    """Return the specs directory."""
    return get_project_root_path() / "specs"

def get_contracts_path() -> Path:
    """Return the contracts directory."""
    return get_project_root_path() / "contracts"

def get_figures_path() -> Path:
    """Return the figures directory."""
    return get_project_root_path() / "figures"

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

# --- Logging Helpers ---

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with optional file handler."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler if specified
        if log_file:
            ensure_directory(Path(log_file).parent)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger, creating one if it doesn't exist."""
    return logging.getLogger(name)

def write_json_log(path: Path, data: Dict[str, Any]) -> None:
    """Write data to a JSON log file."""
    ensure_directory(path.parent)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_json_log(path: Path) -> Dict[str, Any]:
    """Read data from a JSON log file."""
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

# --- Validation Helpers ---

def validate_dataframe_columns(df, required_columns: List[str]) -> bool:
    """Validate that a DataFrame has required columns."""
    if df is None:
        return False
    missing = set(required_columns) - set(df.columns)
    return len(missing) == 0

# --- Security Hardening: URL and Path Sanitization ---

# Allowed protocols for external data fetching
ALLOWED_PROTOCOLS = {'http', 'https'}

# Regex pattern to detect path traversal attempts
PATH_TRAVERSAL_PATTERN = re.compile(r'\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c', re.IGNORECASE)

def sanitize_url(url: str) -> str:
    """
    Sanitize an external URL to prevent SSRF and injection attacks.
    
    Args:
        url: The URL to sanitize.
        
    Returns:
        The validated and cleaned URL string.
        
    Raises:
        ValueError: If the URL is invalid, uses a disallowed protocol, 
                    or contains path traversal attempts.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string.")
    
    url = url.strip()
    
    # Check for path traversal in the URL string itself (rare but possible)
    if PATH_TRAVERSAL_PATTERN.search(url):
        raise ValueError(f"Invalid URL detected: potential path traversal in {url}")
    
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Validate protocol
        if parsed.scheme not in ALLOWED_PROTOCOLS:
            raise ValueError(f"Disallowed protocol in URL: {parsed.scheme}. Allowed: {ALLOWED_PROTOCOLS}")
        
        # Validate netloc is present for http/https
        if not parsed.netloc:
            raise ValueError(f"Invalid URL structure: missing network location in {url}")
        
        # Additional check: ensure no IP address in netloc if strict SSRF protection needed
        # (Optional, but good practice for security hardening)
        # For now, we rely on the protocol and structure checks.
        
        return url
        
    except Exception as e:
        raise ValueError(f"Failed to parse URL: {e}")

def sanitize_file_path(path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Sanitize a file path to prevent directory traversal attacks.
    
    Args:
        path: The path string to sanitize.
        base_dir: Optional base directory to resolve relative paths against.
                  If None, defaults to the project root.
                  
    Returns:
        A resolved and validated Path object.
        
    Raises:
        ValueError: If the path contains traversal attempts or resolves outside the base directory.
    """
    if not path or not isinstance(path, str):
        raise ValueError("Path must be a non-empty string.")
    
    path = path.strip()
    
    # Check for traversal patterns in the string
    if PATH_TRAVERSAL_PATTERN.search(path):
        raise ValueError(f"Invalid path detected: potential directory traversal in {path}")
    
    # Convert to Path object
    p = Path(path)
    
    # If relative, resolve against base_dir
    if not p.is_absolute():
        if base_dir is None:
            base_dir = get_project_root_path()
        p = (base_dir / p).resolve()
    else:
        p = p.resolve()
    
    # Ensure the resolved path is within the intended base directory
    # We check against the project root to prevent writing anywhere on the system
    project_root = get_project_root_path()
    try:
        p.relative_to(project_root)
    except ValueError:
        raise ValueError(f"Path {p} is outside the project root {project_root}")
    
    return p

# --- Data Loading with Retry Logic and Security ---

def get_retry_session(retries: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """
    Create a requests session with automatic retry logic and exponential backoff.
    
    Args:
        retries: Number of retry attempts.
        backoff_factor: Factor for exponential backoff (sleep = backoff * (2 ** (retry - 1))).
                        
    Returns:
        A configured requests Session object.
    """
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_data_from_api(url: str, timeout: int = 30, **kwargs) -> Any:
    """
    Load data from a remote API with security checks and retry logic.
    
    This function sanitizes the URL before making the request and implements
    exponential backoff for transient failures.
    
    Args:
        url: The URL to fetch data from.
        timeout: Request timeout in seconds.
        **kwargs: Additional arguments passed to requests.get (e.g., headers).
                
    Returns:
        The response content (text or json depending on implementation).
        
    Raises:
        ValueError: If URL sanitization fails.
        requests.exceptions.RequestException: If all retries fail.
    """
    # SECURITY: Sanitize URL
    safe_url = sanitize_url(url)
    
    session = get_retry_session()
    
    try:
        response = session.get(safe_url, timeout=timeout, **kwargs)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        # Log the error but re-raise to let the caller handle it
        logger = get_logger(__name__)
        logger.error(f"Failed to fetch data from {safe_url} after retries: {e}")
        raise

def compute_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the hash of a file for integrity verification.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.
        
    Returns:
        Hexadecimal hash string.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

# --- Data Filtering Helpers (Placeholder for existing logic) ---

def filter_low_read_samples(df, column: str, threshold: int = 10000):
    """Filter samples with read counts below threshold."""
    if not validate_dataframe_columns(df, [column]):
        raise ValueError(f"DataFrame missing required column: {column}")
    return df[df[column] >= threshold]

def filter_rare_taxa(df, column: str, threshold: float = 0.001):
    """Filter taxa with abundance below threshold."""
    if not validate_dataframe_columns(df, [column]):
        raise ValueError(f"DataFrame missing required column: {column}")
    return df[df[column] >= threshold]

def get_age_group(age: Union[int, float]) -> str:
    """Categorize age into groups."""
    if age < 40:
        return "<40"
    elif age < 60:
        return "40-59"
    else:
        return ">=60"

def load_data_with_retry(url: str, max_retries: int = 3, backoff_factor: float = 0.5) -> requests.Response:
    """
    Wrapper for load_data_from_api with explicit retry configuration.
    """
    return load_data_from_api(url, retries=max_retries, backoff_factor=backoff_factor)
