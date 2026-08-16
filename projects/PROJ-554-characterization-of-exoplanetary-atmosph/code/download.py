import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from tqdm import tqdm
import json
import time

from config import get_config
from api_config import QUERY_PARAMS
from utils import retry_on_failure, DataFetchError, PipelineError

# --- Logging Setup for Download Task ---

def setup_download_logging(log_path: Optional[Path] = None) -> logging.Logger:
    """
    Configures and returns a logger specifically for download operations.
    Ensures the log file exists and is writable.
    
    Args:
        log_path: Optional path to the log file. Defaults to 'logs/download.log'.
    
    Returns:
        A configured logger instance.
    """
    if log_path is None:
        log_path = Path("logs/download.log")
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("download_logger")
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates if called multiple times
    logger.handlers = []
    
    # File handler for persistent log
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Formatter with timestamp and level
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# --- Core Download Logic ---

@retry_on_failure(max_retries=3, delay=2, backoff=2, logger_name="download_logger")
def fetch_spectrum_data(page: int = 1, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Fetches a single page of spectrum data from the NASA Exoplanet Archive API.
    
    Args:
        page: Page number to fetch.
        params: Query parameters to override defaults.
    
    Returns:
        JSON response data.
    
    Raises:
        DataFetchError: If the API request fails after retries.
    """
    config = get_config()
    base_url = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/Tbl/nph-exoplanetarchive"
    
    query_params = QUERY_PARAMS.copy() if params is None else params
    query_params['page'] = page
    query_params['format'] = 'json'
    
    logger = logging.getLogger("download_logger")
    logger.debug(f"Fetching page {page} with params: {query_params}")
    
    try:
        response = requests.get(base_url, params=query_params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed for page {page}: {e}")
        raise DataFetchError(f"Failed to fetch spectrum data from NASA Exoplanet Archive: {e}")

def fetch_all_pages() -> List[Dict[str, Any]]:
    """
    Fetches all available pages of spectrum data, logging progress.
    
    Returns:
        A list of all fetched data records.
    """
    logger = logging.getLogger("download_logger")
    logger.info("Starting full data fetch from NASA Exoplanet Archive")
    
    all_data = []
    page = 1
    max_pages = 100  # Safety limit to prevent infinite loops
    
    while page <= max_pages:
        logger.info(f"Fetching page {page}...")
        try:
            data = fetch_spectrum_data(page=page)
            
            if not data or isinstance(data, dict) and 'data' not in data:
                logger.warning(f"No data returned for page {page}. Stopping pagination.")
                break
            
            records = data.get('data', [])
            if not records:
                logger.info(f"Reached end of data at page {page}.")
                break
            
            all_data.extend(records)
            logger.debug(f"Retrieved {len(records)} records from page {page}. Total: {len(all_data)}")
            
            # Check if we have more pages (API specific logic might vary)
            # Assuming standard pagination or fixed limit
            if len(records) < 100: # Assuming 100 is the page size limit
                logger.info(f"Last page detected (received {len(records)} records).")
                break
            
            page += 1
            # Small delay to be polite to the API
            time.sleep(0.5)
            
        except DataFetchError as e:
            logger.error(f"Critical failure fetching page {page}: {e}")
            raise
    
    logger.info(f"Successfully fetched {len(all_data)} total records.")
    return all_data

def parse_spectrum_metadata(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parses raw API data into structured metadata.
    
    Args:
        raw_data: List of raw dictionaries from the API.
    
    Returns:
        List of parsed metadata dictionaries.
    """
    logger = logging.getLogger("download_logger")
    logger.info("Parsing spectrum metadata...")
    
    parsed = []
    for idx, record in enumerate(tqdm(raw_data, desc="Parsing metadata")):
        try:
            # Extract fields based on typical NASA Exoplanet Archive schema
            # Adjust keys based on actual API response structure if known
            planet_name = record.get('pl_name', 'Unknown')
            host_name = record.get('pl_hostname', 'Unknown')
            t_eq = record.get('pl_eqt', None) # Equilibrium Temperature
            metallicity = record.get('st_met', None) # Host Star Metallicity
            radius = record.get('pl_radj', None) # Planet Radius in Jupiter Radii
            
            # Instrument and Wavelength info might be in separate columns or nested
            instrument = record.get('disc_facility', 'Unknown')
            wavelength_range = record.get('wavelength_range', 'N/A')
            
            # Calculate SNR if available, otherwise mark as unknown
            snr = record.get('snr', None)
            resolution = record.get('resolution', None)
            
            # Determine Planet Category (Logic from T011c)
            category = "Unknown"
            if t_eq and radius:
                t_eq_val = float(t_eq)
                radius_val = float(radius)
                
                if radius_val > 0.8 and t_eq_val > 1000:
                    category = "Hot Jupiter"
                elif radius_val < 1.6 and t_eq_val < 1000: # Assuming R_E conversion handled or stored
                    category = "Temperate Super-Earth"
                else:
                    category = "Other"
            
            parsed_record = {
                "planet_name": planet_name,
                "host_name": host_name,
                "temperature": t_eq_val if t_eq else None,
                "metallicity": float(metallicity) if metallicity else None,
                "snr": float(snr) if snr else None,
                "resolution": float(resolution) if resolution else None,
                "planet_category": category,
                "instrument": instrument,
                "wavelength_range": wavelength_range
            }
            parsed.append(parsed_record)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse record {idx}: {e}")
            continue
    
    logger.info(f"Parsed {len(parsed)} valid metadata records.")
    return parsed

def validate_parsed_metadata(metadata: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Validates metadata against schema requirements.
    
    Returns:
        Tuple of (valid_records, error_messages)
    """
    logger = logging.getLogger("download_logger")
    valid = []
    errors = []
    
    required_fields = ["planet_name", "temperature", "metallicity", "snr", "resolution", "planet_category"]
    
    for i, record in enumerate(metadata):
        missing = [f for f in required_fields if record.get(f) is None]
        if missing:
            errors.append(f"Record {i} ({record.get('planet_name')}): Missing fields: {missing}")
        else:
            valid.append(record)
    
    if errors:
        logger.warning(f"Validation failed for {len(errors)} records.")
    else:
        logger.info("All records passed validation.")
        
    return valid, errors

def save_raw_spectrum_files(raw_data: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Saves raw JSON data to the specified directory.
    """
    logger = logging.getLogger("download_logger")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "raw_spectrum_data.json"
    
    logger.info(f"Saving raw spectrum data to {file_path}")
    with open(file_path, 'w') as f:
        json.dump(raw_data, f, indent=2)
    logger.info("Raw data saved successfully.")

def save_metadata_csv(metadata: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves parsed metadata to a CSV file.
    """
    logger = logging.getLogger("download_logger")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving metadata CSV to {output_path}")
    import pandas as pd
    df = pd.DataFrame(metadata)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(metadata)} rows to {output_path}")

def validate_sample_size(metadata: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
    """
    Validates the sample size of the fetched data.
    
    Logic:
    1. Count unique planets.
    2. Log WARNING if < 30 or > 45, but proceed.
    3. Save report to JSON.
    """
    logger = logging.getLogger("download_logger")
    
    unique_planets = set(r['planet_name'] for r in metadata if r.get('planet_name'))
    count = len(unique_planets)
    
    status = "proceed"
    if count < 30:
        logger.warning(f"Sample size ({count}) is below target (30). Proceeding as per FR-001.")
    elif count > 45:
        logger.warning(f"Sample size ({count}) exceeds target (45). Proceeding as per FR-001.")
    else:
        logger.info(f"Sample size ({count}) is within target range [30, 45].")
    
    report = {
        "count": count,
        "validation_status": status,
        "target_min": 30,
        "target_max": 45
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sample size report saved to {output_path}")
    return report

def process_download_metadata(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Main processing pipeline for downloaded data.
    """
    logger = logging.getLogger("download_logger")
    logger.info("Starting metadata processing pipeline")
    
    parsed = parse_spectrum_metadata(raw_data)
    valid, errors = validate_parsed_metadata(parsed)
    
    if errors:
        logger.error(f"Validation errors encountered: {errors}")
    
    return valid

def main():
    """
    Entry point for the download and logging task.
    """
    # Setup logging
    log_path = Path("logs/download.log")
    logger = setup_download_logging(log_path)
    logger.info("="*50)
    logger.info("Starting Download Process (T014)")
    logger.info("="*50)
    
    try:
        config = get_config()
        raw_data_path = Path("data/raw")
        processed_path = Path("data/processed")
        
        # Fetch data
        logger.info("Fetching all pages from API...")
        raw_data = fetch_all_pages()
        
        if not raw_data:
            logger.error("No data fetched. Aborting.")
            return
        
        # Save raw data
        save_raw_spectrum_files(raw_data, raw_data_path)
        
        # Process metadata
        logger.info("Processing metadata...")
        metadata = process_download_metadata(raw_data)
        
        # Save metadata CSV
        metadata_csv_path = processed_path / "metadata.csv"
        save_metadata_csv(metadata, metadata_csv_path)
        
        # Validate sample size
        sample_size_report_path = processed_path / "sample_size_report.json"
        validate_sample_size(metadata, sample_size_report_path)
        
        logger.info("="*50)
        logger.info("Download Process Completed Successfully")
        logger.info(f"Metadata saved to: {metadata_csv_path}")
        logger.info(f"Report saved to: {sample_size_report_path}")
        logger.info("="*50)
        
    except Exception as e:
        logger.critical(f"Download process failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()