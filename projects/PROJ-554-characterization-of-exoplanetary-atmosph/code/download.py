import os
import logging
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from config import get_config
from utils import setup_logging, DataFetchError, retry_on_failure
from api_config import QUERY_PARAMS

# Constants
API_BASE_URL = "https://archive.exoplanetarchive.ipac.caltech.edu/"
API_ENDPOINT = "api"
TIMEOUT_SECONDS = 30

def _setup_download_logger() -> logging.Logger:
    """
    Sets up a dedicated logger for download operations.
    Ensures logs are written to logs/download.log.
    """
    logger = logging.getLogger("download")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "download.log"

    # File handler for detailed logs
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Console handler for immediate feedback
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

logger = _setup_download_logger()

@retry_on_failure(max_retries=3, backoff_factor=2)
def _fetch_api_data(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Internal helper to fetch data from the API with retry logic.
    Handles response checking and logging.
    """
    url = f"{API_BASE_URL}{API_ENDPOINT}"
    logger.debug(f"Sending request to {url} with params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        
        # Log response size
        content_length = response.headers.get('Content-Length')
        if content_length:
            logger.debug(f"Received response of {content_length} bytes")
        
        data = response.json()
        if not data:
            logger.warning("API returned an empty dataset.")
            return []
        
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise DataFetchError(f"Failed to fetch data from API: {str(e)}") from e

def classify_planet_category(radius: float, t_eq: float, radius_unit: str = "R_Jup") -> str:
    """
    Classifies planet category based on radius and equilibrium temperature.
    
    Logic:
    - "Hot Jupiter": Radius > 0.8 R_Jup AND T_eq > 1000K
    - "Temperate Super-Earth": Radius < 1.6 R_E AND T_eq < 1000K
    - "Other": Does not fit the above criteria strictly (for metadata tagging only)
    
    Note: 1 R_Jup ≈ 11.2 R_E.
    """
    # Convert radius to R_E if necessary for comparison
    # Assuming input radius is in R_Jup unless specified otherwise
    radius_in_rjup = radius
    if radius_unit == "R_E":
        radius_in_rjup = radius / 11.2
    
    if radius_in_rjup > 0.8 and t_eq > 1000:
        return "Hot Jupiter"
    elif radius_in_rjup < (1.6 / 11.2) and t_eq < 1000:
        return "Temperate Super-Earth"
    else:
        return "Other"

def fetch_spectrum_data(planet_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetches spectrum data for a specific planet from the NASA Exoplanet Archive.
    Includes logging for API response handling.
    """
    logger.info(f"Fetching spectrum data for planet: {planet_name}")
    
    params = {
        "PLANET_NAME": planet_name,
        "FORMAT": "json",
        "COLUMN": "TRANSMISSION_SPECTRUM_DATA"
    }
    
    try:
        data = _fetch_api_data(params)
        if data:
            logger.info(f"Successfully retrieved data for {planet_name}: {len(data)} entries")
            return data[0] if isinstance(data, list) else data
        else:
            logger.warning(f"No data found for {planet_name}")
            return None
    except DataFetchError as e:
        logger.error(f"Failed to fetch data for {planet_name}: {e}")
        return None

def download_all_spectra() -> pd.DataFrame:
    """
    Downloads ALL available spectra matching the criteria in QUERY_PARAMS
    without any resolution or radius filtering.
    
    Returns:
        pd.DataFrame: A DataFrame containing the raw metadata and spectrum references.
    """
    logger.info("Starting download of all spectra matching criteria...")
    start_time = time.time()
    
    # Prepare query parameters from api_config
    params = QUERY_PARAMS.copy()
    params["FORMAT"] = "json"
    
    try:
        raw_data = _fetch_api_data(params)
    except DataFetchError as e:
        logger.critical(f"Critical failure during download: {e}")
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Download completed in {elapsed:.2f} seconds. Total records: {len(raw_data)}")
    
    if not raw_data:
        logger.warning("No records found matching the criteria.")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(raw_data)
    
    # Log column discovery
    logger.debug(f"Discovered columns: {list(df.columns)}")
    
    # Ensure required columns exist or are initialized
    required_cols = ['PLANET_NAME', 'EQ_TEMP', 'HOST_STAR_METALLICITY', 
                     'SPECTRAL_RESOLUTION', 'SIGNAL_TO_NOISE_RATIO', 
                     'RADIUS', 'RADIUS_UNIT', 'INSTRUMENT', 'WAVELENGTH_RANGE']
    
    for col in required_cols:
        if col not in df.columns:
            # Try to find case-insensitive match
            matches = [c for c in df.columns if c.lower() == col.lower()]
            if matches:
                df[col] = df[matches[0]]
                logger.info(f"Renamed column {matches[0]} to {col}")
            else:
                df[col] = None
                logger.warning(f"Column {col} not found in API response, initializing as None")
    
    # Apply classification
    logger.info("Classifying planet categories...")
    df['planet_category'] = df.apply(
        lambda row: classify_planet_category(
            row['RADIUS'], 
            row['EQ_TEMP'], 
            row.get('RADIUS_UNIT', 'R_Jup')
        ), 
        axis=1
    )
    
    logger.info(f"Classification complete. Categories: {df['planet_category'].value_counts().to_dict()}")
    
    return df

def save_metadata_csv(df: pd.DataFrame, output_path: str = "data/processed/metadata.csv") -> None:
    """
    Saves the metadata DataFrame to a CSV file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving metadata to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} rows to {output_path}")

def count_unique_planets(df: pd.DataFrame) -> int:
    """
    Counts unique planets from the dataset.
    """
    count = df['PLANET_NAME'].nunique()
    logger.info(f"Unique planet count: {count}")
    return count

def validate_sample_size(count: int) -> Dict[str, Any]:
    """
    Validates the sample size against the target range (30-45).
    Logs warnings if outside range but returns 'proceed' status.
    
    Returns:
        Dict containing count and validation_status.
    """
    logger.info(f"Validating sample size: {count}")
    
    if count < 30 or count > 45:
        logger.warning(f"Sample size {count} is outside the target range (30-45). Proceeding anyway.")
        status = "proceed"
    else:
        logger.info(f"Sample size {count} is within the target range (30-45).")
        status = "proceed"
    
    return {
        "count": count,
        "validation_status": status
    }

def main():
    """
    Main entry point for the download module.
    Orchestrates the download, processing, and saving of exoplanet data.
    """
    logger.info("=== Starting Exoplanet Data Download Pipeline ===")
    
    try:
        # 1. Download all spectra
        df = download_all_spectra()
        
        if df.empty:
            logger.error("No data downloaded. Exiting.")
            return
        
        # 2. Save metadata CSV
        save_metadata_csv(df)
        
        # 3. Count unique planets
        count = count_unique_planets(df)
        
        # 4. Validate sample size
        validation_result = validate_sample_size(count)
        
        # Log final summary
        logger.info("=== Download Pipeline Summary ===")
        logger.info(f"Total Records: {len(df)}")
        logger.info(f"Unique Planets: {count}")
        logger.info(f"Validation Status: {validation_result['validation_status']}")
        
    except Exception as e:
        logger.exception(f"Pipeline failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
