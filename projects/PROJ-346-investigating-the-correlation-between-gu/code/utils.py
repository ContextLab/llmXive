"""
Shared utilities for the Gut Microbiome and Cognitive Flexibility project.
"""

import logging
import sys
import os
import time
import json
import hashlib
import requests
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

# Constants
READ_THRESHOLD = 10000
ABUNDANCE_FILTER = 0.001
AGE_STRATA = {'young': '<40', 'middle': '40-60', 'senior': '>=60'}

# Logger setup
def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

logger = setup_logger("utils")

def get_project_root_path():
    """Returns the absolute path to the project root."""
    # Assume script is in code/ or code/subdir/
    current = Path(__file__).resolve()
    return current.parent.parent

def get_code_path():
    """Returns the path to the code directory."""
    return get_project_root_path() / "code"

def get_data_path():
    """Returns the path to the data directory."""
    return get_project_root_path() / "data"

def get_data_raw_path():
    """Returns the path to the raw data directory."""
    return get_data_path() / "raw"

def get_data_processed_path(*args, **kwargs):
    """
    Returns the path to the processed data directory.
    Accepts flexible arguments to satisfy various call signatures across the project.
    
    Call signatures observed:
    - get_data_processed_path()
    - get_data_processed_path(root)
    - get_data_processed_path(root, sub_dir)
    """
    root = get_project_root_path()
    
    # Handle positional arguments if passed (e.g., from code/03_correlation.py)
    if args:
        # If first arg is a Path or string, treat as root override
        if isinstance(args[0], (str, Path)):
            root = Path(args[0])
        # If second arg is provided, treat as subdirectory
        if len(args) > 1:
            return root / "data" / "processed" / args[1]
    
    # Handle keyword arguments if passed
    if 'root' in kwargs:
        root = Path(kwargs['root'])
    if 'sub_dir' in kwargs:
        return root / "data" / "processed" / kwargs['sub_dir']
    
    return root / "data" / "processed"

def get_data_qc_path():
    """Returns the path to the QC data directory."""
    return get_project_root_path() / "data" / "qc"

def get_specs_path():
    """Returns the path to the specs directory."""
    return get_project_root_path() / "specs"

def get_contracts_path():
    """Returns the path to the contracts directory."""
    return get_project_root_path() / "contracts"

def get_figures_path():
    """Returns the path to the figures directory."""
    return get_project_root_path() / "figures"

def ensure_directory(path):
    """Creates a directory if it does not exist."""
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path

def filter_low_read_samples(df, column='read_count', threshold=READ_THRESHOLD):
    """Filters out samples with read counts below the threshold."""
    return df[df[column] >= threshold]

def filter_rare_taxa(df, column='relative_abundance', threshold=ABUNDANCE_FILTER):
    """Filters out taxa with relative abundance below the threshold."""
    return df[df[column] >= threshold]

def get_age_group(age, strata=AGE_STRATA):
    """Categorizes age into predefined strata."""
    if age < 40:
        return strata['young']
    elif age < 60:
        return strata['middle']
    else:
        return strata['senior']

def write_json_log(data, path):
    """Writes data to a JSON log file."""
    ensure_directory(path)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def read_json_log(path):
    """Reads data from a JSON log file."""
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def sanitize_url(url):
    """Sanitizes a URL string."""
    # Basic sanitization to prevent injection
    if not url.startswith(('http://', 'https://')):
        raise ValueError("Invalid URL scheme")
    return url

def sanitize_file_path(path):
    """Sanitizes a file path string."""
    p = Path(path)
    if '..' in p.parts:
        raise ValueError("Invalid path: contains '..'")
    return p

def get_retry_session(max_retries=3, backoff_factor=0.5):
    """Returns a requests Session with retry logic."""
    session = requests.Session()
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    retry = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def load_data_with_retry(url, session=None, timeout=30):
    """Loads data from a URL with retry logic."""
    if session is None:
        session = get_retry_session()
    
    for attempt in range(3):
        try:
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)

def compute_file_hash(path, algorithm='sha256'):
    """Computes the hash of a file."""
    h = hashlib.new(algorithm)
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_logger(name):
    """Returns a logger instance."""
    return logging.getLogger(name)