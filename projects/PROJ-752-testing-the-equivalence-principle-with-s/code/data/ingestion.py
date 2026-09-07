import os
import time
import logging
import hashlib
import requests
from typing import List, Optional, Dict, Any, Tuple
from utils.logging import get_logger, log_error, AnalysisError, DataUnavailableError

# Re-export existing public names for compatibility
# These are defined in the same file or imported from other modules as per project structure
# For this implementation, we assume the base logic for NormalPoint and other types
# exists or is defined here if not already present in the full file.
# Since the prompt implies extending existing files, we add the specific error handling logic.

class NormalPoint:
    """Placeholder for NormalPoint dataclass if not defined elsewhere.
    In a real full-file scenario, this would be the complete definition.
    """
    def __init__(self, satellite_id: str, time: float, range_obs: float, residual: float = 0.0):
        self.satellite_id = satellite_id
        self.time = time
        self.range_obs = range_obs
        self.residual = residual

class DataIngestionError(AnalysisError):
    """Custom exception for data ingestion failures."""
    pass

logger = get_logger(__name__)

def validate_config() -> None:
    """
    Read config.paths.verified_datasets and ensure data/verified_datasets.yaml exists.
    Raises DataUnavailableError if missing.
    """
    from config import get_config
    config = get_config()
    if not hasattr(config, 'paths') or not hasattr(config.paths, 'verified_datasets'):
        raise DataUnavailableError("Configuration missing 'paths.verified_datasets' key.")
    
    path = config.paths.verified_datasets
    if not os.path.exists(path):
        raise DataUnavailableError(f"Verified datasets file not found at: {path}")

def get_satellite_urls() -> Dict[str, str]:
    """
    Returns a dictionary mapping satellite IDs to their data URLs.
    In a real implementation, this would parse the verified_datasets.yaml.
    """
    # Placeholder implementation to satisfy signature
    return {
        "LAGEOS-1": "https://example.com/lageos1.dat",
        "LAGEOS-2": "https://example.com/lageos2.dat",
        "STARLETTE": "https://example.com/starlette.dat"
    }

def fetch_satellite_data(satellite_id: str, max_retries: int = 5) -> bytes:
    """
    Fetches satellite data with exponential backoff retry logic.
    Handles 403 errors and "Insufficient Data" warnings explicitly.
    """
    urls = get_satellite_urls()
    if satellite_id not in urls:
        raise DataUnavailableError(f"No URL configured for satellite: {satellite_id}")
    
    url = urls[satellite_id]
    attempt = 0
    backoff = 1.0
    
    while attempt < max_retries:
        try:
            logger.info(f"Fetching data for {satellite_id} from {url} (Attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=30)
            
            # Handle 403 Forbidden specifically
            if response.status_code == 403:
                error_msg = f"HTTP 403 Forbidden: Access denied for {satellite_id}. " \
                            "Check API credentials or data availability."
                logger.error(error_msg)
                # Do not retry on 403 as it is a client permission error
                raise DataIngestionError(error_msg)
            
            if response.status_code == 200:
                return response.content
            
            # Handle other errors with backoff
            if response.status_code >= 500:
                logger.warning(f"Server error {response.status_code} for {satellite_id}. Retrying...")
            else:
                logger.warning(f"Unexpected status code {response.status_code} for {satellite_id}.")
            
            attempt += 1
            time.sleep(backoff)
            backoff *= 2  # Exponential backoff
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {satellite_id}: {e}")
            attempt += 1
            if attempt >= max_retries:
                raise DataIngestionError(f"Failed to fetch {satellite_id} after {max_retries} attempts.")
            time.sleep(backoff)
            backoff *= 2
    
    raise DataIngestionError(f"Failed to fetch {satellite_id} after {max_retries} retries.")

def parse_slr_file(raw_content: bytes) -> List[NormalPoint]:
    """
    Parses raw SLR file content into a list of NormalPoint objects.
    """
    # Placeholder parsing logic - in reality, this would parse the specific SLR format
    points = []
    # Simulate parsing logic for demonstration of the function signature
    # In a real scenario, this would iterate over lines and parse fields
    return points

def aggregate_satellites(satellite_ids: List[str]) -> List[NormalPoint]:
    """
    Orchestrates the loop over satellites: fetch, parse, and aggregate.
    Checks for "Insufficient Data" (<500 points) and logs a warning.
    """
    all_points = []
    min_points_threshold = 500
    
    for sat_id in satellite_ids:
        try:
            raw_data = fetch_satellite_data(sat_id)
            points = parse_slr_file(raw_data)
            
            # Check for insufficient data
            if len(points) < min_points_threshold:
                warning_msg = f"Insufficient Data: {sat_id} has only {len(points)} points " \
                              f"(threshold: {min_points_threshold}). Proceeding with caution."
                logger.warning(warning_msg)
                # We do not raise an error here as per requirement to just warn,
                # but we could choose to skip or flag the satellite.
                # The requirement says "Add error handling for ... warnings", implying we log it.
            
            all_points.extend(points)
            logger.info(f"Aggregated {len(points)} points for {sat_id}.")
            
        except DataIngestionError as e:
            log_error(logger, f"Skipping {sat_id} due to ingestion error: {e}")
            # Continue with other satellites
    
    if not all_points:
        raise DataUnavailableError("No valid data points collected from any satellite.")
    
    return all_points

def verify_data_availability_wrapper(satellite_ids: List[str]) -> bool:
    """
    Wrapper to verify data availability without full processing.
    Returns True if data seems available, False otherwise.
    """
    try:
        validate_config()
        for sat_id in satellite_ids:
            # Quick check if URL exists (does not download full data)
            if sat_id not in get_satellite_urls():
                return False
        return True
    except DataUnavailableError:
        return False

def fetch_all_satellites(satellite_ids: Optional[List[str]] = None) -> List[NormalPoint]:
    """
    Main entry point to fetch all required satellite data.
    """
    if satellite_ids is None:
        # Default set based on project specs
        satellite_ids = ["LAGEOS-1", "LAGEOS-2", "STARLETTE"]
    
    return aggregate_satellites(satellite_ids)
