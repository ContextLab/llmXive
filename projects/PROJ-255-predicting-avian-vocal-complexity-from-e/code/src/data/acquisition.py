"""
Acquisition module for fetching bird vocalization metadata and audio from Xeno-canto.

This module handles:
- Fetching metadata from the Xeno-canto API
- Filtering records by quality
- Downloading audio files
- Creating metadata CSVs
- Mapping land-use to noise levels (OSM integration placeholder for T015)
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import requests
import pandas as pd
import librosa

from src.utils.config import get_project_root, get_raw_data_dir, get_interim_data_dir

# Constants
XC_API_BASE = "https://xeno-canto.org/api/2/recordings"
XC_API_QUERY = f"{XC_API_BASE}?query="
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1.0

# Quality thresholds
MIN_QUALITY = 'C'  # Accept quality C and above (A, B, C)
QUALITY_SCORES = {'A': 3, 'B': 2, 'C': 1, 'D': 0, 'E': 0}

logger = logging.getLogger(__name__)

def fetch_metadata(species_query: str = "all", max_records: int = 100, 
                   min_quality: str = MIN_QUALITY, limit: int = 50) -> List[Dict]:
    """
    Fetch bird vocalization metadata from Xeno-canto API.
    
    Args:
        species_query: Query string for species (e.g., "Turdus merula" or "all")
        max_records: Maximum number of records to fetch
        min_quality: Minimum quality grade (A, B, C)
        limit: API limit parameter (default 50)
        
    Returns:
        List of metadata dictionaries for matching recordings
        
    Raises:
        requests.RequestException: If API call fails after retries
        ValueError: If invalid quality grade provided
    """
    if min_quality not in QUALITY_SCORES:
        raise ValueError(f"Invalid quality grade: {min_quality}. Must be A, B, C, D, or E.")
    
    encoded_query = requests.utils.quote(species_query)
    url = f"{XC_API_QUERY}{encoded_query}&limit={limit}"
    
    all_records = []
    page = 1
    total_fetched = 0
    
    while total_fetched < max_records:
        retry_count = 0
        while retry_count < MAX_RETRIES:
            try:
                logger.info(f"Fetching page {page} from Xeno-canto API...")
                response = requests.get(url, params={'page': page}, timeout=DEFAULT_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                if 'recordings' not in data:
                    logger.warning("No recordings found in API response")
                    break
                
                records = data['recordings']
                if not records:
                    break
                
                # Filter by quality
                filtered_records = [
                    r for r in records 
                    if QUALITY_SCORES.get(r.get('q', 'E'), 0) >= QUALITY_SCORES[min_quality]
                ]
                
                all_records.extend(filtered_records)
                total_fetched += len(records)
                
                # Check if we've fetched all available
                if page >= data.get('numPages', 1):
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting
                break
                
            except requests.RequestException as e:
                retry_count += 1
                logger.warning(f"API request failed (attempt {retry_count}/{MAX_RETRIES}): {e}")
                if retry_count < MAX_RETRIES:
                    time.sleep(RETRY_DELAY * retry_count)
                else:
                    raise
    
    logger.info(f"Fetched {len(all_records)} valid records out of {total_fetched} total")
    return all_records[:max_records]

def filter_records_by_quality(records: List[Dict], min_quality: str = MIN_QUALITY) -> List[Dict]:
    """
    Filter a list of records by minimum quality grade.
    
    Args:
        records: List of metadata dictionaries
        min_quality: Minimum quality grade to keep
        
    Returns:
        Filtered list of records
    """
    if min_quality not in QUALITY_SCORES:
        raise ValueError(f"Invalid quality grade: {min_quality}")
    
    threshold = QUALITY_SCORES[min_quality]
    filtered = [
        r for r in records 
        if QUALITY_SCORES.get(r.get('q', 'E'), 0) >= threshold
    ]
    
    logger.info(f"Filtered from {len(records)} to {len(filtered)} records (min quality: {min_quality})")
    return filtered

def download_audio(record: Dict, output_dir: Path) -> Optional[Path]:
    """
    Download a single audio file from Xeno-canto.
    
    Args:
        record: Metadata dictionary for a single recording
        output_dir: Directory to save the audio file
        
    Returns:
        Path to downloaded file, or None if download failed
    """
    recording_id = record.get('r', '')
    file_url = record.get('file', '')
    
    if not recording_id or not file_url:
        logger.warning(f"Missing recording ID or URL for record: {record.get('id', 'unknown')}")
        return None
    
    # Create safe filename
    species = record.get('sp', 'unknown').replace(' ', '_')
    recorder = record.get('rec', 'unknown').replace(' ', '_')
    filename = f"{recording_id}_{species}_{recorder}.flac"
    output_path = output_dir / filename
    
    if output_path.exists():
        logger.debug(f"File already exists, skipping: {filename}")
        return output_path
    
    try:
        logger.info(f"Downloading: {filename}")
        response = requests.get(file_url, timeout=DEFAULT_TIMEOUT * 2)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        # Verify file is not empty
        if output_path.stat().st_size == 0:
            logger.error(f"Downloaded file is empty: {filename}")
            output_path.unlink()
            return None
        
        return output_path
        
    except requests.RequestException as e:
        logger.error(f"Failed to download {filename}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading {filename}: {e}")
        return None

def download_batch_audio(records: List[Dict], output_dir: Path, 
                         batch_size: int = 10) -> Tuple[List[Path], List[Dict]]:
    """
    Download a batch of audio files with rate limiting.
    
    Args:
        records: List of metadata dictionaries
        output_dir: Directory to save audio files
        batch_size: Number of records to process before logging
        
    Returns:
        Tuple of (successfully downloaded paths, failed records)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    failed = []
    
    for i, record in enumerate(records):
        result = download_audio(record, output_dir)
        if result:
            downloaded.append(result)
        else:
            failed.append(record)
        
        if (i + 1) % batch_size == 0:
            logger.info(f"Progress: {i + 1}/{len(records)} records processed")
            logger.info(f"Downloaded: {len(downloaded)}, Failed: {len(failed)}")
        
        # Rate limiting between downloads
        time.sleep(0.2)
    
    logger.info(f"Batch download complete: {len(downloaded)} succeeded, {len(failed)} failed")
    return downloaded, failed

def create_metadata_csv(records: List[Dict], output_path: Path) -> None:
    """
    Create a CSV file from metadata records.
    
    Args:
        records: List of metadata dictionaries
        output_path: Path to output CSV file
    """
    if not records:
        logger.warning("No records to write to CSV")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()
        return
    
    # Flatten nested structures for CSV export
    flattened = []
    for record in records:
        flat_record = {
            'recording_id': record.get('r', ''),
            'file': record.get('file', ''),
            'species_id': record.get('sp', ''),
            'species_common': record.get('sp', ''),
            'species_scientific': record.get('snt', ''),
            'recorder': record.get('rec', ''),
            'date': record.get('date', ''),
            'country': record.get('cnt', ''),
            'latitude': record.get('lat'),
            'longitude': record.get('lon'),
            'quality': record.get('q', ''),
            'license': record.get('lc', ''),
            'url': record.get('url', ''),
            'file_type': record.get('fl', ''),
            'file_duration': record.get('dur'),
            'file_size': record.get('sz'),
            'downloaded_path': '',  # Will be filled after download
        }
        flattened.append(flat_record)
    
    df = pd.DataFrame(flattened)
    df.to_csv(output_path, index=False)
    logger.info(f"Created metadata CSV with {len(df)} records: {output_path}")

def get_osm_land_use(lat: float, lon: float) -> Optional[str]:
    """
    Get land-use classification from OpenStreetMap for given coordinates.
    
    This is a placeholder for T015 implementation. Currently returns None
    to indicate that OSM data is not yet available.
    
    Args:
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        Land-use classification string or None if not available
    """
    # T015 will implement actual OSM query using osmnx
    # For now, return None to indicate missing data
    logger.debug(f"OSM land-use query placeholder for ({lat}, {lon})")
    return None

def map_land_use_to_noise(land_use: Optional[str]) -> Optional[float]:
    """
    Map land-use classification to estimated noise level in dB.
    
    Args:
        land_use: Land-use classification string
        
    Returns:
        Noise level in dB or None if mapping not available
    """
    mapping = {
        'urban': 60.0,
        'residential': 55.0,
        'commercial': 65.0,
        'industrial': 70.0,
        'rural': 40.0,
        'agricultural': 35.0,
        'wild': 30.0,
        'forest': 30.0,
        'water': 35.0,
    }
    
    if land_use is None:
        return None
    
    # Case-insensitive lookup
    land_use_lower = land_use.lower().strip()
    return mapping.get(land_use_lower)

def map_noise_levels(records: List[Dict]) -> List[Dict]:
    """
    Add noise level estimates to records based on coordinates.
    
    Args:
        records: List of metadata dictionaries
        
    Returns:
        Updated records with noise_level_db field
    """
    for record in records:
        lat = record.get('lat')
        lon = record.get('lon')
        
        if lat is None or lon is None:
            record['noise_level_db'] = None
            record['land_use'] = None
            continue
        
        try:
            lat = float(lat)
            lon = float(lon)
            
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                land_use = get_osm_land_use(lat, lon)
                noise_db = map_land_use_to_noise(land_use)
                
                record['land_use'] = land_use
                record['noise_level_db'] = noise_db
            else:
                record['land_use'] = None
                record['noise_level_db'] = None
                
        except (ValueError, TypeError):
            record['land_use'] = None
            record['noise_level_db'] = None
    
    return records

def save_noise_mapped_data(records: List[Dict], output_path: Path) -> None:
    """
    Save noise-mapped records to CSV.
    
    Args:
        records: List of records with noise levels
        output_path: Path to output CSV file
    """
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df)} noise-mapped records to {output_path}")

def main(species: str = "all", max_records: int = 50, 
         download_audio_flag: bool = False) -> Tuple[Path, Optional[Path]]:
    """
    Main entry point for data acquisition.
    
    Args:
        species: Species query string
        max_records: Maximum number of records to fetch
        download_audio_flag: Whether to download audio files
        
    Returns:
        Tuple of (metadata_csv_path, audio_dir_path or None)
    """
    project_root = get_project_root()
    raw_data_dir = get_raw_data_dir()
    interim_data_dir = get_interim_data_dir()
    
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    interim_data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting acquisition for species: {species}")
    logger.info(f"Max records: {max_records}")
    
    # Fetch metadata
    records = fetch_metadata(species_query=species, max_records=max_records)
    
    if not records:
        logger.warning("No records fetched. Creating empty output files.")
        metadata_path = raw_data_dir / "metadata.csv"
        create_metadata_csv([], metadata_path)
        return metadata_path, None
    
    # Filter by quality
    filtered_records = filter_records_by_quality(records)
    
    if not filtered_records:
        logger.warning("All records filtered out by quality. Creating empty output.")
        metadata_path = raw_data_dir / "metadata.csv"
        create_metadata_csv([], metadata_path)
        return metadata_path, None
    
    # Create metadata CSV
    metadata_path = raw_data_dir / "metadata.csv"
    create_metadata_csv(filtered_records, metadata_path)
    
    # Download audio if requested
    audio_dir = None
    if download_audio_flag:
        audio_dir = raw_data_dir / "audio"
        downloaded, failed = download_batch_audio(filtered_records, audio_dir)
        logger.info(f"Downloaded {len(downloaded)} audio files, {len(failed)} failed")
        
        # Update metadata with download paths
        for record in filtered_records:
            recording_id = record.get('r', '')
            species = record.get('sp', 'unknown').replace(' ', '_')
            recorder = record.get('rec', 'unknown').replace(' ', '_')
            expected_filename = f"{recording_id}_{species}_{recorder}.flac"
            
            if (audio_dir / expected_filename).exists():
                record['downloaded_path'] = str(audio_dir / expected_filename)
        
        # Re-save metadata with paths
        create_metadata_csv(filtered_records, metadata_path)
    
    # Prepare for T015: Add noise level mapping (placeholder - returns None for now)
    records_with_noise = map_noise_levels(filtered_records)
    noise_mapped_path = interim_data_dir / "noise_mapped.csv"
    save_noise_mapped_data(records_with_noise, noise_mapped_path)
    
    logger.info(f"Acquisition complete. Metadata: {metadata_path}")
    if audio_dir:
        logger.info(f"Audio files: {audio_dir}")
    
    return metadata_path, audio_dir
