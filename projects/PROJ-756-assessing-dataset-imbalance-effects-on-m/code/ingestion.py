import os
import sys
import time
import logging
import requests
from pathlib import Path
from typing import Optional, Callable, Any, Dict
import json
import hashlib
import pandas as pd

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/ingestion.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Configuration for retry logic
# These can be overridden by environment variables or config file in a real scenario
DEFAULT_RETRY_COUNT = int(os.getenv('INGESTION_RETRY_COUNT', '5'))
DEFAULT_TIMEOUT = int(os.getenv('INGESTION_TIMEOUT', '60'))
DEFAULT_BACKOFF_FACTOR = float(os.getenv('INGESTION_BACKOFF_FACTOR', '2.0'))
MAX_RETRY_DELAY = int(os.getenv('INGESTION_MAX_RETRY_DELAY', '300'))

def exponential_backoff_retry(
    func: Callable,
    args: tuple = (),
    kwargs: dict = None,
    max_retries: Optional[int] = None,
    timeout: Optional[int] = None,
    backoff_factor: Optional[float] = None
) -> Any:
    """
    Executes a function with exponential backoff retry logic.
    
    Logs all API errors and data ingestion failures.
    Returns the result of the function if successful.
    Raises the last exception if all retries are exhausted.
    
    Args:
        func: The function to execute.
        args: Positional arguments for the function.
        kwargs: Keyword arguments for the function.
        max_retries: Number of retry attempts (default: 5).
        timeout: Request timeout in seconds (default: 60).
        backoff_factor: Exponential backoff multiplier (default: 2.0).
        
    Returns:
        The return value of the successful function call.
        
    Raises:
        Exception: The last exception encountered after all retries.
    """
    if kwargs is None:
        kwargs = {}
    if max_retries is None:
        max_retries = DEFAULT_RETRY_COUNT
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    if backoff_factor is None:
        backoff_factor = DEFAULT_BACKOFF_FACTOR

    attempt = 0
    last_exception = None

    while attempt <= max_retries:
        try:
            logger.info(f"Executing {func.__name__} (Attempt {attempt + 1}/{max_retries + 1})")
            result = func(*args, **kwargs)
            logger.info(f"Successfully executed {func.__name__} on attempt {attempt + 1}")
            return result
        except requests.exceptions.RequestException as e:
            last_exception = e
            attempt += 1
            if attempt > max_retries:
                logger.error(f"API Error: {func.__name__} failed after {max_retries} retries. "
                             f"Last error: {str(e)}")
                raise
            
            # Calculate delay with exponential backoff
            delay = min(backoff_factor ** attempt, MAX_RETRY_DELAY)
            logger.warning(f"API Error: {func.__name__} failed (Attempt {attempt}/{max_retries}). "
                           f"Retrying in {delay:.2f}s due to: {str(e)}")
            time.sleep(delay)
        except TimeoutError as e:
            last_exception = e
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Timeout Error: {func.__name__} timed out after {max_retries} retries. "
                             f"Last error: {str(e)}")
                raise
            
            delay = min(backoff_factor ** attempt, MAX_RETRY_DELAY)
            logger.warning(f"Timeout Error: {func.__name__} timed out (Attempt {attempt}/{max_retries}). "
                           f"Retrying in {delay:.2f}s due to: {str(e)}")
            time.sleep(delay)
        except Exception as e:
            # Log unexpected errors but do not retry unless they are transient
            logger.error(f"Unexpected Error in {func.__name__}: {str(e)}")
            raise

    raise last_exception

def fetch_oqmd_data(api_url: str, params: Optional[Dict] = None) -> pd.DataFrame:
    """
    Fetches data from the OQMD API.
    
    Args:
        api_url: The base URL for the OQMD API.
        params: Query parameters for the API request.
        
    Returns:
        A pandas DataFrame containing the fetched data.
    """
    def _do_request():
        response = requests.get(api_url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    
    return exponential_backoff_retry(_do_request)

def fetch_materials_project_data(api_key: str, endpoint: str) -> pd.DataFrame:
    """
    Fetches data from the Materials Project API.
    
    Args:
        api_key: The API key for authentication.
        endpoint: The specific endpoint to query.
        
    Returns:
        A pandas DataFrame containing the fetched data.
    """
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    def _do_request():
        # Note: Actual MP API usage might differ, this is a generic example
        # Adjust URL and parameters based on specific MP API documentation
        url = f"https://api.materialsproject.org/{endpoint}"
        response = requests.get(url, headers=headers, timeout=DEFAULT_TIMEOUT)
        if response.status_code == 403:
            logger.warning("Materials Project API returned 403 Forbidden. "
                         "Check API key validity and rate limits.")
        response.raise_for_status()
        return pd.DataFrame(response.json().get('results', []))
    
    return exponential_backoff_retry(_do_request)

def fetch_aflow_data(api_url: str, params: Optional[Dict] = None) -> pd.DataFrame:
    """
    Fetches data from the AFLOW API.
    
    Args:
        api_url: The base URL for the AFLOW API.
        params: Query parameters for the API request.
        
    Returns:
        A pandas DataFrame containing the fetched data.
    """
    def _do_request():
        response = requests.get(api_url, params=params, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    
    return exponential_backoff_retry(_do_request)

def ingest_materials_data(
    oqmd_url: str,
    aflow_url: str,
    mp_api_key: Optional[str] = None,
    mp_endpoint: Optional[str] = None
) -> Dict[str, pd.DataFrame]:
    """
    Orchestrates the ingestion of materials data from multiple sources.
    
    Args:
        oqmd_url: URL for OQMD data.
        aflow_url: URL for AFLOW data.
        mp_api_key: Optional API key for Materials Project.
        mp_endpoint: Optional endpoint for Materials Project.
        
    Returns:
        A dictionary mapping source names to DataFrames.
    """
    results = {}
    
    # Ingest OQMD
    try:
        logger.info("Starting OQMD data ingestion...")
        oqmd_data = fetch_oqmd_data(oqmd_url)
        results['oqmd'] = oqmd_data
        logger.info(f"OQMD ingestion complete. Retrieved {len(oqmd_data)} records.")
    except Exception as e:
        logger.error(f"Failed to ingest OQMD data: {str(e)}")
        # Depending on requirements, we might want to fail completely or continue
        # For now, we log and continue if other sources are available
        results['oqmd'] = None
        
    # Ingest AFLOW
    try:
        logger.info("Starting AFLOW data ingestion...")
        aflow_data = fetch_aflow_data(aflow_url)
        results['aflow'] = aflow_data
        logger.info(f"AFLOW ingestion complete. Retrieved {len(aflow_data)} records.")
    except Exception as e:
        logger.error(f"Failed to ingest AFLOW data: {str(e)}")
        results['aflow'] = None
        
    # Ingest Materials Project if credentials provided
    if mp_api_key and mp_endpoint:
        try:
            logger.info("Starting Materials Project data ingestion...")
            mp_data = fetch_materials_project_data(mp_api_key, mp_endpoint)
            results['materials_project'] = mp_data
            logger.info(f"Materials Project ingestion complete. Retrieved {len(mp_data)} records.")
        except Exception as e:
            logger.error(f"Failed to ingest Materials Project data: {str(e)}")
            results['materials_project'] = None
    else:
        logger.info("Skipping Materials Project ingestion (no API key or endpoint provided).")
        
    return results

def save_raw_data(data: Dict[str, pd.DataFrame], output_dir: str) -> None:
    """
    Saves raw ingested data to CSV files.
    
    Args:
        data: Dictionary of source name to DataFrame.
        output_dir: Directory to save the files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    for source, df in data.items():
        if df is not None and not df.empty:
            file_path = output_path / f"{source}_raw.csv"
            df.to_csv(file_path, index=False)
            logger.info(f"Saved {source} data to {file_path}")
        else:
            logger.warning(f"No data to save for {source}")

def main():
    """
    Main entry point for the ingestion script.
    Demonstrates the logging and retry configuration.
    """
    # Example usage with dummy URLs (replace with real ones in production)
    # This will likely fail on the first attempt but demonstrates the retry/logging logic
    oqmd_url = os.getenv('OQMD_URL', 'https://oqmd.org/api/v1/entries?format=json')
    aflow_url = os.getenv('AFLOW_URL', 'https://aflow.org/api/v1/entries?format=json')
    
    logger.info("Starting materials data ingestion pipeline...")
    logger.info(f"Configuration: Retry Count={DEFAULT_RETRY_COUNT}, "
               f"Timeout={DEFAULT_TIMEOUT}s, Backoff Factor={DEFAULT_BACKOFF_FACTOR}")
    
    try:
        data = ingest_materials_data(oqmd_url, aflow_url)
        save_raw_data(data, 'data/raw')
        logger.info("Ingestion pipeline completed successfully.")
    except Exception as e:
        logger.critical(f"Ingestion pipeline failed with unrecoverable error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
