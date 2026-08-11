"""
Ingestion module for data acquisition with retry logic, logging, and fail-loudly behavior.

Implements:
- Exponential backoff retry logic (T004a-Backoff)
- JSON error logging (T004a-LogSchema)
- Size-based log rotation (T004b)
- Fail loudly on persistent failure (T004c)
- Materials Project availability detection (T006a)
"""
import os
import sys
import time
import logging
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import hashlib
import pandas as pd

# Custom exception for data fetch failures
class DataFetchError(Exception):
    """Raised when data fetching fails persistently after retries."""
    pass

# Global flag for Materials Project availability
MP_AVAILABLE = True

# Configuration constants
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "api_errors.log"
MAX_LOG_SIZE_MB = 100
BASE_DELAY = 1.0
MAX_DELAY = 60.0
MULTIPLIER = 2.0
MAX_RETRIES = 5
MP_API_KEY_ENV = "MP_API_KEY"

def get_logger(name: str = "ingestion") -> logging.Logger:
    """Get a logger configured for the ingestion module."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    return logger

logger = get_logger()

def ensure_log_directory():
    """Ensure the log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def rotate_log_if_needed():
    """Rotate log file if it exceeds MAX_LOG_SIZE_MB."""
    ensure_log_directory()
    if LOG_FILE.exists():
        size_mb = LOG_FILE.stat().st_size / (1024 * 1024)
        if size_mb > MAX_LOG_SIZE_MB:
            new_name = LOG_FILE.with_suffix(f".{int(time.time())}.log")
            LOG_FILE.rename(new_name)
            logger.info(f"Rotated log file to {new_name}")

def log_api_error(endpoint: str, error: str, retry_count: int):
    """Log API errors in JSON lines format."""
    ensure_log_directory()
    rotate_log_if_needed()
    
    error_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": endpoint,
        "error": error,
        "retry_count": retry_count
    }
    
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(error_entry) + "\n")

def exponential_backoff_retry(func, *args, **kwargs):
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function if successful
        
    Raises:
        DataFetchError: If all retries fail
    """
    last_exception = None
    delay = BASE_DELAY
    
    for retry_count in range(MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except (requests.RequestException, ConnectionError, Timeout) as e:
            last_exception = e
            error_msg = str(e)
            
            if retry_count < MAX_RETRIES:
                log_api_error(
                    endpoint=kwargs.get("endpoint", "unknown"),
                    error=error_msg,
                    retry_count=retry_count
                )
                logger.warning(
                    f"Retry {retry_count + 1}/{MAX_RETRIES} failed: {error_msg}. "
                    f"Waiting {delay:.1f}s before retry."
                )
                time.sleep(delay)
                delay = min(delay * MULTIPLIER, MAX_DELAY)
            else:
                logger.error(f"Max retries ({MAX_RETRIES}) exceeded for {kwargs.get('endpoint', 'unknown')}")
    
    # All retries exhausted
    raise DataFetchError(
        f"Persistent failure after {MAX_RETRIES} retries: {last_exception}"
    )

def detect_mp_availability():
    """
    Detect Materials Project API availability by attempting a probe request.
    
    Sets global MP_AVAILABLE flag to False if probe fails.
    """
    global MP_AVAILABLE
    api_key = os.getenv(MP_API_KEY_ENV)
    
    if not api_key:
        logger.warning(f"Material Project API key not found in environment variable {MP_API_KEY_ENV}")
        MP_AVAILABLE = False
        return False
    
    try:
        # Lightweight probe request
        response = requests.get(
            "https://materialsproject.org/rest/v2/materials/MP-1",
            headers={"X-API-Key": api_key},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info("Materials Project API is available")
            MP_AVAILABLE = True
            return True
        elif response.status_code in [403, 401]:
            logger.warning(f"Materials Project API returned {response.status_code}: Invalid or expired key")
            MP_AVAILABLE = False
            return False
        else:
            logger.warning(f"Materials Project API returned unexpected status {response.status_code}")
            MP_AVAILABLE = False
            return False
            
    except (requests.RequestException, Timeout, ConnectionError) as e:
        logger.warning(f"Materials Project API probe failed: {e}")
        MP_AVAILABLE = False
        return False

def fetch_oqmd_data():
    """
    Fetch OQMD dataset using official REST API with exponential backoff.
    
    Returns:
        DataFrame with OQMD data
        
    Raises:
        DataFetchError: If fetch fails persistently
    """
    def _fetch():
        # OQMD REST API endpoint for constitution data
        # Using a specific endpoint that returns JSON/CSV
        url = "https://oqmd.org/api/v2/entries"
        params = {"format": "json", "limit": 1000}  # Example limit, adjust as needed
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    try:
        result = exponential_backoff_retry(_fetch, endpoint="oqmd")
        return pd.DataFrame(result.get("entries", []))
    except DataFetchError:
        # Fail loudly - no synthetic fallback
        raise DataFetchError("Failed to fetch OQMD data after all retries. No synthetic fallback available.")

def fetch_aflow_data():
    """
    Fetch AFLOW dataset using official REST API with exponential backoff.
    
    Returns:
        DataFrame with AFLOW data
        
    Raises:
        DataFetchError: If fetch fails persistently
    """
    def _fetch():
        # AFLOW REST API endpoint
        url = "https://aflow.org/rest/v1.0/aflow_api"
        params = {"format": "json", "limit": 1000}  # Example limit
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    try:
        result = exponential_backoff_retry(_fetch, endpoint="aflow")
        return pd.DataFrame(result.get("entries", []))
    except DataFetchError:
        # Fail loudly - no synthetic fallback
        raise DataFetchError("Failed to fetch AFLOW data after all retries. No synthetic fallback available.")

def fetch_materials_project_data():
    """
    Fetch Materials Project dataset using official REST API with exponential backoff.
    
    Returns:
        DataFrame with MP data or None if MP unavailable
        
    Raises:
        DataFetchError: If fetch fails persistently and MP is available
        Warning logged if MP unavailable, returns None
    """
    if not MP_AVAILABLE:
        logger.warning("Materials Project unavailable - skipping fetch")
        return None
    
    def _fetch():
        api_key = os.getenv(MP_API_KEY_ENV)
        if not api_key:
            raise DataFetchError("MP API key missing")
        
        url = "https://materialsproject.org/rest/v2/materials"
        headers = {"X-API-Key": api_key}
        params = {"limit": 1000}  # Example limit
        
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    try:
        result = exponential_backoff_retry(_fetch, endpoint="materials_project")
        return pd.DataFrame(result.get("data", []))
    except DataFetchError as e:
        # Persistent failure for MP - log warning and return None (fallback mode)
        logger.warning(f"Materials Project fetch failed persistently: {e}. Switching to fallback mode (OQMD/AFLOW only).")
        return None

def merge_datasets(oqmd_df: Optional[pd.DataFrame], aflow_df: Optional[pd.DataFrame], 
                   mp_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    """Merge multiple datasets into a single DataFrame."""
    dfs = []
    if oqmd_df is not None and not oqmd_df.empty:
        oqmd_df['source'] = 'oqmd'
        dfs.append(oqmd_df)
    if aflow_df is not None and not aflow_df.empty:
        aflow_df['source'] = 'aflow'
        dfs.append(aflow_df)
    if mp_df is not None and not mp_df.empty:
        mp_df['source'] = 'mp'
        dfs.append(mp_df)
    
    if not dfs:
        raise DataFetchError("No datasets available to merge")
    
    return pd.concat(dfs, ignore_index=True)

def validate_data_integrity(df: pd.DataFrame) -> bool:
    """Validate basic data integrity."""
    if df.empty:
        return False
    # Basic checks
    return True

def ingest_materials_data():
    """
    Main orchestration function for data ingestion.
    
    Returns:
        Merged DataFrame or raises DataFetchError on critical failure
    """
    # Detect MP availability first
    detect_mp_availability()
    
    # Fetch OQMD (required)
    logger.info("Fetching OQMD data...")
    try:
        oqmd_df = fetch_oqmd_data()
    except DataFetchError:
        raise  # Re-raise - OQMD is required, fail loudly
    
    # Fetch AFLOW (required)
    logger.info("Fetching AFLOW data...")
    try:
        aflow_df = fetch_aflow_data()
    except DataFetchError:
        raise  # Re-raise - AFLOW is required, fail loudly
    
    # Fetch MP (optional, with fallback)
    mp_df = None
    if MP_AVAILABLE:
        logger.info("Fetching Materials Project data...")
        try:
            mp_df = fetch_materials_project_data()
        except DataFetchError:
            # MP failure - log warning and continue with OQMD/AFLOW only
            logger.warning("Materials Project fetch failed. Proceeding with OQMD/AFLOW only.")
            mp_df = None
    
    # Merge datasets
    logger.info("Merging datasets...")
    merged_df = merge_datasets(oqmd_df, aflow_df, mp_df)
    
    # Validate
    if not validate_data_integrity(merged_df):
        raise DataFetchError("Data integrity validation failed")
    
    return merged_df

def save_raw_data(df: pd.DataFrame, output_path: str):
    """Save raw data to parquet file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved raw data to {output_path}")

def main():
    """Main entry point for ingestion script."""
    logger.info("Starting data ingestion...")
    try:
        data = ingest_materials_data()
        save_raw_data(data, "data/raw/merged_materials.parquet")
        logger.info("Ingestion completed successfully")
        return 0
    except DataFetchError as e:
        logger.error(f"Ingestion failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())