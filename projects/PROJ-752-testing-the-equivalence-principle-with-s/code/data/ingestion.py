"""
Data Ingestion Module for SLR Normal Point Data.

Handles downloading data from ILRS/UCS with retry logic and validation.
"""
import os
import time
from typing import List, Optional, Dict, Any
import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry
from utils.logging import get_logger, log_progress, log_error, DataUnavailableError

logger = get_logger(__name__)

def get_satellite_urls() -> Dict[str, str]:
    """
    Retrieve verified URLs for satellite data.
    
    Returns:
        Dictionary mapping satellite ID to URL.
    """
    from config import get_config
    config = get_config()
    return config.verified_dataset_urls

def verify_data_availability() -> bool:
    """
    Verify that at least one data source is reachable.
    
    Returns:
        True if data is available, False otherwise.
        
    Raises:
        DataUnavailableError: If no data sources are configured.
    """
    urls = get_satellite_urls()
    if not urls:
        log_error(logger, "No verified dataset URLs configured in config.py.")
        raise DataUnavailableError("No verified dataset URLs configured.")
        
    # Quick check of first URL
    first_url = next(iter(urls.values()))
    try:
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        response = session.head(first_url, timeout=10)
        if response.status_code == 200:
            log_progress(logger, "Data availability verified.")
            return True
        else:
            log_error(logger, f"Data source returned status {response.status_code}")
            return False
    except requests.RequestException as e:
        log_error(logger, f"Network error checking data availability: {e}")
        return False

def fetch_single_satellite(satellite_id: str, url: str) -> Optional[pd.DataFrame]:
    """
    Fetch data for a single satellite with exponential backoff.
    
    Args:
        satellite_id: Identifier for the satellite.
        url: URL to fetch data from.
        
    Returns:
        DataFrame containing the raw data, or None if failed.
    """
    log_progress(logger, f"Fetching data for {satellite_id} from {url}")
    
    session = requests.Session()
    retry = Retry(
        total=5, 
        backoff_factor=1, 
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    try:
        response = session.get(url, timeout=60)
        response.raise_for_status()
        
        # Assume CSV format for now, adjust based on actual source
        df = pd.read_csv(pd.io.common.StringIO(response.text))
        
        if df.empty:
            log_error(logger, f"Data for {satellite_id} is empty.")
            return None
            
        log_progress(logger, f"Successfully fetched {len(df)} rows for {satellite_id}")
        return df
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            log_error(logger, f"Access forbidden (403) for {satellite_id}. Check credentials or permissions.")
        else:
            log_error(logger, f"HTTP error for {satellite_id}: {e}")
        return None
    except Exception as e:
        log_error(logger, f"Failed to fetch {satellite_id}: {e}")
        return None

def fetch_all_satellites(satellite_ids: List[str]) -> Optional[pd.DataFrame]:
    """
    Fetch and aggregate data for all relevant satellites.
    
    Args:
        satellite_ids: List of satellite identifiers.
        
    Returns:
        Aggregated DataFrame, or None if all fetches failed.
    """
    urls = get_satellite_urls()
    all_data = []
    failed_count = 0
    
    for sat_id in satellite_ids:
        if sat_id not in urls:
            log_error(logger, f"No URL configured for {sat_id}. Skipping.")
            failed_count += 1
            continue
            
        df = fetch_single_satellite(sat_id, urls[sat_id])
        if df is not None:
            # Add satellite ID column
            df['satellite_id'] = sat_id
            all_data.append(df)
        else:
            failed_count += 1
            
    if not all_data:
        log_error(logger, "Failed to fetch data for all satellites.")
        return None
        
    if failed_count > 0:
        log_error(logger, f"Failed to fetch data for {failed_count} satellites, but continuing with {len(all_data)} successful.")
        
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Check minimum points constraint
    if len(combined_df) < 500:
        log_error(logger, f"Total points ({len(combined_df)}) is below minimum threshold (500).")
        # Do not raise here, let preprocessing handle warnings, but log it
        
    return combined_df
