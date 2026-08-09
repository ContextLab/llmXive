"""
Ingestion module for materials data pipeline.
Handles API clients, retries, error logging, merging, and data integrity validation.
"""
import os
import sys
import time
import logging
import json
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

# Configure logging for this module
logger = logging.getLogger(__name__)

# Custom Exception for Data Fetch Errors
class DataFetchError(Exception):
    """Raised when data fetching fails persistently after retries."""
    pass

# Global flag for MP availability (set by detect_mp_availability)
MP_AVAILABLE = True

def log_api_error(error_data: Dict[str, Any]) -> None:
    """
    Log API errors as JSON lines to logs/api_errors.log.
    Implements size-based rotation (create new file if > 100MB).
    """
    log_path = Path("logs/api_errors.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Check file size for rotation
    if log_path.exists() and log_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
        new_log_path = log_path.with_suffix(f".{int(time.time())}.log")
        logger.warning(f"Rotating log file: {log_path} -> {new_log_path}")
        log_path.rename(new_log_path)

    with open(log_path, "a") as f:
        f.write(json.dumps(error_data) + "\n")

def exponential_backoff_retry(url: str, max_retries: int = 5, timeout: int = 30) -> Optional[requests.Response]:
    """
    Fetch URL with exponential backoff retry logic.
    Returns Response object on success, None on failure.
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return response
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                # Log error
                log_api_error({
                    "url": url,
                    "status_code": response.status_code,
                    "attempt": attempt + 1,
                    "error": f"HTTP {response.status_code}"
                })
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request exception for {url}: {e}")
            log_api_error({
                "url": url,
                "attempt": attempt + 1,
                "error": str(e)
            })

        if attempt < max_retries - 1:
            delay = 2 ** attempt
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)

    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None

def fetch_oqmd_data() -> Optional[pd.DataFrame]:
    """Fetch OQMD data via API or fallback to dataset loading."""
    # Placeholder for actual API implementation or dataset loading
    # In a real scenario, this would call the OQMD API or load from a dataset
    try:
        # Simulating a fetch (replace with actual API call)
        # response = exponential_backoff_retry("https://oqmd.org/api/...")
        # if response:
        #     return pd.read_json(response.text)
        
        # For now, return None to indicate failure or missing implementation
        logger.warning("OQMD data fetch not implemented or failed")
        return None
    except Exception as e:
        log_api_error({"source": "OQMD", "error": str(e)})
        return None

def fetch_aflow_data() -> Optional[pd.DataFrame]:
    """Fetch AFLOW data via API or fallback to dataset loading."""
    try:
        # Simulating a fetch
        # response = exponential_backoff_retry("https://aflow.org/api/...")
        # if response:
        #     return pd.read_json(response.text)

        logger.warning("AFLOW data fetch not implemented or failed")
        return None
    except Exception as e:
        log_api_error({"source": "AFLOW", "error": str(e)})
        return None

def detect_mp_availability() -> bool:
    """
    Detect Materials Project API availability.
    Returns True if available, False otherwise.
    Sets global MP_AVAILABLE flag.
    """
    global MP_AVAILABLE
    api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if not api_key:
        logger.warning("Materials Project API key not found. Setting MP_AVAILABLE to False.")
        MP_AVAILABLE = False
        return False

    try:
        # Lightweight probe request
        url = "https://api.materialsproject.org/v2/summary/"
        headers = {"X-API-Key": api_key}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            logger.info("Materials Project API is available.")
            MP_AVAILABLE = True
            return True
        else:
            logger.warning(f"Materials Project API probe failed with status {response.status_code}")
            MP_AVAILABLE = False
            return False
    except Exception as e:
        logger.warning(f"Materials Project API probe exception: {e}")
        MP_AVAILABLE = False
        return False

def fetch_materials_project_data() -> Optional[pd.DataFrame]:
    """Fetch Materials Project data if available."""
    if not MP_AVAILABLE:
        logger.warning("Materials Project not available, skipping fetch.")
        return None

    try:
        # Simulating a fetch
        # response = exponential_backoff_retry("https://api.materialsproject.org/v2/...")
        # if response:
        #     return pd.read_json(response.text)

        logger.warning("Materials Project data fetch not implemented or failed")
        return None
    except Exception as e:
        log_api_error({"source": "Materials Project", "error": str(e)})
        return None

def merge_datasets(df_list: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple DataFrames into a unified DataFrame.
    Assumes all DataFrames have compatible columns or handles missing columns.
    """
    if not df_list:
        logger.warning("No DataFrames to merge. Returning empty DataFrame.")
        return pd.DataFrame()

    # Filter out None or empty DataFrames
    valid_dfs = [df for df in df_list if df is not None and not df.empty]
    
    if not valid_dfs:
        logger.warning("No valid DataFrames to merge. Returning empty DataFrame.")
        return pd.DataFrame()

    try:
        merged_df = pd.concat(valid_dfs, ignore_index=True)
        logger.info(f"Merged {len(valid_dfs)} datasets. Total rows: {len(merged_df)}")
        return merged_df
    except Exception as e:
        logger.error(f"Error merging datasets: {e}")
        raise

def validate_data_integrity(df: pd.DataFrame) -> None:
    """
    Validate data integrity of the merged DataFrame.
    Raises DataFetchError if critical data is missing or invalid.
    Ensures no synthetic fallback code paths exist.
    """
    if df is None or df.empty:
        logger.error("Data validation failed: DataFrame is empty or None.")
        raise DataFetchError("Data validation failed: No data available after fetching. No synthetic fallback allowed.")

    # Check for critical columns (example: composition, target property)
    # Adjust based on actual expected columns
    critical_columns = ["composition", "formation_energy_per_atom"]
    missing_columns = [col for col in critical_columns if col not in df.columns]
    
    if missing_columns:
        logger.error(f"Data validation failed: Missing critical columns: {missing_columns}")
        raise DataFetchError(f"Data validation failed: Missing critical columns: {missing_columns}. No synthetic fallback allowed.")

    # Check for NaN values in critical columns
    for col in critical_columns:
        if df[col].isna().any():
            logger.warning(f"Data integrity warning: Column '{col}' contains NaN values.")
            # Optionally drop or fill NaNs, but raise if critical data is missing
            # For now, we proceed but log the warning

    logger.info("Data integrity validation passed.")

def ingest_materials_data() -> pd.DataFrame:
    """
    Ingest materials data from OQMD, AFLOW, and Materials Project.
    Implements 'Fail Loudly' logic for OQMD/AFLOW.
    Implements fallback logic for Materials Project.
    """
    # Fetch OQMD data
    oqmd_df = fetch_oqmd_data()
    if oqmd_df is None:
        logger.error("OQMD data fetch failed. Raising DataFetchError.")
        raise DataFetchError("OQMD data fetch failed. No synthetic fallback allowed.")

    # Fetch AFLOW data
    aflow_df = fetch_aflow_data()
    if aflow_df is None:
        logger.error("AFLOW data fetch failed. Raising DataFetchError.")
        raise DataFetchError("AFLOW data fetch failed. No synthetic fallback allowed.")

    # Detect MP availability
    detect_mp_availability()

    # Fetch MP data (optional fallback)
    mp_df = fetch_materials_project_data()
    if mp_df is None and MP_AVAILABLE:
        logger.warning("Materials Project data fetch failed. Proceeding without MP data.")
    elif mp_df is None:
        logger.info("Materials Project not available. Proceeding without MP data.")

    # Merge datasets
    df_list = [df for df in [oqmd_df, aflow_df, mp_df] if df is not None]
    merged_df = merge_datasets(df_list)

    # Validate data integrity
    validate_data_integrity(merged_df)

    return merged_df

def save_raw_data(df: pd.DataFrame, output_path: str) -> None:
    """Save raw data to a Parquet file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    logger.info(f"Raw data saved to {output_path}")

def main():
    """Main entry point for ingestion module."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    try:
        merged_df = ingest_materials_data()
        save_raw_data(merged_df, "data/raw/merged_materials_data.parquet")
        logger.info("Ingestion completed successfully.")
    except DataFetchError as e:
        logger.error(f"DataFetchError: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()