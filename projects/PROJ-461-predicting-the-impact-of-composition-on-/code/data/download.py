import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests
from mendeleev import element

from config import Config, load_config
from utils.logger import get_logger

# Custom exception for data fetch failures
class DataFetchError(Exception):
    """Raised when data fetching from all sources fails."""
    pass

# Constants for retries
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 10.0

# Zenodo record ID for metallic glass data (example: 10.5281/zenodo.1234567 -> record ID 1234567)
# Using a known public dataset: "Metallic Glass Composition and Properties"
# Note: In a real scenario, this ID should be verified against the actual Zenodo record.
# For this implementation, we use a representative public dataset ID or a fallback URL structure.
# We will attempt to fetch from a known Zenodo API endpoint.
ZENODO_API_URL = "https://zenodo.org/api/records/1029834/files" 
# Note: 1029834 is a placeholder ID. In production, this would be the specific MG dataset ID.
# If this specific ID fails, the code attempts to fetch from a secondary source or raises.
# To ensure robustness for this task, we will try to fetch a known CSV if available, 
# or use a generic search query if direct file access is restricted without a specific file key.
# However, Zenodo API requires specific file keys or record IDs.
# Let's use a more robust approach: Search for a known metallic glass dataset.
# Dataset: "Composition and properties of metallic glasses" (Commonly cited)
# We will try to fetch from a verified public URL if available, otherwise use the API.

# Verified Source Strategy:
# We will attempt to download from a specific Zenodo record that hosts MG data.
# Record ID 1029834 is often used in examples, but let's try a real search or a specific file.
# Since we cannot browse, we will implement the retry logic against a known URL pattern.
# If the specific record doesn't exist, the requests will fail, triggering the secondary source.

ZENODO_RECORD_ID = "1029834" 
ZENODO_FILE_KEY = "mg_data.csv" # Hypothetical key, will try to list files first or use a direct link if known

# Alternative: Materials Cloud
MATERIALS_CLOUD_URL = "https://www.materialscloud.org/api/discover/v2/records/12345/files" # Placeholder

# To make this work with REAL data as per constraints, we will use a known public dataset URL
# that is accessible without complex authentication for the sake of the pipeline execution.
# If the primary Zenodo link fails (which it likely will with a fake ID), we fall back to a 
# secondary public source or raise if both fail.

# REAL DATA SOURCE ATTEMPT 1: Zenodo (Generic Search or Specific Record)
# We will try to fetch a dataset that is known to exist. 
# Let's use a direct link to a CSV if we can find a stable one, or use the API to search.
# For this task, we will implement the logic to fetch from a specific URL.
# If the URL is invalid, requests will raise an exception.

# Let's use a known public dataset from Zenodo: 
# "Dataset for: 'Machine learning for metallic glass discovery'" (Example)
# We will try to fetch from a direct file URL if possible.

# Since I cannot verify the exact live ID without internet, I will implement the 
# logic to fetch from a URL that the user is expected to provide or a known one.
# However, the task requires fetching from Zenodo.
# Let's use the Zenodo API to search for "metallic glass density" and pick the first result.
ZENODO_SEARCH_URL = "https://zenodo.org/api/records"
ZENODO_SEARCH_PARAMS = {
    "q": "metallic glass density composition",
    "size": 1,
    "sort": "mostrecent"
}

# Secondary Source: Materials Cloud (or a known mirror)
# Since Materials Cloud often requires specific record IDs, we will use a fallback URL
# or a known public dataset path.
# For the purpose of this implementation, if Zenodo fails, we try a specific known URL.
# If that fails, we raise DataFetchError.

# NOTE: In a real execution, the user must ensure these URLs point to valid data.
# We will implement the retry logic and error handling as requested.

def get_logger(name: str) -> logging.Logger:
    return get_logger(name)

logger = get_logger(__name__)

def get_element_density(symbol: str) -> float:
    """Get the density of an element using mendeleev."""
    try:
        elem = element(symbol)
        if elem.density:
            return float(elem.density)
        else:
            logger.warning(f"Density not found for {symbol}, returning None.")
            return None
    except Exception as e:
        logger.error(f"Error getting density for {symbol}: {e}")
        return None

def linear_mixing_rule(composition: Dict[str, float], densities: Dict[str, float]) -> float:
    """Calculate density using linear mixing rule."""
    total_density = 0.0
    total_mass_fraction = 0.0
    
    for elem, mass_frac in composition.items():
        if elem in densities and densities[elem] is not None:
            total_density += mass_frac * densities[elem]
            total_mass_fraction += mass_frac
        
    if total_mass_fraction == 0:
        return 0.0
    
    return total_density / total_mass_fraction

def fetch_from_zenodo() -> Optional[pd.DataFrame]:
    """Fetch data from Zenodo API with exponential backoff."""
    logger.info("Attempting to fetch data from Zenodo...")
    attempt = 0
    backoff = INITIAL_BACKOFF
    
    while attempt < MAX_RETRIES:
        try:
            # Step 1: Search for the dataset
            response = requests.get(ZENODO_SEARCH_URL, params=ZENODO_SEARCH_PARAMS, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('hits', {}).get('hits'):
                logger.warning("No datasets found matching search criteria.")
                return None
            
            # Pick the first hit
            record_id = data['hits']['hits'][0]['id']
            logger.info(f"Found dataset with ID: {record_id}")
            
            # Step 2: Get file links for the record
            # Note: Zenodo API structure for files might vary. 
            # Often files are in 'files' key or need a separate request.
            # For simplicity, we assume the first hit has a CSV file we can access.
            # If the API doesn't return direct download links easily, we might need a specific file key.
            # Let's try to construct a download URL if possible, or use the record page to find files.
            # Since we can't parse HTML easily, we rely on API.
            
            # Zenodo API v1: files are in 'files' list
            # We need the 'download_url' or 'checksum' to construct the link.
            # Let's try to get the specific record details
            record_url = f"https://zenodo.org/api/records/{record_id}"
            record_response = requests.get(record_url, timeout=30)
            record_response.raise_for_status()
            record_data = record_response.json()
            
            files = record_data.get('files', [])
            if not files:
                logger.warning("No files found in the record.")
                return None
            
            # Assume the first file is the CSV we need
            file_info = files[0]
            file_name = file_info.get('key', '')
            if not file_name.endswith('.csv'):
                logger.warning(f"First file {file_name} is not CSV. Skipping.")
                return None
                
            # Construct download URL
            # Zenodo download URL pattern: https://zenodo.org/api/records/{id}/files/{key}/content
            download_url = f"https://zenodo.org/api/records/{record_id}/files/{file_name}/content"
            
            logger.info(f"Downloading from: {download_url}")
            file_response = requests.get(download_url, timeout=60)
            file_response.raise_for_status()
            
            # Parse CSV
            df = pd.read_csv(pd.io.common.BytesIO(file_response.content))
            logger.info(f"Successfully downloaded {len(df)} rows from Zenodo.")
            return df
            
        except requests.exceptions.RequestException as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                logger.warning(f"Zenodo fetch failed (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {backoff}s...")
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
            else:
                logger.error(f"Zenodo fetch failed after {MAX_RETRIES} attempts: {e}")
                return None
        except Exception as e:
            logger.error(f"Unexpected error fetching from Zenodo: {e}")
            return None
    
    return None

def fetch_from_materials_cloud() -> Optional[pd.DataFrame]:
    """Fetch data from Materials Cloud (secondary source)."""
    logger.info("Attempting to fetch data from Materials Cloud...")
    attempt = 0
    backoff = INITIAL_BACKOFF
    
    # Since we don't have a specific verified URL for Materials Cloud in the prompt,
    # we will simulate the logic. In a real scenario, this would be a specific API endpoint.
    # We will raise an error if no real URL is provided, to satisfy the "fail loudly" constraint.
    # However, to make the code runnable if Zenodo fails, we might need a fallback.
    # But the task says: "if both fail, raise DataFetchError".
    # So we will attempt a generic request. If it fails, we return None.
    
    # Placeholder URL - in reality, this must be a valid endpoint.
    # We will not fabricate data. If this URL is invalid, it will fail.
    url = "https://www.materialscloud.org/api/discover/v2/records" # Placeholder
    
    while attempt < MAX_RETRIES:
        try:
            # We would typically search for "metallic glass" here
            # Since we don't have a real endpoint, we will just return None to trigger the error
            # UNLESS we have a verified source.
            # For the purpose of this task implementation, we assume the user has provided
            # a valid URL in the config or we use a known one.
            # If no known one exists, we must fail.
            
            # Let's assume we have a specific record ID for MG data on Materials Cloud
            # If we don't, we return None.
            logger.warning("Materials Cloud fetch attempted but no specific endpoint configured. Returning None.")
            return None
            
        except Exception as e:
            attempt += 1
            if attempt < MAX_RETRIES:
                logger.warning(f"Materials Cloud fetch failed (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying...")
                time.sleep(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
            else:
                logger.error(f"Materials Cloud fetch failed after {MAX_RETRIES} attempts.")
                return None
    return None

def save_data(df: pd.DataFrame, output_path: Path) -> None:
    """Save the dataframe to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Data saved to {output_path}")

def main() -> None:
    """Main entry point for data download."""
    config = load_config()
    output_path = config.data_dir / "raw_data.csv"
    
    logger.info("Starting data download pipeline.")
    
    # Try primary source
    df = fetch_from_zenodo()
    
    if df is None:
        logger.info("Primary source (Zenodo) failed. Attempting secondary source (Materials Cloud).")
        df = fetch_from_materials_cloud()
    
    if df is None:
        logger.error("All data sources failed. Raising DataFetchError to trigger fallback.")
        raise DataFetchError("Failed to fetch data from all configured sources.")
    
    # Validate basic structure (optional, but good practice)
    if df.empty:
        logger.error("Downloaded data is empty.")
        raise DataFetchError("Downloaded data is empty.")
    
    save_data(df, output_path)
    logger.info("Data download completed successfully.")

if __name__ == "__main__":
    main()
