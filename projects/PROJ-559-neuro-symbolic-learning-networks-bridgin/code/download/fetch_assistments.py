"""
Fetcher for ASSISTments dataset.

This module handles the retrieval of the ASSISTments educational dataset.
It supports fetching from a local cache, downloading from a remote URL,
or generating a synthetic fallback if external data is unavailable or restricted.

Dependencies:
    - pandas
    - requests
    - os
    - json
"""

import os
import time
import hashlib
import json
import logging
from typing import Optional, Dict, Any, List

import pandas as pd

# Configure logger for this module
logger = logging.getLogger(__name__)

# Constants
DEFAULT_DATA_DIR = "data/raw"
ASSISTMENTS_CACHE_FILE = os.path.join(DEFAULT_DATA_DIR, "assistments_sample.csv")
SYNTHETIC_CACHE_FILE = os.path.join(DEFAULT_DATA_DIR, "assistments_synthetic_fallback.csv")

# Simulated remote URL (in a real scenario, this would be the actual ASSISTments URL)
# For this implementation, we use a known stable public dataset or generate synthetic if unreachable
# Using a direct link to a sample CSV from a public repository that mimics ASSISTments structure
REMOTE_URL = "https://raw.githubusercontent.com/Assistments/assistments-data/master/sample.csv"

# Timeout for network requests (seconds) - FR-001, FR-007
REQUEST_TIMEOUT = 10

def _ensure_data_dir():
    """Ensure the data directory exists."""
    if not os.path.exists(DEFAULT_DATA_DIR):
        os.makedirs(DEFAULT_DATA_DIR)
        logger.info(f"Created data directory: {DEFAULT_DATA_DIR}")

def _generate_synthetic_assistments(num_rows: int = 100) -> pd.DataFrame:
    """
    Generate a synthetic ASSISTments-like dataset for fallback purposes.
    
    This is used when the real dataset is unavailable or the download fails.
    It mimics the schema of the ASSISTments dataset (problem_id, skill, correct, rt).
    
    Args:
        num_rows: Number of synthetic rows to generate.
        
    Returns:
        A pandas DataFrame with synthetic data.
    """
    import random
    import numpy as np

    logger.warning(f"Generating synthetic ASSISTments dataset with {num_rows} rows.")
    
    skills = [
        "Addition", "Subtraction", "Multiplication", "Division", 
        "Fractions", "Decimals", "Algebra Basics", "Geometry"
    ]
    
    # Set seed for reproducibility in synthetic generation
    random.seed(42)
    np.random.seed(42)
    
    data = {
        "problem_id": [f"prob_{i:05d}" for i in range(num_rows)],
        "skill": [random.choice(skills) for _ in range(num_rows)],
        "correct": [random.choice([0, 1]) for _ in range(num_rows)],
        "rt_seconds": [max(0.5, random.gauss(15.0, 5.0)) for _ in range(num_rows)],
        "user_id": [f"user_{random.randint(1, 1000):04d}" for _ in range(num_rows)]
    }
    
    return pd.DataFrame(data)

def download_raw_csv(target_path: str) -> bool:
    """
    Attempt to download the raw CSV from the remote source.
    
    Implements FR-001 (timeout handling) and FR-007 (fallback logic).
    
    Args:
        target_path: Local path where the CSV should be saved.
        
    Returns:
        True if download was successful, False otherwise.
    """
    _ensure_data_dir()
    
    try:
        import requests
        logger.info(f"Attempting to download dataset from {REMOTE_URL}")
        
        start_time = time.time()
        response = requests.get(REMOTE_URL, timeout=REQUEST_TIMEOUT)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(response.text)
            logger.info(f"Successfully downloaded dataset in {elapsed:.2f}s to {target_path}")
            return True
        else:
            logger.warning(f"Download failed with status code {response.status_code}")
            return False
            
    except ImportError:
        logger.warning("The 'requests' library is not installed. Cannot download.")
        return False
    except Exception as e:
        logger.error(f"Error during download: {e}")
        return False

def fetch_assistments_dataset(
    use_cache: bool = True,
    force_synthetic: bool = False,
    min_rows: int = 50
) -> Optional[pd.DataFrame]:
    """
    Fetch the ASSISTments dataset, with fallback mechanisms.
    
    Priority:
    1. Local cache (if use_cache is True)
    2. Remote download
    3. Synthetic fallback (if configured or if download fails)
    
    Args:
        use_cache: If True, check for existing local files before downloading.
        force_synthetic: If True, skip download and generate synthetic data immediately.
        min_rows: Minimum number of rows required for the dataset to be considered valid.
        
    Returns:
        A pandas DataFrame containing the dataset, or None if all methods fail.
    """
    _ensure_data_dir()
    
    # 1. Check cache
    if use_cache and os.path.exists(ASSISTMENTS_CACHE_FILE):
        logger.info(f"Loading cached dataset from {ASSISTMENTS_CACHE_FILE}")
        try:
            df = pd.read_csv(ASSISTMENTS_CACHE_FILE)
            if len(df) >= min_rows:
                logger.info(f"Cache valid: {len(df)} rows loaded.")
                return df
            else:
                logger.warning(f"Cache invalid: only {len(df)} rows, regenerating.")
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
    
    # 2. Try synthetic if forced
    if force_synthetic:
        df = _generate_synthetic_assistments(min_rows)
        df.to_csv(SYNTHETIC_CACHE_FILE, index=False)
        logger.info(f"Saved synthetic fallback to {SYNTHETIC_CACHE_FILE}")
        return df

    # 3. Try remote download
    if download_raw_csv(ASSISTMENTS_CACHE_FILE):
        df = pd.read_csv(ASSISTMENTS_CACHE_FILE)
        if len(df) >= min_rows:
            return df
        else:
            logger.warning(f"Downloaded dataset has only {len(df)} rows, too small.")
    
    # 4. Final fallback: Synthetic
    logger.warning("Real data unavailable. Falling back to synthetic dataset.")
    df = _generate_synthetic_assistments(min_rows)
    df.to_csv(SYNTHETIC_CACHE_FILE, index=False)
    return df
