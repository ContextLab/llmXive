"""
Download module for fetching raw grain boundary data from external APIs.
Handles authentication via environment variables with exponential backoff for rate limits.
"""
import os
import sys
import json
import logging
import hashlib
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))
from utils import compute_sha256, setup_logging, raise_data_insufficiency

logger = setup_logging()

def exponential_backoff_retry(func, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator to add exponential backoff retry logic to a function.
    
    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        
    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs):
        delay = base_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) reached. Last error: {e}")
                    raise
                
                # Check if the error is a rate limit (429) or server error (5xx)
                status_code = getattr(e, 'response', None)
                if status_code is not None:
                    status_code = status_code.status_code
                
                if status_code in [429, 500, 502, 503, 504]:
                    jitter = random.uniform(0.1, 0.5)
                    sleep_time = min(delay * (2 ** attempt) + jitter, max_delay)
                    logger.warning(f"Attempt {attempt + 1} failed with status {status_code}. Retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                    delay = min(delay * 2, max_delay)
                else:
                    # For other errors, don't retry immediately, just log and raise
                    logger.error(f"Non-retryable error: {e}")
                    raise
        raise last_exception
    return wrapper

@exponential_backoff_retry
def _fetch_materials_project_internal(query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Internal function to fetch data from Materials Project API.
    Wrapped with retry logic.
    
    Args:
        query_params: Dictionary of query parameters.
        
    Returns:
        List of data records or None if fetch fails.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.error("MP_API_KEY not found in environment variables.")
        return None

    base_url = "https://materialsproject.org/rest/v2/materials"
    headers = {"X-API-Key": api_key}
    
    try:
        # Using the search endpoint as per spec
        url = f"{base_url}/search" 
        params = {
            "keywords": "grain boundary bicrystal",
            "properties": "diffusivity",
            "format": "json",
            **query_params
        }
        
        logger.info(f"Fetching from Materials Project: {url}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    except requests.exceptions.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from Materials Project: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed (will be retried by decorator): {e}")
        raise

def fetch_materials_project_data(query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch data from Materials Project API with exponential backoff.
    
    Args:
        query_params: Dictionary of query parameters.
        
    Returns:
        List of data records or None if fetch fails.
    """
    return _fetch_materials_project_internal(query_params)

@exponential_backoff_retry
def _fetch_openkim_internal(query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Internal function to fetch data from OpenKIM.
    Wrapped with retry logic.
    
    Args:
        query_params: Dictionary of query parameters.
        
    Returns:
        List of data records or None if fetch fails.
    """
    api_key = os.getenv("OPENKIM_API_KEY")
    if not api_key:
        logger.warning("OPENKIM_API_KEY not found. Skipping OpenKIM fetch.")
        return []

    # OpenKIM typically uses a different API structure (often JSON-RPC or specific endpoints)
    # Placeholder for implementation - assuming a similar REST structure for now
    base_url = "https://api.openkim.org/v1"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        # Example endpoint - adjust based on actual OpenKIM API
        url = f"{base_url}/search"
        params = {
            "keywords": "grain boundary diffusivity",
            **query_params
        }
        
        logger.info(f"Fetching from OpenKIM: {url}")
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    except requests.exceptions.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from OpenKIM: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed (will be retried by decorator): {e}")
        raise

def fetch_openkim_data(query_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch data from OpenKIM with exponential backoff.
    
    Args:
        query_params: Dictionary of query parameters.
        
    Returns:
        List of data records or None if fetch fails.
    """
    return _fetch_openkim_internal(query_params)

def save_raw_data(data: List[Dict[str, Any]], output_dir: Path, source: str) -> str:
    """
    Save raw data to JSON file and compute checksum.
    
    Args:
        data: List of records.
        output_dir: Directory to save the file.
        source: Source identifier for filename.
        
    Returns:
        Checksum of the saved file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = "raw" # In real use, use datetime
    filename = f"{source}_data_{timestamp}.json"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
        
    checksum = compute_sha256(filepath)
    logger.info(f"Saved {len(data)} records to {filepath} (SHA256: {checksum})")
    return checksum

def main():
    """
    Main entry point for data download.
    """
    logger.info("Starting data download pipeline.")
    
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    all_records = []
    
    # Fetch from Materials Project
    mp_data = fetch_materials_project_data({"keywords": ["grain boundary", "bicrystal"], "properties": ["diffusivity"]})
    if mp_data:
        all_records.extend(mp_data)
        save_raw_data(mp_data, data_dir, "materials_project")
        
    # Fetch from OpenKIM
    kim_data = fetch_openkim_data({})
    if kim_data:
        all_records.extend(kim_data)
        save_raw_data(kim_data, data_dir, "openkim")
        
    # Fetch from NIST (Placeholder)
    # nist_data = fetch_nist_data(...)
    
    total_count = len(all_records)
    logger.info(f"Total records retrieved: {total_count}")
    
    # Check data sufficiency
    if total_count < 500:
        raise_data_insufficiency(retrieved=total_count, required=500)
        
    logger.info("Data download completed successfully.")

if __name__ == "__main__":
    main()