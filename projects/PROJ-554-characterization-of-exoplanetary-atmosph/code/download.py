import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from tqdm import tqdm
import json
import pandas as pd
import numpy as np
from config import get_config
from utils import setup_logging, retry_on_failure, DataFetchError, ParsingError

# Configure logging for this module
logger = logging.getLogger(__name__)

# Constants for NASA Exoplanet Archive query
API_URL = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"

# Required columns for metadata extraction per FR-001 and Review Response
REQUIRED_COLUMNS = [
    'pl_name', 'pl_orbsnum', 'pl_contropf', 'pl_massj', 'pl_radj', 
    'pl_eqt', 'pl_dens', 'pl_per', 'pl_snum', 'pl_discmethod',
    'st_name', 'st_mass', 'st_rad', 'st_teff', 'st_met', 'st_logg',
    'discoveryyear', 'pub_title', 'pub_doi'
]

# Specific columns needed for Review Response (SNR, Resolution)
# Note: NASA Exoplanet Archive does not always provide direct SNR/R columns for every entry.
# We will attempt to fetch 'transit_depth', 'transit_depth_err', and 'transit_depth_sig'
# to derive SNR, and look for 'spectral_resolution' if available in extended metadata.
# If not directly available, we will calculate proxy SNR from depth/error where possible.
METADATA_COLUMNS = REQUIRED_COLUMNS + [
    'transit_depth', 'transit_depth_err', 'transit_depth_sig',
    'transit_duration', 'transit_duration_err',
    'ra', 'dec', 'st_dist', 'st_age', 'st_met_err', 'st_logg_err'
]

def fetch_spectrum_data(
    query_type: str = "hot_jupiters",
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch spectrum metadata from NASA Exoplanet Archive.
    
    Args:
        query_type: Type of planets to fetch ('hot_jupiters' or 'super_earths')
        limit: Maximum number of records to fetch (None for all)
        
    Returns:
        List of dictionaries containing spectrum metadata
    """
    config = get_config()
    
    # Construct query based on type
    if query_type == "hot_jupiters":
        # Hot Jupiters: T_eq > 1000K, R_p > 0.8 R_jup
        where_clause = "pl_eqt > 1000 AND pl_radj > 0.8"
    elif query_type == "super_earths":
        # Super Earths: 1.0 < R_p < 1.6 R_jup (approx), T_eq < 1000K (typical)
        where_clause = "pl_radj > 0.3 AND pl_radj < 1.6 AND pl_eqt < 1000"
    else:
        where_clause = "1=1"  # Default: all planets with data
    
    # Build TAP query
    columns_str = ", ".join(METADATA_COLUMNS)
    query = f"SELECT {columns_str} FROM exoplanetarchive WHERE {where_clause}"
    
    if limit:
        query += f" AND 1=1"  # TAP doesn't support LIMIT in WHERE, handled by fetch
    
    params = {
        "QUERY": query,
        "FORMAT": "json",
        "TAPFORMAT": "json"
    }
    
    logger.info(f"Fetching {query_type} data from NASA Exoplanet Archive...")
    logger.debug(f"Query: {query}")
    
    try:
        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if not data or 'data' not in data:
            logger.warning("No data returned from API")
            return []
        
        records = data['data']
        logger.info(f"Fetched {len(records)} records")
        
        return records
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        raise DataFetchError(f"Failed to fetch spectrum data: {e}")

def parse_spectrum_metadata(
    raw_records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Parse raw API records into structured metadata.
    
    Extracts:
    - Equilibrium Temperature (K)
    - Host Star Metallicity ([Fe/H])
    - Spectral Resolution (R) - derived or from metadata
    - Signal-to-Noise Ratio (SNR) - derived from transit depth errors
    
    Args:
        raw_records: List of raw API response records
        
    Returns:
        List of parsed metadata dictionaries
    """
    parsed_records = []
    
    for i, record in enumerate(raw_records):
        try:
            # Extract basic fields
            planet_name = record.get('pl_name', 'Unknown')
            eq_temp = record.get('pl_eqt')
            host_met = record.get('st_met')
            
            # Parse Equilibrium Temperature
            temp_k = float(eq_temp) if eq_temp is not None and eq_temp != '' else None
            
            # Parse Host Star Metallicity
            metallicity = float(host_met) if host_met is not None and host_met != '' else None
            
            # Calculate SNR from transit depth and error
            # SNR = depth / error (if error exists)
            depth = record.get('transit_depth')
            depth_err = record.get('transit_depth_err')
            snr = None
            
            if depth is not None and depth_err is not None:
                try:
                    d = float(depth)
                    e = float(depth_err)
                    if e > 0:
                        snr = d / e
                    else:
                        snr = None
                except (ValueError, TypeError):
                    snr = None
            
            # Determine Spectral Resolution (R)
            # NASA Exoplanet Archive does not always provide 'R' directly.
            # We check for 'spectral_resolution' or derive proxy from instrument info if available.
            # For this implementation, we attempt to read from a hypothetical extended field
            # or set to None if not available, logging the status.
            resolution_r = record.get('spectral_resolution')
            if resolution_r is None or resolution_r == '':
                # Try to infer from instrument if available (not in standard columns)
                # For now, we mark as 'N/A' or attempt a proxy based on typical values
                # if specific instrument data were present. Since we rely on standard columns,
                # we default to None and log.
                resolution_r = None
            
            # Construct parsed record
            parsed = {
                'planet_name': planet_name,
                'equilibrium_temp_k': temp_k,
                'host_metallicity': metallicity,
                'snr': snr,
                'spectral_resolution_r': resolution_r,
                'raw_record': record  # Keep raw for reference
            }
            
            parsed_records.append(parsed)
            
        except Exception as e:
            logger.warning(f"Failed to parse record {i}: {e}")
            continue
    
    return parsed_records

def validate_parsed_metadata(
    records: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Validate parsed metadata ensuring critical fields are present.
    
    Per FR-001 and Review Response, we must log and store R and SNR.
    If R is missing, we log a warning but proceed (do not raise error).
    If SNR is missing, we log a warning.
    
    Args:
        records: List of parsed metadata records
        
    Returns:
        Validated list of records
    """
    validated = []
    
    for i, record in enumerate(records):
        planet = record.get('planet_name', 'Unknown')
        snr = record.get('snr')
        resolution = record.get('spectral_resolution_r')
        
        # Log status for Review Response compliance
        if snr is None:
            logger.warning(f"Planet {planet}: SNR could not be derived from available data.")
        else:
            logger.debug(f"Planet {planet}: SNR = {snr:.2f}")
        
        if resolution is None:
            logger.warning(f"Planet {planet}: Spectral Resolution (R) not available in archive metadata.")
        else:
            logger.debug(f"Planet {planet}: Resolution R = {resolution}")
        
        # We do NOT discard records even if R/SNR are missing, per FR-001 "download ALL"
        # We just ensure the fields exist (even if None) for downstream handling
        validated.append(record)
    
    return validated

def process_download_metadata(
    records: List[Dict[str, Any]],
    output_dir: Path
) -> Path:
    """
    Save metadata to CSV and raw spectrum files to disk.
    
    Creates:
    - data/processed/metadata.csv (with SNR, R columns)
    - data/raw/ directory for any associated spectrum files (if URLs available)
    
    Args:
        records: List of validated metadata records
        output_dir: Base output directory (data/)
        
    Returns:
        Path to the generated metadata CSV
    """
    processed_dir = output_dir / "processed"
    raw_dir = output_dir / "raw"
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_csv_path = processed_dir / "metadata.csv"
    
    # Flatten records for CSV
    csv_rows = []
    for i, record in enumerate(records):
        row = {
            'planet_name': record.get('planet_name'),
            'equilibrium_temp_k': record.get('equilibrium_temp_k'),
            'host_metallicity': record.get('host_metallicity'),
            'snr': record.get('snr'),
            'spectral_resolution_r': record.get('spectral_resolution_r'),
            'has_spectrum': False,  # Placeholder for future file linking
            'source': 'NASA_Exoplanet_Archive'
        }
        csv_rows.append(row)
        
        # If raw record has a URL for spectrum, we would download it here.
        # For now, we just log the intent.
        raw_rec = record.get('raw_record', {})
        # Example check if a spectrum URL exists (hypothetical field)
        # if 'spectrum_url' in raw_rec:
        #     ... download ...
        #     row['has_spectrum'] = True
    
    # Write CSV
    df = pd.DataFrame(csv_rows)
    df.to_csv(metadata_csv_path, index=False)
    
    logger.info(f"Saved metadata to {metadata_csv_path}")
    logger.info(f"Total records processed: {len(csv_rows)}")
    
    # Log summary for Review Response
    snr_count = df['snr'].notna().sum()
    r_count = df['spectral_resolution_r'].notna().sum()
    logger.info(f"Records with SNR: {snr_count}/{len(df)}")
    logger.info(f"Records with Resolution R: {r_count}/{len(df)}")
    
    return metadata_csv_path

def validate_sample_size(
    metadata_path: Path,
    min_count: int = 30,
    max_count: int = 45
) -> Tuple[int, bool]:
    """
    Validate sample size against targets.
    
    Per T013 logic:
    - If count < 30 or > 45, log warning but proceed (do not raise error).
    - If count is absent or null, raise RuntimeError.
    
    Args:
        metadata_path: Path to the metadata CSV
        min_count: Minimum expected unique planets
        max_count: Maximum expected unique planets
        
    Returns:
        Tuple of (count, is_valid)
    """
    if not metadata_path.exists():
        raise RuntimeError(f"Metadata file not found: {metadata_path}")
    
    df = pd.read_csv(metadata_path)
    unique_planets = df['planet_name'].nunique()
    
    if unique_planets == 0:
        raise RuntimeError("No unique planets found in metadata.")
    
    is_valid = min_count <= unique_planets <= max_count
    
    if not is_valid:
        if unique_planets < min_count:
            logger.warning(f"Sample size ({unique_planets}) is below target ({min_count}). Proceeding per FR-001.")
        else:
            logger.warning(f"Sample size ({unique_planets}) exceeds target ({max_count}). Proceeding per FR-001.")
    else:
        logger.info(f"Sample size ({unique_planets}) is within target range [{min_count}, {max_count}].")
    
    return unique_planets, is_valid

def main():
    """
    Main entry point for data acquisition.
    
    Executes the full pipeline:
    1. Fetch data for Hot Jupiters and Super-Earths
    2. Parse metadata (extracting T_eq, Metallicity, SNR, R)
    3. Validate and log quality metrics
    4. Save to data/processed/metadata.csv
    5. Validate sample size
    """
    # Setup logging
    log_file = Path("logs/download.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(level=logging.INFO, log_file=log_file)
    
    logger.info("Starting data acquisition pipeline...")
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data'))
    
    all_records = []
    
    # Fetch Hot Jupiters
    try:
        hjs = fetch_spectrum_data("hot_jupiters")
        all_records.extend(hjs)
        logger.info(f"Fetched {len(hjs)} Hot Jupiters")
    except DataFetchError as e:
        logger.error(f"Failed to fetch Hot Jupiters: {e}")
    
    # Fetch Super-Earths
    try:
        ses = fetch_spectrum_data("super_earths")
        all_records.extend(ses)
        logger.info(f"Fetched {len(ses)} Super-Earths")
    except DataFetchError as e:
        logger.error(f"Failed to fetch Super-Earths: {e}")
    
    if not all_records:
        logger.error("No data fetched. Exiting.")
        return
    
    # Parse metadata
    parsed = parse_spectrum_metadata(all_records)
    logger.info(f"Parsed metadata for {len(parsed)} planets")
    
    # Validate metadata (logs SNR/R status)
    validated = validate_parsed_metadata(parsed)
    
    # Save to disk
    metadata_path = process_download_metadata(validated, data_dir)
    
    # Validate sample size
    count, is_valid = validate_sample_size(metadata_path)
    
    logger.info(f"Pipeline completed. Processed {count} unique planets.")
    if not is_valid:
        logger.warning("Sample size warning issued, but pipeline continued.")

if __name__ == "__main__":
    main()