import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import requests
import pandas as pd
import osmnx as ox

from src.utils.config import get_project_root, get_interim_data_dir, get_raw_data_dir, ensure_directories
from src.utils.logging import setup_logger

# Configure logger for this module
logger = setup_logger("acquisition")

# Constants for land-use to noise mapping
LAND_USE_NOISE_MAP = {
    'residential': 60,
    'commercial': 60,
    'industrial': 65,
    'urban': 60,
    'city': 60,
    'town': 55,
    'village': 50,
    'farm': 40,
    'farmland': 40,
    'rural': 40,
    'forest': 30,
    'wild': 30,
    'natural': 30,
    'water': 30,
    'wetland': 30,
    'park': 35,
    'garden': 40,
    'recreation_ground': 45,
    'leisure': 45,
    'cemetery': 35,
    'grave_yard': 35
}

DEFAULT_NOISE_LEVEL = 50  # Fallback if mapping fails but OSM exists
MISSING_OSM_NOISE_LEVEL = None

def get_osm_land_use(lat: float, lon: float, radius: int = 500) -> Optional[str]:
    """
    Query OpenStreetMap via osmnx to get the dominant land-use type
    at a given coordinate.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Radius in meters to search (default 500m)
        
    Returns:
        Dominant land-use tag string, or None if no data found.
    """
    try:
        # Use osmnx to get place features around the point
        # We query for landuse tags specifically
        gdf = ox.features_from_point((lon, lat), tags={'landuse': True}, dist=radius)
        
        if gdf.empty:
            logger.debug(f"No landuse data found for ({lat}, {lon}) within {radius}m")
            return None
        
        # Get the most common landuse value
        landuse_counts = gdf['landuse'].value_counts()
        if len(landuse_counts) == 0:
            return None
        
        dominant_landuse = landuse_counts.index[0].lower()
        logger.debug(f"Dominant landuse for ({lat}, {lon}): {dominant_landuse}")
        return dominant_landuse
        
    except Exception as e:
        logger.warning(f"OSM query failed for ({lat}, {lon}): {e}")
        return None

def map_land_use_to_noise(land_use: str) -> Optional[int]:
    """
    Map a land-use string to a noise level in dB.
    
    Args:
        land_use: Land-use category string
        
    Returns:
        Noise level in dB, or None if mapping not found.
    """
    if not land_use:
        return None
        
    land_use_lower = land_use.lower().strip()
    
    # Direct match
    if land_use_lower in LAND_USE_NOISE_MAP:
        return LAND_USE_NOISE_MAP[land_use_lower]
    
    # Partial match (e.g., "residential_area" -> "residential")
    for key in LAND_USE_NOISE_MAP:
        if key in land_use_lower or land_use_lower in key:
            return LAND_USE_NOISE_MAP[key]
    
    logger.debug(f"No noise mapping for land-use: {land_use}")
    return None

def map_noise_levels(land_use: str) -> Tuple[Optional[int], bool]:
    """
    Map land-use to noise level and indicate if OSM data was found.
    
    Args:
        land_use: Land-use category string
        
    Returns:
        Tuple of (noise_level_db, osm_found)
        - noise_level_db: The mapped noise level or None
        - osm_found: True if land_use was provided (OSM query succeeded)
    """
    if land_use is None:
        return None, False
        
    noise_level = map_land_use_to_noise(land_use)
    return noise_level, True

def fetch_metadata_from_xeno_canto(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch bird recording metadata from Xeno-canto API.
    
    Args:
        query: Search query (e.g., species name, country)
        max_results: Maximum number of results to fetch
        
    Returns:
        List of recording metadata dictionaries
    """
    base_url = "https://xeno-canto.org/api/2/recordings"
    params = {
        'q': query,
        'limit': max_results,
        'format': 'json'
    }
    
    try:
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        recordings = []
        for rec in data.get('recordings', []):
            recordings.append({
                'id': rec.get('id'),
                'species': rec.get('sp'),
                'species_code': rec.get('sp'),
                'latitude': float(rec.get('lat', 0)),
                'longitude': float(rec.get('lng', 0)),
                'country': rec.get('cnt'),
                'file_type': rec.get('file-type'),
                'quality': rec.get('q'),
                'url': rec.get('file'),
                'recording_date': rec.get('date'),
                'recording_id': rec.get('rec-id')
            })
        
        logger.info(f"Fetched {len(recordings)} recordings for query: {query}")
        return recordings
        
    except Exception as e:
        logger.error(f"Failed to fetch metadata from Xeno-canto: {e}")
        return []

def filter_records_by_quality(recordings: List[Dict], min_quality: str = 'B') -> List[Dict]:
    """
    Filter recordings by quality grade.
    
    Args:
        recordings: List of recording metadata
        min_quality: Minimum quality grade (A, B, C, D)
        
    Returns:
        Filtered list of recordings
    """
    quality_order = {'A': 0, 'B': 1, 'C': 2, 'D': 3}
    min_quality_val = quality_order.get(min_quality, 0)
    
    filtered = []
    for rec in recordings:
        rec_quality = rec.get('quality', 'D')
        if quality_order.get(rec_quality, 3) <= min_quality_val:
            filtered.append(rec)
    
    logger.info(f"Filtered to {len(filtered)} recordings with quality >= {min_quality}")
    return filtered

def download_audio(audio_url: str, output_path: Path) -> bool:
    """
    Download audio file from URL.
    
    Args:
        audio_url: URL to audio file
        output_path: Local path to save the file
        
    Returns:
        True if download successful, False otherwise
    """
    try:
        response = requests.get(audio_url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded audio to {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to download audio from {audio_url}: {e}")
        return False

def download_batch_audio(recordings: List[Dict], output_dir: Path, max_downloads: int = 5) -> List[Dict]:
    """
    Download audio files for multiple recordings with rate limiting.
    
    Args:
        recordings: List of recording metadata
        output_dir: Directory to save audio files
        max_downloads: Maximum concurrent downloads (not implemented, sequential only)
        
    Returns:
        List of recordings with download status
    """
    ensure_directories()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    downloaded = []
    for i, rec in enumerate(recordings):
        # Rate limiting
        if i > 0:
            time.sleep(1)
        
        filename = f"{rec['recording_id']}.mp3"
        output_path = output_dir / filename
        
        success = download_audio(rec['url'], output_path)
        rec['downloaded'] = success
        rec['local_path'] = str(output_path) if success else None
        downloaded.append(rec)
        
        if success:
            logger.info(f"Downloaded {i+1}/{len(recordings)}: {rec['species']}")
        else:
            logger.warning(f"Failed download {i+1}/{len(recordings)}: {rec['species']}")
    
    return downloaded

def create_metadata_csv(recordings: List[Dict], output_path: Path) -> None:
    """
    Save recording metadata to CSV.
    
    Args:
        recordings: List of recording metadata
        output_path: Output CSV path
    """
    if not recordings:
        logger.warning("No recordings to save to CSV")
        return
    
    df = pd.DataFrame(recordings)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metadata to {output_path}")

def save_noise_mapped_data(mapped_data: List[Dict], output_path: Path, dropped_data: List[Dict], dropped_path: Path) -> None:
    """
    Save noise-mapped data and dropped records to CSV files.
    
    Args:
        mapped_data: List of records with noise levels
        output_path: Path for noise_mapped.csv
        dropped_data: List of records dropped due to missing OSM
        dropped_path: Path for dropped_missing_osm.csv
    """
    ensure_directories()
    
    if mapped_data:
        df_mapped = pd.DataFrame(mapped_data)
        df_mapped.to_csv(output_path, index=False)
        logger.info(f"Saved {len(mapped_data)} records to {output_path}")
    else:
        logger.warning("No data to save to noise_mapped.csv")
        # Create empty file with headers
        pd.DataFrame(columns=['recording_id', 'species', 'latitude', 'longitude', 'noise_level_db']).to_csv(output_path, index=False)
    
    if dropped_data:
        df_dropped = pd.DataFrame(dropped_data)
        df_dropped.to_csv(dropped_path, index=False)
        logger.info(f"Saved {len(dropped_data)} dropped records to {dropped_path}")
    else:
        logger.info("No records dropped due to missing OSM data")
        # Create empty file with headers
        pd.DataFrame(columns=['recording_id', 'species', 'latitude', 'longitude', 'reason']).to_csv(dropped_path, index=False)

def main(query: str = "Turdus merula", max_results: int = 50, min_quality: str = 'B') -> Tuple[Path, Path]:
    """
    Main function to execute the T015 task:
    1. Fetch metadata from Xeno-canto
    2. Filter by quality
    3. Query OSM for land-use at each coordinate
    4. Map land-use to noise levels
    5. Drop records with missing OSM data
    6. Save results to CSV files
    
    Args:
        query: Xeno-canto search query
        max_results: Maximum recordings to fetch
        min_quality: Minimum quality grade
        
    Returns:
        Tuple of (noise_mapped_path, dropped_path)
    """
    logger.info(f"Starting T015 task for query: {query}")
    
    # Get output directories
    interim_dir = get_interim_data_dir()
    ensure_directories()
    
    noise_mapped_path = interim_dir / "noise_mapped.csv"
    dropped_path = interim_dir / "dropped_missing_osm.csv"
    
    # Step 1: Fetch metadata
    logger.info("Fetching metadata from Xeno-canto...")
    recordings = fetch_metadata_from_xeno_canto(query, max_results)
    
    if not recordings:
        logger.error("No recordings fetched. Exiting.")
        # Create empty output files
        pd.DataFrame(columns=['recording_id', 'species', 'latitude', 'longitude', 'noise_level_db']).to_csv(noise_mapped_path, index=False)
        pd.DataFrame(columns=['recording_id', 'species', 'latitude', 'longitude', 'reason']).to_csv(dropped_path, index=False)
        return noise_mapped_path, dropped_path
    
    # Step 2: Filter by quality
    logger.info(f"Filtering by quality >= {min_quality}...")
    filtered_recordings = filter_records_by_quality(recordings, min_quality)
    
    if not filtered_recordings:
        logger.warning("No recordings passed quality filter.")
        pd.DataFrame(columns=['recording_id', 'species', 'latitude', 'longitude', 'noise_level_db']).to_csv(noise_mapped_path, index=False)
        pd.DataFrame(columns=['recording_id', 'species', 'latitude', 'longitude', 'reason']).to_csv(dropped_path, index=False)
        return noise_mapped_path, dropped_path
    
    # Step 3 & 4: Query OSM and map to noise levels
    logger.info("Querying OSM for land-use data...")
    mapped_data = []
    dropped_data = []
    
    for i, rec in enumerate(filtered_recordings):
        lat = rec['latitude']
        lon = rec['longitude']
        
        # Skip invalid coordinates
        if lat == 0 and lon == 0:
            dropped_data.append({
                'recording_id': rec['recording_id'],
                'species': rec['species'],
                'latitude': lat,
                'longitude': lon,
                'reason': 'Invalid coordinates (0,0)'
            })
            continue
        
        # Query OSM
        land_use = get_osm_land_use(lat, lon)
        
        if land_use is None:
            dropped_data.append({
                'recording_id': rec['recording_id'],
                'species': rec['species'],
                'latitude': lat,
                'longitude': lon,
                'reason': 'OSM data missing'
            })
            continue
        
        # Map to noise level
        noise_level, _ = map_noise_levels(land_use)
        
        if noise_level is None:
            # OSM found but no mapping - use default
            noise_level = DEFAULT_NOISE_LEVEL
        
        mapped_data.append({
            'recording_id': rec['recording_id'],
            'species': rec['species'],
            'latitude': lat,
            'longitude': lon,
            'land_use': land_use,
            'noise_level_db': noise_level
        })
        
        if (i + 1) % 10 == 0:
            logger.info(f"Processed {i+1}/{len(filtered_recordings)} recordings")
    
    # Step 5: Save results
    logger.info("Saving results...")
    save_noise_mapped_data(mapped_data, noise_mapped_path, dropped_data, dropped_path)
    
    logger.info(f"T015 task completed. Mapped: {len(mapped_data)}, Dropped: {len(dropped_data)}")
    return noise_mapped_path, dropped_path

if __name__ == "__main__":
    # Default execution for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="T015: OSM Noise Mapping")
    parser.add_argument('--query', type=str, default="Turdus merula", help="Xeno-canto query")
    parser.add_argument('--max-results', type=int, default=50, help="Maximum recordings to fetch")
    parser.add_argument('--min-quality', type=str, default='B', help="Minimum quality grade")
    
    args = parser.parse_args()
    
    main(args.query, args.max_results, args.min_quality)
