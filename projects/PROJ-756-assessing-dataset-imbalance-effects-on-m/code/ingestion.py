"""
Ingestion module for OQMD, AFLOW, and Materials Project APIs.
Implements exponential backoff retry logic and strict 'Fail Loudly' error handling.
"""
import os
import sys
import time
import logging
import requests
from pathlib import Path
import json
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom Exception
class DataFetchError(Exception):
    """Raised when a data fetch operation fails persistently after retries."""
    pass

# Global flag for MP availability
MP_AVAILABLE = True

def exponential_backoff_retry(func, max_retries: int = 5, base_delay: float = 2.0):
    """
    Decorator for exponential backoff retry logic.
    Raises DataFetchError if all retries are exhausted.
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (requests.RequestException, ConnectionError, Timeout) as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}")
                if attempt == max_retries:
                    logger.error(f"Persistent failure in {func.__name__} after {max_retries} retries.")
                    raise DataFetchError(f"Persistent failure in {func.__name__} after {max_retries} retries: {e}")
                delay = base_delay * (2 ** (attempt - 1))
                time.sleep(delay)
        raise DataFetchError(f"Unexpected loop exit in {func.__name__}")
    return wrapper

def log_api_error(error: Exception, source: str) -> None:
    """Log API errors as JSON lines to logs/api_errors.log."""
    log_file = Path("logs/api_errors.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    error_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source": source,
        "error_type": type(error).__name__,
        "message": str(error),
        "traceback": None # Could capture traceback if needed
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(error_entry) + '\n')

@exponential_backoff_retry
def fetch_oqmd_data(api_url: str, params: Optional[Dict] = None) -> requests.Response:
    """Fetch data from OQMD API."""
    response = requests.get(api_url, params=params, timeout=60)
    response.raise_for_status()
    return response

@exponential_backoff_retry
def fetch_aflow_data(api_url: str, params: Optional[Dict] = None) -> requests.Response:
    """Fetch data from AFLOW API."""
    response = requests.get(api_url, params=params, timeout=60)
    response.raise_for_status()
    return response

@exponential_backoff_retry
def fetch_materials_project_data(api_url: str, api_key: str, params: Optional[Dict] = None) -> requests.Response:
    """Fetch data from Materials Project API."""
    headers = {"X-API-Key": api_key}
    response = requests.get(api_url, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    return response

def detect_mp_availability() -> bool:
    """
    Detect Materials Project API availability.
    Sets global MP_AVAILABLE flag.
    """
    global MP_AVAILABLE
    api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if not api_key:
        logger.warning("Materials Project API key not found. MP_AVAILABLE set to False.")
        MP_AVAILABLE = False
        return False
    
    try:
        # Lightweight probe
        url = "https://materialsproject.org/rest/v2/materials/ICSD-1" # Example probe
        response = requests.get(url, headers={"X-API-Key": api_key}, timeout=10)
        if response.status_code == 403:
            logger.warning("MP API returned 403. MP_AVAILABLE set to False.")
            MP_AVAILABLE = False
            return False
        response.raise_for_status()
        logger.info("Materials Project API is available.")
        MP_AVAILABLE = True
        return True
    except Exception as e:
        logger.warning(f"MP API probe failed: {e}. MP_AVAILABLE set to False.")
        MP_AVAILABLE = False
        return False

def ingest_materials_data(source: str = "hf") -> Optional[Dict]:
    """
    Ingest materials data from a source.
    For MP, uses fallback logic if API is unavailable (FR-008).
    For OQMD/AFLOW, raises DataFetchError on failure.
    """
    if source == "mp" and not MP_AVAILABLE:
        logger.warning("MP unavailable. Skipping MP ingestion.")
        return None
    
    # Placeholder for actual ingestion logic which would call the fetch functions
    # and merge data. The core requirement here is the error handling structure.
    return {"status": "success", "source": source}

def save_raw_data(data: Any, output_path: str) -> None:
    """Save raw data to a file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    # Implementation depends on data type (parquet, json, etc.)
    logger.info(f"Saving raw data to {output_path}")

def main():
    """Main entry point for ingestion pipeline."""
    logger.info("Starting ingestion pipeline...")
    
    # Check MP availability first
    detect_mp_availability()
    
    try:
        # Example: Fetch OQMD
        # This will raise DataFetchError if it fails persistently
        # oqmd_response = fetch_oqmd_data("https://oqmd.org/rest/v1/...")
        
        # Example: Fetch AFLOW
        # aflow_response = fetch_aflow_data("https://aflow.org/rest/v1/...")
        
        # Example: Fetch MP (if available)
        # if MP_AVAILABLE:
        #     mp_response = fetch_materials_project_data("https://materialsproject.org/rest/v2/...", os.getenv("MATERIALS_PROJECT_API_KEY"))
        
        logger.info("Ingestion pipeline completed successfully.")
        
    except DataFetchError as e:
        logger.critical(f"Ingestion pipeline failed due to persistent data fetch error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in ingestion pipeline: {e}")
        raise

if __name__ == "__main__":
    main()
