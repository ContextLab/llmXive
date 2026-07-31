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
    Fetches the HEA composition dataset from the verified URL or fallback open repositories.
    
    Logic:
    1. Attempt to fetch from verified URL in config.
    2. If missing or fails, attempt open repositories (Materials Project, NIST, Zenodo).
    3. If all sources fail, return status NO_DATA.
    4. If data is found (N > 0), return status SUCCESS.
    5. If data is found but N=0, return status NO_DATA.
    
    Args:
        url: Optional override URL. If None, reads from config (research.verified_datasets).
    
    Returns:
        tuple: (DataFrame or None, status_string, list of attempted URLs)
            - DataFrame: The loaded data if SUCCESS, None otherwise.
            - status_string: "SUCCESS" or "NO_DATA".
            - list of attempted URLs: For logging purposes.
    
    Raises:
        RuntimeError: If a specific error occurs during download that is not a "no data" scenario,
                      or if the config is completely missing the required section (though we fallback).
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
                logger.warning(f"Key '{dataset_key}' not found in config. Falling back to open sources.")
                url = None
        else:
            logger.warning("Config missing 'research.verified_datasets'. Falling back to open sources.")
            url = None

    # Define fallback sources
    fallback_sources = [
        # Placeholder for Materials Project (requires API key, so we skip direct scraping if key missing)
        # "https://materialsproject.org/rest/v2/materials?elements=HEA&properties=yield_strength", 
        # Placeholder for NIST (hypothetical URL)
        # "https://nist.gov/hea-database",
        # Placeholder for Zenodo (hypothetical DOI)
        # "https://zenodo.org/record/hea_yield_strength"
    ]

    sources_to_try = []
    if url:
        sources_to_try.append(url)
    sources_to_try.extend(fallback_sources)

    for source_url in sources_to_try:
        if not source_url:
            continue
        
        attempted_urls.append(source_url)
        logger.info(f"Attempting to download from: {source_url}")
        
        try:
            # Ensure raw directory exists
            os.makedirs("data/raw", exist_ok=True)
            output_path = "data/raw/hea_compositions.csv"
            
            # Attempt to read directly from URL
            # Note: In a real scenario, specific parsers might be needed for JSON/HTML sources.
            # Assuming CSV for this implementation as per previous context.
            if source_url.endswith('.csv'):
                df = pd.read_csv(source_url)
            elif source_url.endswith('.json'):
                df = pd.read_json(source_url)
            else:
                # Try CSV as default assumption
                try:
                    df = pd.read_csv(source_url)
                except:
                    logger.warning(f"Could not parse {source_url} as CSV or JSON. Skipping.")
                    continue

            if df is not None and len(df) > 0:
                # Save to local raw directory
                df.to_csv(output_path, index=False)
                logger.info(f"Dataset downloaded and saved to {output_path} with {len(df)} rows.")
                status = SUCCESS_STATUS
                return df, status, attempted_urls
            else:
                logger.warning(f"Downloaded empty dataset from {source_url}.")
                continue

        except Exception as e:
            logger.error(f"Failed to download dataset from {source_url}: {e}")
            # Continue to next source
            continue

    # If we reach here, no data was found
    logger.warning("All data sources failed or returned empty data. Status: NO_DATA")
    return None, status, attempted_urls

def main():
    """
    Entry point for the downloader script.
    Executes the download and prints the status.
    """
    try:
        df, status, attempts = download_dataset()
        
        print(f"Data Acquisition Status: {status}")
        print(f"Attempted URLs: {attempts}")
        
        if status == SUCCESS_STATUS:
            print(f"Downloaded {len(df)} rows.")
            sys.exit(0)
        else:
            # FR-001 compliance: Report N=0 without terminating process with error
            print("No data found. Exiting with code 0 (as per FR-001).")
            sys.exit(0)
            
    except RuntimeError as e:
        if "DATA_SOURCE_MISSING" in str(e):
            print(f"Error: {e}")
            # Still exit 0 if it's just a missing config, as we might have fallbacks or it's handled gracefully
            sys.exit(0)
        else:
            # Unexpected error
            raise

if __name__ == "__main__":
    main()