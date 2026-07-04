import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from tqdm import tqdm

from config import get_config
from utils import setup_logging, retry_on_failure, DataFetchError, ParsingError
from api_config import QUERY_PARAMS

# Ensure logging is configured (redundant if called from main, but safe)
logger = setup_logging()

def fetch_spectrum_data(
    base_url: str = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/TblAccess/nph-tblaccess",
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> List[Dict[str, Any]]:
    """
    Fetches spectrum metadata from the NASA Exoplanet Archive API.
    
    Implements logging for API response handling and progress as per T014.
    
    Args:
        base_url: The API endpoint URL.
        params: Query parameters for the request.
        timeout: Request timeout in seconds.
        
    Returns:
        A list of dictionaries containing the raw API response rows.
        
    Raises:
        DataFetchError: If the request fails or returns a non-200 status.
    """
    config = get_config()
    if params is None:
        params = QUERY_PARAMS
    
    logger.info(f"Initiating API request to {base_url} with params: {params}")
    
    try:
        response = requests.get(base_url, params=params, timeout=timeout)
        
        # Log response handling details
        logger.debug(f"API Response Status Code: {response.status_code}")
        logger.debug(f"API Response Headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            error_msg = f"API request failed with status {response.status_code}: {response.text[:200]}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
        
        # Log response size for monitoring
        content_length = len(response.content)
        logger.info(f"API request successful. Received {content_length} bytes.")
        
        # Attempt to parse JSON
        try:
            data = response.json()
            count = len(data) if isinstance(data, list) else 1
            logger.info(f"Successfully parsed {count} records from API response.")
            return data
        except ValueError as e:
            logger.error(f"Failed to parse API response as JSON: {e}")
            raise DataFetchError(f"Invalid JSON response: {e}")
            
    except requests.exceptions.Timeout:
        logger.error(f"API request timed out after {timeout} seconds.")
        raise DataFetchError("API request timed out.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during API request: {e}")
        raise DataFetchError(f"Network error: {e}")

@retry_on_failure(max_retries=3, delay=2, backoff=2)
def parse_spectrum_metadata(
    raw_data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Parses raw API data to extract specific metadata fields:
    equilibrium temperature, host star metallicity, spectral resolution, SNR.
    
    Logs progress for each record processed.
    
    Args:
        raw_data: List of raw dictionaries from the API.
        
    Returns:
        List of parsed metadata dictionaries.
    """
    logger.info(f"Starting parsing of {len(raw_data)} records.")
    parsed_records = []
    
    # Use tqdm for progress logging as requested in T014
    # We iterate with a progress bar that logs to the logger or stderr
    for i, record in enumerate(tqdm(raw_data, desc="Parsing Metadata", unit="rec")):
        try:
            # Extract fields with safe defaults
            planet_name = record.get('planets_name', record.get('pl_name', 'Unknown'))
            temp = record.get('pl_eqt')
            metallicity = record.get('st_met')
            resolution = record.get('pl_res') # Depending on archive schema, might be different key
            snr = record.get('pl_snr')
            
            # Log specific record processing if needed for debugging
            if i % 10 == 0:
                logger.debug(f"Processed record {i}: {planet_name}")

            parsed_record = {
                'planet_name': planet_name,
                'equilibrium_temp_k': float(temp) if temp is not None else None,
                'host_metallicity': float(metallicity) if metallicity is not None else None,
                'spectral_resolution': float(resolution) if resolution is not None else None,
                'snr': float(snr) if snr is not None else None,
                'raw_record': record # Keep raw for potential future extension
            }
            parsed_records.append(parsed_record)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse record {i} ({planet_name}): {e}. Skipping.")
            continue
        except Exception as e:
            logger.error(f"Unexpected error parsing record {i}: {e}")
            raise ParsingError(f"Error parsing record {i}: {e}")
    
    logger.info(f"Parsing complete. Successfully parsed {len(parsed_records)} records.")
    return parsed_records

def validate_parsed_metadata(parsed_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Validates that parsed records have the required fields for downstream tasks.
    
    Logs validation results.
    
    Args:
        parsed_data: List of parsed metadata.
        
    Returns:
        Tuple of (valid_records, list_of_missing_field_warnings)
    """
    valid_records = []
    warnings = []
    
    logger.info(f"Validating {len(parsed_data)} parsed records.")
    
    required_fields = ['equilibrium_temp_k', 'host_metallicity', 'spectral_resolution', 'snr']
    
    for i, record in enumerate(parsed_data):
        missing = [f for f in required_fields if record.get(f) is None]
        if missing:
            msg = f"Record {i} ({record.get('planet_name')}) missing fields: {missing}"
            logger.warning(msg)
            warnings.append(msg)
        else:
            valid_records.append(record)
            
    logger.info(f"Validation complete. {len(valid_records)} valid, {len(warnings)} skipped.")
    return valid_records, warnings

def process_download_metadata(
    raw_data: List[Dict[str, Any]],
    output_dir: Path
) -> Path:
    """
    Orchestrates the download, parsing, validation, and saving of metadata.
    
    Logs the full pipeline progress.
    
    Args:
        raw_data: Raw data from the API (or path to it if pre-fetched, but here we assume raw list).
        output_dir: Directory to save the processed CSV.
        
    Returns:
        Path to the saved CSV file.
    """
    logger.info(f"Processing download metadata to {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Parse
    parsed = parse_spectrum_metadata(raw_data)
    
    # 2. Validate
    valid, warnings = validate_parsed_metadata(parsed)
    
    # 3. Save
    import pandas as pd
    df = pd.DataFrame(valid)
    csv_path = output_dir / "metadata.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved validated metadata to {csv_path}")
    
    return csv_path

def validate_sample_size(parsed_data: List[Dict[str, Any]]) -> int:
    """
    Validates the sample size of unique planets.
    
    Logs warnings if the count is outside the expected range [30, 45].
    Raises RuntimeError if count is absent/null (0).
    
    Args:
        parsed_data: List of parsed records.
        
    Returns:
        Count of unique planets.
    """
    if not parsed_data:
        raise RuntimeError("No data found to validate sample size.")
    
    unique_planets = set(r['planet_name'] for r in parsed_data if r.get('planet_name'))
    count = len(unique_planets)
    
    logger.info(f"Sample size validation: Found {count} unique planets.")
    
    if count < 30 or count > 45:
        logger.warning(f"Sample size {count} is outside the target range [30, 45]. Proceeding anyway as per FR-001.")
    
    return count

def main():
    """
    Main entry point for the download and processing pipeline.
    """
    # Setup logging
    log_file = setup_logging()
    logger.info("Starting Download Pipeline (T014: Logging implementation)")
    
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data'))
    raw_dir = data_dir / 'raw'
    processed_dir = data_dir / 'processed'
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Fetch
        logger.info("Step 1: Fetching data from NASA Exoplanet Archive...")
        raw_data = fetch_spectrum_data()
        
        # Process and Save
        logger.info("Step 2: Processing and saving metadata...")
        csv_path = process_download_metadata(raw_data, processed_dir)
        
        # Validate Sample Size
        logger.info("Step 3: Validating sample size...")
        count = validate_sample_size([r for r in raw_data]) # Use raw or parsed? Usually parsed valid set
        # Re-validate on the valid set to be precise
        parsed_valid, _ = validate_parsed_metadata(parse_spectrum_metadata(raw_data))
        count = validate_sample_size(parsed_valid)
        
        logger.info(f"Pipeline completed successfully. Output: {csv_path}, Count: {count}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()