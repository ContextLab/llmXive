"""
Data download module for Metallic Glass Density prediction.
Fetches data from Zenodo (primary) and Materials Cloud (secondary).
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import pandas as pd

from utils.logger import get_logger
from config import load_config

# Custom exception for data fetching failures
class DataFetchError(Exception):
    """Raised when data fetching fails from all sources."""
    pass

# Constants
ZENODO_RECORD_ID = "1040665"  # Metallic Glass Database (example ID, replace with actual if known)
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
MATERIALS_CLOUD_URL = "https://www.materialscloud.org/api/discover"  # Placeholder, adjust if specific endpoint known

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
BACKOFF_MULTIPLIER = 2.0

logger = get_logger(__name__)
config = load_config()

def get_element_density(element_symbol: str) -> float:
    """
    Get the density of an element from Mendeleev.
    
    Args:
        element_symbol: Chemical symbol (e.g., 'Fe', 'Zr')
        
    Returns:
        Density in g/cm³
        
    Raises:
        KeyError: If element is not found
    """
    try:
        from mendeleev import element
        elem = element(element_symbol)
        if elem.density is None:
            # Fallback for elements without density data
            logger.warning(f"Density not found for {element_symbol}, using placeholder 0.0")
            return 0.0
        return elem.density
    except Exception as e:
        logger.error(f"Failed to get density for {element_symbol}: {e}")
        raise

def linear_mixing_rule(composition: Dict[str, float]) -> float:
    """
    Calculate density using the linear mixing rule: ρ = Σ(w_i × ρ_i)
    
    Args:
        composition: Dict mapping element symbols to mass fractions
        
    Returns:
        Calculated density in g/cm³
    """
    total_density = 0.0
    for element, mass_frac in composition.items():
        density = get_element_density(element)
        total_density += mass_frac * density
    return total_density

def fetch_from_zenodo() -> Optional[pd.DataFrame]:
    """
    Fetch metallic glass data from Zenodo.
    
    Returns:
        DataFrame with raw data or None if fetch fails
    """
    logger.info(f"Attempting to fetch data from Zenodo (Record ID: {ZENODO_RECORD_ID})")
    
    # Note: The actual file download requires finding the specific file ID.
    # This implementation assumes we can list files and download the first CSV found.
    # In a real scenario, we might need to hardcode the file_id if known.
    
    try:
        # Step 1: Get record metadata to find file IDs
        response = requests.get(ZENODO_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        files = data.get('files', [])
        if not files:
            logger.warning("No files found in Zenodo record.")
            return None
        
        # Find the first CSV file
        csv_file = None
        for f in files:
            if f.get('key', '').endswith('.csv'):
                csv_file = f
                break
        
        if not csv_file:
            logger.warning("No CSV file found in Zenodo record.")
            return None
        
        # Step 2: Download the file
        download_url = csv_file.get('links', {}).get('self')
        if not download_url:
            logger.warning("No download URL found for CSV file.")
            return None
        
        logger.info(f"Downloading file from: {download_url}")
        file_response = requests.get(download_url, timeout=300) # Longer timeout for file download
        file_response.raise_for_status()
        
        # Parse CSV from content
        df = pd.read_csv(pd.io.common.BytesIO(file_response.content))
        logger.info(f"Successfully fetched {len(df)} rows from Zenodo.")
        return df
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching from Zenodo: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from Zenodo: {e}")
        return None

def fetch_from_materials_cloud() -> Optional[pd.DataFrame]:
    """
    Fetch metallic glass data from Materials Cloud.
    
    Returns:
        DataFrame with raw data or None if fetch fails
    """
    logger.info("Attempting to fetch data from Materials Cloud")
    
    try:
        # This is a placeholder implementation. 
        # The actual API usage depends on the specific dataset and endpoint.
        # We will simulate a request to a known dataset or return None if not found.
        
        # Example: If there's a specific dataset ID, use it.
        # For now, we'll try a generic search or return None if no specific endpoint is known.
        # Since we cannot guess the exact API structure without more info, 
        # we will attempt a simple GET to a potential endpoint or return None.
        
        # NOTE: In a real implementation, you would need the specific dataset ID or search query.
        # For this task, we assume a generic fallback or return None if the primary source fails.
        # If a specific URL is provided in the project specs, use it here.
        
        # Attempting a generic request (this might need adjustment based on real API)
        # Using a placeholder URL that might need to be updated
        url = "https://www.materialscloud.org/api/discover?format=json&dataset_type=metallic_glass"
        
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            # Parse the response into a DataFrame
            # This depends heavily on the actual API response structure
            # Assuming a 'results' key with a list of items
            if 'results' in data:
                df = pd.DataFrame(data['results'])
                logger.info(f"Successfully fetched {len(df)} rows from Materials Cloud.")
                return df
            else:
                logger.warning("Unexpected response structure from Materials Cloud.")
                return None
        else:
            logger.warning(f"Materials Cloud returned status {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching from Materials Cloud: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching from Materials Cloud: {e}")
        return None

def save_data(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save DataFrame to CSV.
    
    Args:
        df: DataFrame to save
        output_path: Path to save the file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Data saved to {output_path} ({len(df)} rows)")

def main() -> None:
    """
    Main function to orchestrate data download.
    Implements exponential backoff and fallback logic.
    """
    logger.info("Starting data download process")
    
    output_path = config.data_dir / "raw_data.csv"
    
    # Try primary source (Zenodo) with retries
    data = None
    last_error = None
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.info(f"Attempt {attempt}/{MAX_RETRIES} to fetch from Zenodo")
            data = fetch_from_zenodo()
            if data is not None:
                break
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt} failed: {e}")
        
        if attempt < MAX_RETRIES:
            backoff_time = INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** (attempt - 1))
            logger.info(f"Waiting {backoff_time:.2f}s before retry...")
            time.sleep(backoff_time)
    
    # If primary source failed, try secondary source (Materials Cloud)
    if data is None:
        logger.info("Primary source (Zenodo) failed. Attempting secondary source (Materials Cloud).")
        try:
            data = fetch_from_materials_cloud()
        except Exception as e:
            logger.error(f"Secondary source (Materials Cloud) also failed: {e}")
            last_error = e
    
    if data is None:
        logger.error("All data sources failed.")
        raise DataFetchError("Failed to fetch data from all sources (Zenodo and Materials Cloud).")
    
    # Save the fetched data
    save_data(data, output_path)
    logger.info("Data download process completed successfully.")

if __name__ == "__main__":
    main()