import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from tqdm import tqdm
import time
import json

from api_config import QUERY_PARAMS
from config import get_config
from utils import setup_logging, DataFetchError, retry_on_failure

# Configure logger for this module
logger = logging.getLogger(__name__)

# Base URL for NASA Exoplanet Archive API
API_BASE_URL = "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/Tbl/nph-exoplanetarchive"

@retry_on_failure(max_retries=3, backoff_factor=1.0)
def fetch_spectrum_data(planet_name: str, output_dir: Path) -> Tuple[Optional[Path], Dict[str, Any]]:
    """
    Fetch spectrum data and metadata for a specific planet from NASA Exoplanet Archive.
    
    Args:
        planet_name: Name of the exoplanet
        output_dir: Directory to save downloaded files
        
    Returns:
        Tuple of (path to saved file, metadata dict) or (None, {}) on failure
    """
    config = get_config()
    params = {
        'cmd': f"SELECT * FROM transit_spectra WHERE pl_name = '{planet_name}'",
        'format': 'json',
        'limit': 10
    }
    
    logger.info(f"Fetching spectrum data for {planet_name} from NASA Exoplanet Archive")
    start_time = time.time()
    
    try:
        response = requests.get(API_BASE_URL, params=params, timeout=30)
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"API response received in {elapsed:.2f}s with {len(data.get('data', []))} records")
            
            if not data.get('data'):
                logger.warning(f"No spectrum data found for {planet_name}")
                return None, {}
            
            # Save raw response
            output_dir.mkdir(parents=True, exist_ok=True)
            filename = f"spectrum_{planet_name.replace(' ', '_')}.json"
            filepath = output_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved spectrum data for {planet_name} to {filepath} ({elapsed:.2f}s)")
            return filepath, data['data'][0]  # Return first record metadata
        else:
            error_msg = f"API request failed for {planet_name}: HTTP {response.status_code}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
            
    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {planet_name}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching data for {planet_name}: {str(e)}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for {planet_name}: {str(e)}")
        raise DataFetchError(f"Invalid JSON response for {planet_name}")

def parse_spectrum_metadata(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Parse raw API response into structured metadata.
    
    Args:
        raw_data: List of raw API records
        
    Returns:
        List of parsed metadata dictionaries
    """
    logger.info("Parsing spectrum metadata from raw API data")
    parsed_records = []
    
    for idx, record in enumerate(tqdm(raw_data, desc="Parsing metadata", unit="record")):
        try:
            parsed = {
                'planet_name': record.get('pl_name'),
                'host_name': record.get('pl_host'),
                'equilibrium_temp': record.get('pl_eqt'),
                'host_star_metallicity': record.get('pl_met'),
                'spectral_resolution': record.get('sp_res'),
                'signal_to_noise': record.get('snr'),
                'category': _categorize_planet(record.get('pl_massj'), record.get('pl_orbper')),
                'raw_data': record
            }
            
            # Log individual record processing
            if parsed['planet_name']:
                logger.debug(f"Parsed metadata for {parsed['planet_name']}: "
                           f"Temp={parsed['equilibrium_temp']}K, "
                           f"Metallicity={parsed['host_star_metallicity']}, "
                           f"Resolution={parsed['spectral_resolution']}")
            
            parsed_records.append(parsed)
            
        except Exception as e:
            logger.warning(f"Failed to parse record {idx}: {str(e)}")
            continue
    
    logger.info(f"Successfully parsed {len(parsed_records)} records")
    return parsed_records

def _categorize_planet(mass_jup: Optional[float], period_days: Optional[float]) -> str:
    """
    Categorize planet as Hot Jupiter or Super-Earth based on mass and period.
    
    Args:
        mass_jup: Planet mass in Jupiter masses
        period_days: Orbital period in days
        
    Returns:
        Planet category string
    """
    if mass_jup is None or period_days is None:
        return "Unknown"
    
    # Hot Jupiter: Mass > 0.3 MJ and Period < 10 days
    if mass_jup > 0.3 and period_days < 10:
        return "Hot Jupiter"
    
    # Super-Earth: Mass < 10 M_earth (~0.03 MJ) and Period < 100 days
    if mass_jup < 0.03 and period_days < 100:
        return "Super-Earth"
    
    return "Other"

def validate_parsed_metadata(parsed_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate parsed metadata for required fields.
    
    Args:
        parsed_records: List of parsed metadata dictionaries
        
    Returns:
        Filtered list of valid records
    """
    logger.info("Validating parsed metadata")
    valid_records = []
    required_fields = ['planet_name', 'equilibrium_temp', 'host_star_metallicity', 
                     'spectral_resolution', 'signal_to_noise', 'category']
    
    for record in tqdm(parsed_records, desc="Validating records", unit="record"):
        if all(record.get(field) is not None for field in required_fields):
            valid_records.append(record)
        else:
            missing = [f for f in required_fields if record.get(f) is None]
            logger.debug(f"Record missing fields {missing}: {record.get('planet_name', 'Unknown')}")
    
    logger.info(f"Validation complete: {len(valid_records)} valid records out of {len(parsed_records)}")
    return valid_records

def process_download_metadata(parsed_records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Process and save validated metadata to CSV.
    
    Args:
        parsed_records: List of validated metadata dictionaries
        output_path: Path to save CSV file
    """
    import pandas as pd
    
    logger.info(f"Saving {len(parsed_records)} metadata records to {output_path}")
    
    # Prepare DataFrame
    df = pd.DataFrame(parsed_records)
    
    # Log summary statistics
    logger.info(f"Metadata summary: {len(df)} records")
    logger.info(f"  - Hot Jupiters: {(df['category'] == 'Hot Jupiter').sum()}")
    logger.info(f"  - Super-Earths: {(df['category'] == 'Super-Earth').sum()}")
    logger.info(f"  - Temperature range: {df['equilibrium_temp'].min():.1f}K - {df['equilibrium_temp'].max():.1f}K")
    logger.info(f"  - Resolution range: {df['spectral_resolution'].min():.1f} - {df['spectral_resolution'].max():.1f}")
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved metadata to {output_path}")

def main():
    """Main entry point for download module."""
    setup_logging()
    logger.info("Starting exoplanet spectrum download process")
    
    config = get_config()
    output_dir = Path(config['data_dir']) / 'raw'
    processed_dir = Path(config['data_dir']) / 'processed'
    
    # Ensure directories exist
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Fetch data for each planet in QUERY_PARAMS
    all_metadata = []
    planets = QUERY_PARAMS.get('planet_filters', [])
    
    logger.info(f"Processing {len(planets)} planets from query parameters")
    
    for planet in tqdm(planets, desc="Downloading spectra", unit="planet"):
        try:
            filepath, metadata = fetch_spectrum_data(planet, output_dir)
            if filepath and metadata:
                all_metadata.append(metadata)
        except DataFetchError as e:
            logger.error(f"Skipping planet {planet} due to error: {str(e)}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing {planet}: {str(e)}")
            continue
    
    if not all_metadata:
        logger.error("No metadata collected. Check API connectivity and query parameters.")
        return
    
    # Parse and validate metadata
    parsed = parse_spectrum_metadata(all_metadata)
    validated = validate_parsed_metadata(parsed)
    
    if not validated:
        logger.error("No valid metadata after parsing and validation")
        return
    
    # Save processed metadata
    metadata_path = processed_dir / 'metadata.csv'
    process_download_metadata(validated, metadata_path)
    
    logger.info("Download process completed successfully")

if __name__ == "__main__":
    main()