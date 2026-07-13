"""
Data ingestion module for NOAA GHCN-Daily weather data.

Downloads station data for Northeast USA region (2000-2020) from NOAA GHCN-Daily
dataset via HuggingFace or direct NOAA URLs.
"""

import os
import csv
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
from datetime import datetime
import requests

from src.config import get_config
from src.data.loaders import fetch_noaa_ghcn_data, verify_data_integrity
from src.pipeline.logging_config import get_logger, log_with_context, time_execution

logger = get_logger(__name__)

# Northeast USA bounding box (latitude, longitude)
# Covers: Maine, Vermont, New Hampshire, Massachusetts, Rhode Island, Connecticut,
# New York, New Jersey, Pennsylvania, Delaware, Maryland, Virginia, West Virginia
NORTHEAST_BOUNDS = {
    "lat_min": 37.0,
    "lat_max": 47.5,
    "lon_min": -81.0,
    "lon_max": -66.0,
}

INGESTION_DATE_RANGE = ("2000-01-01", "2020-12-31")


def get_northeast_stations(
    stations_metadata_path: Optional[Path] = None,
) -> List[Dict[str, any]]:
    """
    Retrieve list of NOAA GHCN-Daily stations within Northeast USA bounds.
    
    Filters stations by geographic location and data availability.
    
    Args:
        stations_metadata_path: Optional path to pre-cached stations metadata file.
            If not provided, downloads from NOAA.
    
    Returns:
        List of station metadata dicts with keys: id, latitude, longitude, elevation, name
    """
    config = get_config()
    
    if stations_metadata_path is None:
        stations_metadata_path = Path(config.data_raw_dir) / "ghcn_stations.json"
    
    # Try to load cached metadata first
    if stations_metadata_path.exists():
        logger.info(f"Loading cached stations metadata from {stations_metadata_path}")
        with open(stations_metadata_path, 'r') as f:
            all_stations = json.load(f)
    else:
        # Download stations list from NOAA
        logger.info("Downloading NOAA GHCN-Daily stations metadata...")
        try:
            stations_url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"
            response = requests.get(stations_url, timeout=30)
            response.raise_for_status()
            
            all_stations = _parse_ghcn_stations_txt(response.text)
            
            # Cache for future use
            stations_metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(stations_metadata_path, 'w') as f:
                json.dump(all_stations, f, indent=2)
            logger.info(f"Cached {len(all_stations)} stations to {stations_metadata_path}")
        except Exception as e:
            logger.error(f"Failed to download stations metadata: {e}")
            raise
    
    # Filter to Northeast bounds
    northeast_stations = [
        s for s in all_stations
        if (NORTHEAST_BOUNDS["lat_min"] <= s.get("latitude", 0) <= NORTHEAST_BOUNDS["lat_max"]
            and NORTHEAST_BOUNDS["lon_min"] <= s.get("longitude", 0) <= NORTHEAST_BOUNDS["lon_max"])
    ]
    
    logger.info(f"Found {len(northeast_stations)} stations in Northeast USA bounds")
    return northeast_stations


def _parse_ghcn_stations_txt(text: str) -> List[Dict[str, any]]:
    """
    Parse NOAA GHCN-Daily stations.txt format.
    
    Format (fixed-width):
    - Positions 1-11: Station ID
    - Positions 13-20: Latitude
    - Positions 22-30: Longitude
    - Positions 32-37: Elevation
    - Positions 39-end: Station name
    """
    stations = []
    for line in text.strip().split('\n'):
        if len(line) < 39:
            continue
        try:
            station_id = line[0:11].strip()
            latitude = float(line[12:20].strip())
            longitude = float(line[21:30].strip())
            elevation = float(line[31:37].strip()) if line[31:37].strip() else None
            name = line[38:].strip()
            
            stations.append({
                "id": station_id,
                "latitude": latitude,
                "longitude": longitude,
                "elevation": elevation,
                "name": name,
            })
        except (ValueError, IndexError) as e:
            logger.debug(f"Skipped malformed station line: {line[:40]}")
            continue
    
    return stations


def download_station_data(
    station_id: str,
    start_date: str = INGESTION_DATE_RANGE[0],
    end_date: str = INGESTION_DATE_RANGE[1],
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Download daily weather data for a single station from NOAA GHCN-Daily.
    
    Args:
        station_id: NOAA station ID (e.g., "USW00014755")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        output_dir: Directory to save CSV file. If None, uses config.data_raw_dir
    
    Returns:
        Path to downloaded CSV file, or None if download failed
    """
    config = get_config()
    
    if output_dir is None:
        output_dir = Path(config.data_raw_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{station_id}.csv"
    
    # Skip if already exists
    if output_path.exists():
        logger.debug(f"Station data already exists: {output_path}")
        return output_path
    
    try:
        logger.info(f"Downloading data for station {station_id}...")
        
        # Use the loader function from loaders.py which handles NOAA URLs
        data = fetch_noaa_ghcn_data(station_id, start_date, end_date)
        
        if data is None or len(data) == 0:
            logger.warning(f"No data returned for station {station_id}")
            return None
        
        # Write to CSV
        with open(output_path, 'w', newline='') as f:
            if isinstance(data, list) and len(data) > 0:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        
        logger.info(f"Successfully downloaded {len(data)} records to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download data for station {station_id}: {e}")
        return None


@time_execution
def ingest_northeast_data(
    start_date: str = INGESTION_DATE_RANGE[0],
    end_date: str = INGESTION_DATE_RANGE[1],
    max_stations: Optional[int] = None,
) -> Dict[str, any]:
    """
    Main ingestion pipeline: Download NOAA GHCN-Daily data for Northeast USA stations.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        max_stations: Limit number of stations to download (for testing). None = all.
    
    Returns:
        Dictionary with ingestion summary:
        {
            "total_stations_found": int,
            "stations_downloaded": int,
            "stations_failed": int,
            "output_directory": str,
            "date_range": (start_date, end_date),
            "downloaded_files": [list of paths],
        }
    """
    config = get_config()
    output_dir = Path(config.data_raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting NOAA GHCN-Daily ingestion for Northeast USA ({start_date} to {end_date})")
    
    # Get Northeast stations
    stations = get_northeast_stations()
    
    if max_stations:
        stations = stations[:max_stations]
    
    logger.info(f"Attempting to download data for {len(stations)} stations")
    
    downloaded_files = []
    failed_stations = []
    
    for i, station in enumerate(stations):
        station_id = station["id"]
        logger.info(f"[{i+1}/{len(stations)}] Processing station {station_id} ({station['name']})")
        
        try:
            result_path = download_station_data(
                station_id,
                start_date=start_date,
                end_date=end_date,
                output_dir=output_dir,
            )
            
            if result_path:
                downloaded_files.append(str(result_path))
            else:
                failed_stations.append(station_id)
                
        except Exception as e:
            logger.error(f"Exception downloading {station_id}: {e}")
            failed_stations.append(station_id)
    
    summary = {
        "total_stations_found": len(stations),
        "stations_downloaded": len(downloaded_files),
        "stations_failed": len(failed_stations),
        "output_directory": str(output_dir),
        "date_range": (start_date, end_date),
        "downloaded_files": downloaded_files,
        "failed_stations": failed_stations,
    }
    
    logger.info(
        f"Ingestion complete: {len(downloaded_files)} downloaded, "
        f"{len(failed_stations)} failed out of {len(stations)} stations"
    )
    
    # Save summary
    summary_path = output_dir / "ingestion_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Ingestion summary saved to {summary_path}")
    
    return summary


def load_ingested_data(
    station_id: str,
    input_dir: Optional[Path] = None,
) -> Optional[List[Dict[str, any]]]:
    """
    Load previously ingested station data from CSV.
    
    Args:
        station_id: NOAA station ID
        input_dir: Directory containing station CSV files. If None, uses config.data_raw_dir
    
    Returns:
        List of daily records as dicts, or None if file not found
    """
    config = get_config()
    
    if input_dir is None:
        input_dir = Path(config.data_raw_dir)
    
    csv_path = input_dir / f"{station_id}.csv"
    
    if not csv_path.exists():
        logger.warning(f"Station data file not found: {csv_path}")
        return None
    
    try:
        records = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            records = list(reader)
        
        logger.info(f"Loaded {len(records)} records for station {station_id}")
        return records
        
    except Exception as e:
        logger.error(f"Failed to load station data from {csv_path}: {e}")
        return None


if __name__ == "__main__":
    # Simple CLI for testing
    import sys
    
    max_stations = None
    if len(sys.argv) > 1:
        try:
            max_stations = int(sys.argv[1])
        except ValueError:
            pass
    
    summary = ingest_northeast_data(max_stations=max_stations)
    print(json.dumps(summary, indent=2))