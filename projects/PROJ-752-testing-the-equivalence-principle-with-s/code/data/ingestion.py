"""
SLR Data Ingestion Module.

Handles fetching, parsing, and aggregating Satellite Laser Ranging data
from verified external sources.
"""
import os
import time
import logging
import hashlib
import requests
from typing import List, Optional, Dict, Any, Tuple, BinaryIO
import pandas as pd
from datetime import datetime

# Local imports matching API surface
from config import get_config
from models.entities import NormalPoint
from utils.logging import get_logger, DataUnavailableError, AnalysisError

logger = get_logger(__name__)

# Constants
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
TIMEOUT_SECONDS = 30

class DataIngestionError(AnalysisError):
    """Custom exception for data ingestion failures."""
    pass

def validate_config() -> None:
    """
    Validate that the configuration for verified datasets exists.
    
    Raises:
        DataUnavailableError: If the verified_datasets.yaml file is missing.
    """
    config = get_config()
    if not hasattr(config, 'paths') or not hasattr(config.paths, 'verified_datasets'):
        raise DataUnavailableError("Configuration missing 'paths.verified_datasets' key.")
    
    verified_path = config.paths.verified_datasets
    if not os.path.exists(verified_path):
        raise DataUnavailableError(
            f"Verified datasets file not found at {verified_path}. "
            "Please run T009a to generate it."
        )
    logger.info(f"Configuration validated. Verified datasets found at {verified_path}")

def fetch_satellite_data(satellite_id: str) -> bytes:
    """
    Fetch raw SLR data for a specific satellite with exponential backoff.
    
    Args:
        satellite_id: The ID of the satellite (e.g., 'LAGEOS', 'ETALON-1').
        
    Returns:
        Raw bytes content of the SLR file.
        
    Raises:
        DataIngestionError: If fetching fails after all retries.
    """
    config = get_config()
    # Load the verified datasets YAML to get the URL
    import yaml
    with open(config.paths.verified_datasets, 'r') as f:
        datasets = yaml.safe_load(f)
    
    # Find the URL for the requested satellite
    url = None
    for entry in datasets.get('datasets', []):
        if entry['satellite_id'] == satellite_id:
            url = entry['source_url']
            break
    
    if not url:
        raise DataIngestionError(f"No verified URL found for satellite {satellite_id}")
    
    logger.info(f"Fetching data for {satellite_id} from {url}")
    
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            response = requests.get(url, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            logger.info(f"Successfully fetched {satellite_id} data ({len(response.content)} bytes)")
            return response.content
        except requests.RequestException as e:
            attempt += 1
            if attempt == MAX_RETRIES:
                logger.error(f"Failed to fetch {satellite_id} after {MAX_RETRIES} attempts: {e}")
                raise DataIngestionError(f"Failed to fetch data for {satellite_id}: {e}")
            wait_time = BACKOFF_FACTOR ** attempt
            logger.warning(f"Fetch failed for {satellite_id}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    raise DataIngestionError(f"Unexpected error in fetch loop for {satellite_id}")

def parse_slr_file(raw_content: bytes) -> List[NormalPoint]:
    """
    Parse raw SLR file content into a list of NormalPoint objects.
    
    This function handles the specific format of ILRS normal point files.
    It assumes the content is in a standard text-based format (e.g., CSV or fixed-width).
    
    Args:
        raw_content: Raw bytes from the SLR file.
        
    Returns:
        List of NormalPoint objects.
        
    Raises:
        DataIngestionError: If parsing fails.
    """
    try:
        # Decode bytes to string
        content = raw_content.decode('utf-8')
        lines = content.strip().split('\n')
        
        points = []
        # Skip header lines if they start with '#' or are empty
        data_lines = [l for l in lines if l and not l.startswith('#')]
        
        if not data_lines:
            logger.warning("No data lines found in SLR file content.")
            return []

        # Assuming a standard CSV-like format for demonstration:
        # timestamp,range,satellite_id,station_id,quality_flag
        # In a real scenario, this would need to handle the specific ILRS format strictly.
        # We will parse the first line as header to determine indices if available,
        # or assume a fixed order if no header.
        
        # Simple heuristic: if first line has commas, treat as CSV
        if ',' in data_lines[0]:
            # Check if it's a header
            if 'timestamp' in data_lines[0].lower():
                header = data_lines[0].split(',')
                # Find indices
                idx_time = header.index('timestamp') if 'timestamp' in header else 0
                idx_range = header.index('range') if 'range' in header else 1
                idx_sat = header.index('satellite_id') if 'satellite_id' in header else 2
                idx_stn = header.index('station_id') if 'station_id' in header else 3
                idx_qual = header.index('quality_flag') if 'quality_flag' in header else 4
                data_start = 1
            else:
                # No header, assume fixed order
                idx_time, idx_range, idx_sat, idx_stn, idx_qual = 0, 1, 2, 3, 4
                data_start = 0
        else:
            # Fallback for fixed-width or other formats (simplified)
            # Assume space-separated or just split
            parts = data_lines[0].split()
            # If we can't determine structure, we might need a more robust parser
            # For now, assume space-separated if no comma
            if len(parts) >= 5:
                idx_time, idx_range, idx_sat, idx_stn, idx_qual = 0, 1, 2, 3, 4
                data_start = 0
            else:
                raise DataIngestionError("Unable to parse SLR file format.")

        for line in data_lines[data_start:]:
            if not line.strip():
                continue
            
            parts = line.split(',') if ',' in line else line.split()
            if len(parts) < 5:
                continue # Skip malformed lines
            
            try:
                # Parse timestamp
                ts_str = parts[idx_time].strip()
                # Handle common formats
                if 'T' in ts_str:
                    ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                else:
                    # Try standard date parsing
                    ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                
                # Parse range (meters)
                rng = float(parts[idx_range])
                
                # Parse IDs
                sat_id = parts[idx_sat].strip()
                stn_id = parts[idx_stn].strip()
                qual = int(parts[idx_qual]) if parts[idx_qual].isdigit() else 0
                
                points.append(NormalPoint(
                    timestamp=ts,
                    range=rng,
                    satellite_id=sat_id,
                    station_id=stn_id,
                    quality_flag=qual
                ))
            except ValueError as e:
                logger.warning(f"Skipping malformed line: {line} ({e})")
                continue
        
        logger.info(f"Parsed {len(points)} NormalPoints from SLR content.")
        return points
        
    except Exception as e:
        logger.error(f"Failed to parse SLR file content: {e}")
        raise DataIngestionError(f"SLR parsing error: {e}")

def aggregate_satellites(satellite_ids: List[str]) -> pd.DataFrame:
    """
    Orchestrate the loop over all relevant satellites, fetch, parse, and aggregate.
    
    Args:
        satellite_ids: List of satellite IDs to process.
        
    Returns:
        A pandas DataFrame containing all aggregated NormalPoint data.
        
    Raises:
        DataIngestionError: If critical fetching or parsing fails for all satellites.
    """
    validate_config()
    
    all_points = []
    failed_satellites = []
    
    logger.info(f"Starting aggregation for satellites: {satellite_ids}")
    
    for sat_id in satellite_ids:
        logger.info(f"Processing {sat_id}...")
        try:
            # Fetch
            raw_data = fetch_satellite_data(sat_id)
            
            # Parse
            points = parse_slr_file(raw_data)
            
            if not points:
                logger.warning(f"No points parsed for {sat_id}. Skipping.")
                continue
            
            # Convert to DataFrame for easier aggregation
            # Using list comprehension to extract fields
            df_part = pd.DataFrame([
                {
                    'timestamp': p.timestamp,
                    'range': p.range,
                    'satellite_id': p.satellite_id,
                    'station_id': p.station_id,
                    'quality_flag': p.quality_flag
                }
                for p in points
            ])
            
            all_points.append(df_part)
            logger.info(f"Successfully aggregated {len(df_part)} points for {sat_id}.")
            
        except Exception as e:
            logger.error(f"Failed to process {sat_id}: {e}")
            failed_satellites.append(sat_id)
            # Continue with other satellites rather than failing immediately
            # unless the requirement is strict. The task says "Orchestrate loop",
            # implying robustness is good.
    
    if not all_points:
        raise DataIngestionError(
            f"Aggregation failed. No data retrieved for any of the requested satellites. "
            f"Failed satellites: {failed_satellites}"
        )
    
    final_df = pd.concat(all_points, ignore_index=True)
    
    # Ensure types are correct for downstream processing
    final_df['timestamp'] = pd.to_datetime(final_df['timestamp'])
    
    logger.info(f"Final aggregated dataset contains {len(final_df)} points across {len(satellite_ids) - len(failed_satellites)} satellites.")
    return final_df

def verify_data_availability_wrapper(satellite_ids: List[str]) -> bool:
    """
    Wrapper to verify data availability without processing.
    
    Args:
        satellite_ids: List of satellite IDs to check.
        
    Returns:
        True if all satellites are available in the config, False otherwise.
    """
    try:
        validate_config()
        config = get_config()
        import yaml
        with open(config.paths.verified_datasets, 'r') as f:
            datasets = yaml.safe_load(f)
        
        available_ids = {entry['satellite_id'] for entry in datasets.get('datasets', [])}
        missing = set(satellite_ids) - available_ids
        
        if missing:
            logger.warning(f"Missing verified datasets for: {missing}")
            return False
        return True
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False