"""
Ingestion module for materials dataset fetching with robust error handling.

Implements:
- Exponential backoff retry logic
- API availability detection (Materials Project)
- Fail-loudly behavior for persistent failures
- Streaming dataset loading
"""

import os
import sys
import time
import logging
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List

# Import DataFetchError from downloaders as per API surface
from downloaders import DataFetchError

# Constants
API_BASE_DELAY = 1.0
API_MAX_DELAY = 60.0
API_MULTIPLIER = 2.0
API_MAX_RETRIES = 5

# Global flag for Materials Project availability
MP_AVAILABLE = True

# Logger setup
_logger = None

def get_logger():
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(__name__)
        _logger.setLevel(logging.DEBUG)
        if not _logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
    return _logger

def ensure_log_directory():
    """Ensure the logs directory exists."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir

def rotate_log_if_needed(log_path: Path, max_size_mb: int = 100):
    """Rotate log file if it exceeds max_size_mb."""
    if log_path.exists() and log_path.stat().st_size > max_size_mb * 1024 * 1024:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = log_path.parent / f"{log_path.stem}_{timestamp}.log"
        log_path.rename(backup_path)
        get_logger().info(f"Rotated log file to {backup_path}")

def log_api_error(endpoint: str, error: str, retry_count: int, log_path: Optional[Path] = None):
    """
    Log API errors as JSON lines to logs/api_errors.log.
    
    Args:
        endpoint: The API endpoint that failed
        error: The error message
        retry_count: The current retry count
        log_path: Optional path to log file (defaults to logs/api_errors.log)
    """
    if log_path is None:
        log_dir = ensure_log_directory()
        log_path = log_dir / "api_errors.log"
    
    error_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "endpoint": endpoint,
        "error": error,
        "retry_count": retry_count
    }
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(error_entry) + '\n')

def exponential_backoff_retry(func, *args, base_delay: float = API_BASE_DELAY, 
                              max_delay: float = API_MAX_DELAY, 
                              multiplier: float = API_MULTIPLIER, 
                              max_retries: int = API_MAX_RETRIES,
                              endpoint: str = "unknown",
                              **kwargs):
    """
    Execute a function with exponential backoff retry logic.
    
    Args:
        func: The function to execute
        *args: Positional arguments for the function
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        multiplier: Multiplier for delay
        max_retries: Maximum number of retry attempts
        endpoint: API endpoint name for logging
        **kwargs: Keyword arguments for the function
        
    Returns:
        The result of the function if successful
        
    Raises:
        DataFetchError: If all retries fail
    """
    logger = get_logger()
    delay = base_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries + 1} for {endpoint}")
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed for {endpoint}: {str(e)}")
            log_api_error(endpoint, str(e), attempt)
            
            if attempt < max_retries:
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                delay = min(delay * multiplier, max_delay)
            else:
                logger.error(f"All {max_retries + 1} attempts failed for {endpoint}")
    
    # If we reach here, all retries failed
    error_msg = f"Persistent failure for {endpoint} after {max_retries + 1} attempts: {str(last_exception)}"
    logger.error(error_msg)
    raise DataFetchError(error_msg)

def detect_mp_availability(api_key: Optional[str] = None) -> bool:
    """
    Detect Materials Project API availability by attempting a lightweight probe.
    
    Args:
        api_key: Optional API key (reads from MP_API_KEY env var if not provided)
        
    Returns:
        True if MP is available, False otherwise
    """
    global MP_AVAILABLE
    
    if api_key is None:
        api_key = os.getenv("MP_API_KEY")
    
    if not api_key:
        logger = get_logger()
        logger.warning("Materials Project API key not found. Setting MP_AVAILABLE=False.")
        MP_AVAILABLE = False
        return False
    
    try:
        # Lightweight probe request
        url = "https://materialsproject.org/rest/v2/materials/vasp"
        headers = {"X-API-Key": api_key}
        params = {"material_id": "mp-1", "pretty_print": "true"}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            logger = get_logger()
            logger.info("Materials Project API is available.")
            MP_AVAILABLE = True
            return True
        elif response.status_code == 403:
            logger = get_logger()
            logger.warning(f"Materials Project API returned 403. Setting MP_AVAILABLE=False.")
            MP_AVAILABLE = False
            return False
        else:
            logger = get_logger()
            logger.warning(f"Materials Project API returned {response.status_code}. Setting MP_AVAILABLE=False.")
            MP_AVAILABLE = False
            return False
            
    except requests.exceptions.Timeout:
        logger = get_logger()
        logger.warning("Materials Project API probe timed out. Setting MP_AVAILABLE=False.")
        MP_AVAILABLE = False
        return False
    except requests.exceptions.RequestException as e:
        logger = get_logger()
        logger.warning(f"Materials Project API probe failed: {str(e)}. Setting MP_AVAILABLE=False.")
        MP_AVAILABLE = False
        return False

def fetch_oqmd_data(streaming: bool = True) -> Any:
    """
    Fetch OQMD dataset with fail-loudly behavior.
    
    Args:
        streaming: Whether to stream the dataset
        
    Returns:
        The dataset object
        
    Raises:
        DataFetchError: If fetch fails after retries
    """
    from downloaders import download_oqmd_constitution
    
    def _fetch():
        return download_oqmd_constitution(streaming=streaming)
    
    return exponential_backoff_retry(
        _fetch,
        endpoint="OQMD",
        base_delay=API_BASE_DELAY,
        max_delay=API_MAX_DELAY,
        multiplier=API_MULTIPLIER,
        max_retries=API_MAX_RETRIES
    )

def fetch_aflow_data(streaming: bool = True) -> Any:
    """
    Fetch AFLOW dataset with fail-loudly behavior.
    
    Args:
        streaming: Whether to stream the dataset
        
    Returns:
        The dataset object
        
    Raises:
        DataFetchError: If fetch fails after retries
    """
    from downloaders import download_aflow_constitution
    
    def _fetch():
        return download_aflow_constitution(streaming=streaming)
    
    return exponential_backoff_retry(
        _fetch,
        endpoint="AFLOW",
        base_delay=API_BASE_DELAY,
        max_delay=API_MAX_DELAY,
        multiplier=API_MULTIPLIER,
        max_retries=API_MAX_RETRIES
    )

def fetch_materials_project_data(streaming: bool = True) -> Optional[Any]:
    """
    Fetch Materials Project dataset with fail-loudly behavior and fallback logic.
    
    Args:
        streaming: Whether to stream the dataset
        
    Returns:
        The dataset object if successful, None if MP is unavailable
        
    Raises:
        DataFetchError: If fetch fails after retries and MP is available
    """
    global MP_AVAILABLE
    
    if not MP_AVAILABLE:
        logger = get_logger()
        logger.warning("Materials Project is unavailable. Skipping MP fetch.")
        return None
    
    from downloaders import download_materials_project
    
    def _fetch():
        return download_materials_project(streaming=streaming)
    
    try:
        return exponential_backoff_retry(
            _fetch,
            endpoint="Materials Project",
            base_delay=API_BASE_DELAY,
            max_delay=API_MAX_DELAY,
            multiplier=API_MULTIPLIER,
            max_retries=API_MAX_RETRIES
        )
    except DataFetchError:
        # For MP, if persistent failure occurs, log warning and switch to fallback mode
        logger = get_logger()
        logger.warning(
            "Materials Project fetch failed after retries. "
            "Switching to fallback mode (OQMD/AFLOW only) as per FR-008. "
            "No synthetic fallback will be used."
        )
        MP_AVAILABLE = False
        return None

def merge_datasets(datasets: List[Any]) -> Any:
    """
    Merge multiple datasets into a single unified dataset.
    
    Args:
        datasets: List of dataset objects to merge
        
    Returns:
        Merged dataset
    """
    if not datasets:
        return None
    
    # Filter out None values (e.g., if MP was unavailable)
    valid_datasets = [ds for ds in datasets if ds is not None]
    
    if not valid_datasets:
        logger = get_logger()
        logger.warning("No valid datasets to merge.")
        return None
    
    # Import pandas for merging
    import pandas as pd
    
    # Load all datasets into DataFrames
    dfs = []
    for i, ds in enumerate(valid_datasets):
        try:
            # Try to convert to DataFrame
            if hasattr(ds, 'to_pandas'):
                df = ds.to_pandas()
            elif hasattr(ds, 'data'):
                df = pd.DataFrame(ds.data)
            else:
                df = pd.DataFrame(ds)
            dfs.append(df)
            logger = get_logger()
            logger.info(f"Loaded dataset {i+1}: {len(df)} rows")
        except Exception as e:
            logger = get_logger()
            logger.warning(f"Failed to load dataset {i+1}: {str(e)}")
    
    if not dfs:
        logger = get_logger()
        logger.warning("No datasets could be loaded for merging.")
        return None
    
    # Concatenate all DataFrames
    merged_df = pd.concat(dfs, ignore_index=True)
    logger = get_logger()
    logger.info(f"Merged dataset: {len(merged_df)} rows")
    
    return merged_df

def validate_data_integrity(dataset: Any) -> bool:
    """
    Validate the integrity of a dataset.
    
    Args:
        dataset: The dataset to validate
        
    Returns:
        True if valid, False otherwise
    """
    if dataset is None:
        return False
    
    try:
        import pandas as pd
        
        if hasattr(dataset, 'to_pandas'):
            df = dataset.to_pandas()
        elif hasattr(dataset, 'data'):
            df = pd.DataFrame(dataset.data)
        else:
            df = pd.DataFrame(dataset)
        
        # Check for empty dataset
        if df.empty:
            logger = get_logger()
            logger.warning("Dataset is empty.")
            return False
        
        # Check for required columns (basic validation)
        required_cols = ['composition', 'formula']
        available_cols = df.columns.tolist()
        
        missing_cols = [col for col in required_cols if col not in available_cols]
        if missing_cols:
            logger = get_logger()
            logger.warning(f"Missing required columns: {missing_cols}")
            return False
        
        logger = get_logger()
        logger.info(f"Dataset validation passed: {len(df)} rows, {len(df.columns)} columns")
        return True
        
    except Exception as e:
        logger = get_logger()
        logger.error(f"Dataset validation failed: {str(e)}")
        return False

def ingest_materials_data(streaming: bool = True) -> Dict[str, Any]:
    """
    Ingest all materials datasets (OQMD, AFLOW, MP).
    
    Args:
        streaming: Whether to stream datasets
        
    Returns:
        Dictionary with dataset objects and metadata
    """
    logger = get_logger()
    logger.info("Starting materials data ingestion...")
    
    # Fetch datasets
    oqmd_data = fetch_oqmd_data(streaming=streaming)
    aflow_data = fetch_aflow_data(streaming=streaming)
    mp_data = fetch_materials_project_data(streaming=streaming)
    
    # Merge datasets
    merged_data = merge_datasets([oqmd_data, aflow_data, mp_data])
    
    # Validate
    is_valid = validate_data_integrity(merged_data)
    
    result = {
        "oqmd": oqmd_data,
        "aflow": aflow_data,
        "mp": mp_data,
        "merged": merged_data,
        "valid": is_valid,
        "mp_available": MP_AVAILABLE
    }
    
    logger.info(f"Ingestion complete. Valid: {is_valid}, MP Available: {MP_AVAILABLE}")
    return result

def save_raw_data(dataset: Any, output_path: str):
    """
    Save a dataset to a parquet file.
    
    Args:
        dataset: The dataset to save
        output_path: Path to the output file
    """
    import pandas as pd
    from pathlib import Path
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        if hasattr(dataset, 'to_pandas'):
            df = dataset.to_pandas()
        elif hasattr(dataset, 'data'):
            df = pd.DataFrame(dataset.data)
        else:
            df = pd.DataFrame(dataset)
        
        df.to_parquet(output_path, index=False)
        logger = get_logger()
        logger.info(f"Saved dataset to {output_path}: {len(df)} rows")
    except Exception as e:
        logger = get_logger()
        logger.error(f"Failed to save dataset: {str(e)}")
        raise

def main():
    """Main entry point for the ingestion module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest materials datasets")
    parser.add_argument("--streaming", action="store_true", help="Use streaming mode")
    parser.add_argument("--output-dir", default="data/raw", help="Output directory for raw data")
    args = parser.parse_args()
    
    logger = get_logger()
    logger.info("Running ingestion module...")
    
    # Detect MP availability first
    detect_mp_availability()
    
    # Ingest data
    result = ingest_materials_data(streaming=args.streaming)
    
    if result["valid"]:
        # Save individual datasets
        if result["oqmd"] is not None:
            save_raw_data(result["oqmd"], os.path.join(args.output_dir, "oqmd.parquet"))
        if result["aflow"] is not None:
            save_raw_data(result["aflow"], os.path.join(args.output_dir, "aflow.parquet"))
        if result["mp"] is not None:
            save_raw_data(result["mp"], os.path.join(args.output_dir, "mp.parquet"))
        
        # Save merged dataset
        if result["merged"] is not None:
            save_raw_data(result["merged"], os.path.join(args.output_dir, "merged_raw.parquet"))
        
        logger.info("Ingestion completed successfully.")
    else:
        logger.error("Ingestion failed validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()