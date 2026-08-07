import os
import sys
import pandas as pd
from typing import Optional
from utils.logging import get_logger
from utils.config import get_config

logger = get_logger(__name__)

# Error code constant
DATA_SOURCE_MISSING = 1
SUCCESS_STATUS = "SUCCESS"
NO_DATA_STATUS = "NO_DATA"

def download_dataset(url: Optional[str] = None) -> tuple:
    """
    Fetches the HEA composition dataset from the verified URL or user-provided path.
    
    Logic (Strict "Fail Loudly" per T108):
    1. Attempt to fetch from verified URL in config.
    2. If the user-provided CSV (data/raw/heas_raw.csv) is specified or implied by config,
       validate its existence and schema.
    3. If the file is missing or invalid, raise FileNotFoundError or ValidationError immediately.
    4. NO synthetic fallbacks, NO mock data, NO silent returns of empty DataFrames.
    5. If data is found and valid, return status SUCCESS.
    
    Args:
        url: Optional override URL. If None, reads from config (research.verified_datasets).
    
    Returns:
        tuple: (DataFrame, status_string, list of attempted URLs)
            - DataFrame: The loaded data if SUCCESS.
            - status_string: "SUCCESS".
            - list of attempted URLs: For logging purposes.
    
    Raises:
        FileNotFoundError: If the required dataset file is missing.
        ValueError: If the dataset is empty or invalid.
        RuntimeError: If a specific error occurs during download.
    """
    attempted_urls = []
    df = None
    status = NO_DATA_STATUS
    
    # Priority 1: Verified URL from config
    if url is None:
        config = get_config()
        if 'research' in config and 'verified_datasets' in config['research']:
            dataset_key = 'hea_compositions'
            if dataset_key in config['research']['verified_datasets']:
                url = config['research']['verified_datasets'][dataset_key]
            else:
                logger.warning(f"Key '{dataset_key}' not found in config. Falling back to local file check.")
                url = None
        else:
            logger.warning("Config missing 'research.verified_datasets'. Falling back to local file check.")
            url = None

    # Define the expected local path for the user-provided dataset
    # This aligns with T008 and T098 which validate data/raw/heas_raw.csv
    local_path = "data/raw/heas_raw.csv"
    
    # If a URL is provided that looks like a local file path, treat it as such
    if url and (url.startswith('/') or url.startswith('data/')):
        local_path = url
        url = None # Clear URL to avoid double attempt

    sources_to_try = []
    if url:
        sources_to_try.append(url)
    
    # We do NOT add fallback open sources here. T108 requires strict failure.
    # We only try the config URL (if real http) and the local file.

    # Attempt 1: Config URL (if it's a real http(s) link)
    if sources_to_try:
        for source_url in sources_to_try:
            attempted_urls.append(source_url)
            logger.info(f"Attempting to download from: {source_url}")
            
            try:
                os.makedirs("data/raw", exist_ok=True)
                output_path = "data/raw/hea_compositions.csv"
                
                if source_url.endswith('.csv'):
                    df = pd.read_csv(source_url)
                elif source_url.endswith('.json'):
                    df = pd.read_json(source_url)
                else:
                    try:
                        df = pd.read_csv(source_url)
                    except:
                        logger.warning(f"Could not parse {source_url} as CSV or JSON. Skipping.")
                        continue

                if df is not None and len(df) > 0:
                    df.to_csv(output_path, index=False)
                    logger.info(f"Dataset downloaded and saved to {output_path} with {len(df)} rows.")
                    status = SUCCESS_STATUS
                    return df, status, attempted_urls
                else:
                    logger.warning(f"Downloaded empty dataset from {source_url}.")
                    # Fail loudly if the URL was supposed to have data but was empty
                    raise ValueError(f"Dataset from {source_url} is empty.")

            except Exception as e:
                logger.error(f"Failed to download dataset from {source_url}: {e}")
                # Re-raise to fail loudly if it was the primary source
                if source_url == sources_to_try[0]:
                    raise RuntimeError(f"Primary data source failed: {e}")
                continue

    # Attempt 2: Local User-Provided File (The primary expected source per FR-001)
    if os.path.exists(local_path):
        attempted_urls.append(local_path)
        logger.info(f"Found local dataset at: {local_path}")
        try:
            df = pd.read_csv(local_path)
            if df is not None and len(df) > 0:
                # Ensure it's in the standard raw location if it wasn't there
                if local_path != "data/raw/hea_compositions.csv":
                    os.makedirs("data/raw", exist_ok=True)
                    df.to_csv("data/raw/hea_compositions.csv", index=False)
                logger.info(f"Loaded local dataset with {len(df)} rows.")
                status = SUCCESS_STATUS
                return df, status, attempted_urls
            else:
                raise ValueError(f"Local dataset at {local_path} is empty.")
        except Exception as e:
            logger.error(f"Failed to load local dataset: {e}")
            raise FileNotFoundError(f"Local dataset at {local_path} is invalid or empty: {e}")
    else:
        # CRITICAL: Fail loudly. No fallback.
        logger.error(f"CRITICAL: Required dataset file not found: {local_path}")
        raise FileNotFoundError(f"CRITICAL: Required dataset file not found: {local_path}. "
                                f"Please provide the HEA yield strength data at {local_path}. "
                                f"Synthetic fallbacks are disabled per T108.")

    # If we reach here, something went wrong with the flow (should be caught above)
    raise RuntimeError("Data acquisition failed: No valid source found and no fallback available.")

def main():
    """
    Entry point for the downloader script.
    Executes the download and prints the status.
    Exits with code 0 on success, non-zero on failure.
    """
    try:
        df, status, attempts = download_dataset()
        
        print(f"Data Acquisition Status: {status}")
        print(f"Attempted URLs/Paths: {attempts}")
        
        if status == SUCCESS_STATUS:
            print(f"Downloaded {len(df)} rows.")
            sys.exit(0)
        else:
            # This branch should theoretically not be reached due to "Fail Loudly"
            print("No data found. Exiting with error.")
            sys.exit(DATA_SOURCE_MISSING)
            
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(DATA_SOURCE_MISSING)
    except ValueError as e:
        print(f"VALIDATION ERROR: {e}")
        sys.exit(DATA_SOURCE_MISSING)
    except RuntimeError as e:
        print(f"RUNTIME ERROR: {e}")
        sys.exit(DATA_SOURCE_MISSING)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(DATA_SOURCE_MISSING)

if __name__ == "__main__":
    main()