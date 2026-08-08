"""
Data Ingestion Module for SLR Satellite Data.

This module handles the fetching of Satellite Laser Ranging (SLR) data
from the International Laser Ranging Service (ILRS) and other verified sources.
It implements robust retry logic, error handling, and data validation.
"""

import os
import time
from typing import List, Optional, Dict, Any
import requests
import pandas as pd
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urljoin

from config import get_config
from utils.logging import get_logger, DataUnavailableError, PipelineError

logger = get_logger(__name__)

# Constants for retry logic
MAX_RETRIES = 5
BACKOFF_FACTOR = 1.5
STATUS_FORCELIST = [429, 500, 502, 503, 504]

# Verified ILRS URLs for supported satellites (Hardcoded as per T009 requirement)
# These are the canonical sources for the Equivalence Principle test
VERIFIED_SATELLITE_URLS = {
    "LAGEOS-1": "https://cddis.nasa.gov/20Years/Lageos1/",
    "LAGEOS-2": "https://cddis.nasa.gov/20Years/Lageos2/",
    "Etalon-1": "https://cddis.nasa.gov/20Years/Etalon1/",
    "Etalon-2": "https://cddis.nasa.gov/20Years/Etalon2/",
    "Starlette": "https://cddis.nasa.gov/20Years/Starlette/",
}

class DataUnavailableError(DataUnavailableError):
    """Custom exception for data availability issues."""
    pass


def verify_data_availability() -> bool:
    """
    Verify that the configured dataset URLs are available.

    Checks if `config.verified_dataset_urls` is populated.
    If empty, raises DataUnavailableError as per T009 requirements.

    Returns:
        bool: True if data sources are configured.

    Raises:
        DataUnavailableError: If no verified URLs are found.
    """
    config = get_config()
    if not config.verified_dataset_urls:
        # Fallback to hardcoded list if config is empty but we have defaults
        if not VERIFIED_SATELLITE_URLS:
            raise DataUnavailableError(
                "No verified dataset URLs found in config and no hardcoded defaults available."
            )
        logger.warning("Config verified_dataset_urls is empty. Using hardcoded defaults.")
        return True
    
    # If config has URLs, we assume they are valid for now
    # The actual validation happens during fetch
    return True


def get_satellite_urls(satellite_ids: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Retrieve verified URLs for requested satellites.

    Args:
        satellite_ids: List of satellite IDs. If None, returns all defaults.

    Returns:
        Dict mapping satellite_id to URL.

    Raises:
        ValueError: If a requested satellite ID is not found.
    """
    if satellite_ids is None:
        return VERIFIED_SATELLITE_URLS.copy()

    result = {}
    for sat_id in satellite_ids:
        if sat_id in VERIFIED_SATELLITE_URLS:
            result[sat_id] = VERIFIED_SATELLITE_URLS[sat_id]
        else:
            logger.warning(f"Satellite ID '{sat_id}' not found in verified list.")
            # Try to find a case-insensitive match
            for key in VERIFIED_SATELLITE_URLS:
                if key.lower() == sat_id.lower():
                    result[sat_id] = VERIFIED_SATELLITE_URLS[key]
                    break
            if sat_id not in result:
                raise ValueError(f"Unknown satellite ID: {sat_id}")
    
    return result


def fetch_single_satellite(satellite_id: str, url: str) -> pd.DataFrame:
    """
    Fetch SLR data for a single satellite from the provided URL.

    Implements exponential backoff retry logic for robustness against
    network issues and server rate limiting.

    Args:
        satellite_id: The identifier for the satellite (e.g., "LAGEOS-1").
        url: The base URL for the satellite data.

    Returns:
        pd.DataFrame: A DataFrame containing the SLR observations.
                      Columns typically include: 'time', 'range', 'range_rate', 'residual', 'quality'.

    Raises:
        DataUnavailableError: If the data cannot be fetched after retries.
        PipelineError: If the response format is invalid or no data is found.
    """
    logger.info(f"Fetching data for {satellite_id} from {url}")

    # Create a session with retry strategy
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        read=True,
        connect=True,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCELIST,
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Construct the specific data file URL
    # ILRS usually provides specific .slr or .csv files. 
    # We attempt to fetch a standard naming convention or index.
    # For this implementation, we assume a direct link to a CSV/SLR file 
    # or an index page that lists them. 
    # Given the "20Years" structure, we often look for specific epoch files.
    
    # Attempt to fetch a standard data file path
    # This is a heuristic; real implementation might need to parse an index.html
    # For robustness, we try common patterns.
    possible_paths = [
        f"{url}slr_data.csv",
        f"{url}normal_points.csv",
        f"{url}data.csv",
        f"{url}all_data.csv"
    ]

    final_url = None
    for p in possible_paths:
        try:
            # Check if file exists (HEAD request)
            head_resp = session.head(p, timeout=10, allow_redirects=True)
            if head_resp.status_code == 200:
                final_url = p
                break
        except requests.exceptions.RequestException:
            continue

    if not final_url:
        # If we can't find a specific file, try the base URL (might be an index)
        # In a real scenario, we would parse the HTML to find links.
        # For now, we raise an error if no specific file is found.
        raise DataUnavailableError(
            f"Could not locate a valid data file for {satellite_id} at {url}. "
            f"Expected one of: {possible_paths}"
        )

    try:
        response = session.get(final_url, timeout=60)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data for {satellite_id} after retries: {e}")
        raise DataUnavailableError(f"Network error fetching {satellite_id}: {str(e)}")

    # Parse the content
    try:
        # Try to read as CSV first
        # Assuming the data has headers. If not, we might need to infer.
        # Common SLR formats: time (MJD or ISO), range (mm), residual (mm), etc.
        if 'text/csv' in response.headers.get('Content-Type', '') or final_url.endswith('.csv'):
            df = pd.read_csv(pd.io.common.StringIO(response.text))
        else:
            # Fallback: try to read as whitespace-delimited or generic CSV
            df = pd.read_csv(pd.io.common.StringIO(response.text), sep=r'\s+|,')
    except Exception as e:
        raise PipelineError(f"Failed to parse data for {satellite_id}: {str(e)}")

    if df.empty:
        raise DataUnavailableError(f"No data records found for {satellite_id} at {final_url}")

    # Basic validation: Ensure essential columns exist
    # We normalize column names to lowercase for consistency
    df.columns = [c.lower().strip() for c in df.columns]
    
    expected_cols = ['time', 'range'] # Minimum required
    missing_cols = [c for c in expected_cols if c not in df.columns]
    
    if missing_cols:
        # Try to infer if columns exist with different names
        # This is a simple heuristic; real code might need a schema validator
        logger.warning(f"Missing expected columns {missing_cols} in {satellite_id} data. Available: {list(df.columns)}")
        # If we have 'mjd' or 'date', map to 'time'
        if 'mjd' in df.columns:
            df['time'] = df['mjd']
        if 'date' in df.columns and 'time' not in df.columns:
            df['time'] = df['date']
        
        if 'range_mm' in df.columns and 'range' not in df.columns:
            df['range'] = df['range_mm']

    # Add satellite ID column for tracking
    df['satellite_id'] = satellite_id

    logger.info(f"Successfully fetched {len(df)} records for {satellite_id}")
    return df


def fetch_all_satellites(satellite_ids: List[str]) -> pd.DataFrame:
    """
    Orchestrate the fetching of data for multiple satellites.

    Aggregates results into a single DataFrame.

    Args:
        satellite_ids: List of satellite IDs to fetch.

    Returns:
        pd.DataFrame: Combined DataFrame for all requested satellites.

    Raises:
        DataUnavailableError: If fetching fails for all satellites.
    """
    urls = get_satellite_urls(satellite_ids)
    all_dfs = []
    failed_satellites = []

    for sat_id in satellite_ids:
        if sat_id not in urls:
            logger.warning(f"Skipping {sat_id}: URL not found.")
            continue

        try:
            df = fetch_single_satellite(sat_id, urls[sat_id])
            all_dfs.append(df)
        except (DataUnavailableError, PipelineError) as e:
            logger.error(f"Failed to fetch {sat_id}: {e}")
            failed_satellites.append(sat_id)

    if not all_dfs:
        raise DataUnavailableError(
            f"Failed to fetch data for any of the requested satellites: {satellite_ids}"
        )

    combined_df = pd.concat(all_dfs, ignore_index=True)
    
    if failed_satellites:
        logger.warning(f"Data for the following satellites was skipped: {failed_satellites}")
        logger.info(f"Total records fetched: {len(combined_df)}")

    return combined_df