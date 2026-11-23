"""
Data Acquisition Module for Avian Vocal Complexity Project.

This module handles:
1. Fetching metadata from Xeno-canto API
2. Downloading audio files
3. Querying OpenStreetMap (OSM) via osmnx for land-use data
4. Mapping land-use to noise levels
5. Creating noise-mapped datasets
"""

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
from geopy.geocoders import Nominatim

from src.utils.config import get_project_root, get_raw_data_dir, get_interim_data_dir
from src.utils.logging import setup_logger

# Configure logging
logger = setup_logger(__name__)

# Constants
XENO_CANTO_API_BASE = "https://xeno-canto.org/api/2/recordings"
OSMPHONES_TIMEOUT = 30
NOISE_LEVELS = {
    "urban": 60,
    "residential": 55,
    "industrial": 65,
    "commercial": 58,
    "rural": 40,
    "forest": 30,
    "wild": 30,
    "agricultural": 45,
    "water": 35,
    "grassland": 35,
    "wetland": 35,
    "mountain": 30,
    "park": 40,
    "green_space": 40,
    "default": 45  # Fallback for unmapped land-use types
}

def fetch_metadata(query: str = "all", max_records: int = 100) -> List[Dict[str, Any]]:
    """
    Fetch bird recording metadata from Xeno-canto API.

    Args:
        query: Search query (e.g., "species:Zonotrichia capensis")
        max_records: Maximum number of records to fetch

    Returns:
        List of recording metadata dictionaries
    """
    url = f"{XENO_CANTO_API_BASE}?query={query}&format=json&max={max_records}"
    logger.info(f"Fetching metadata from Xeno-canto: {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        recordings = data.get("recordings", [])
        logger.info(f"Fetched {len(recordings)} recordings")

        return recordings

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch metadata: {e}")
        raise


def filter_records_by_quality(recordings: List[Dict[str, Any]], min_quality: str = "B") -> List[Dict[str, Any]]:
    """
    Filter recordings by quality grade.

    Args:
        recordings: List of recording metadata
        min_quality: Minimum quality grade (A, B, C, D, X)

    Returns:
        Filtered list of recordings
    """
    quality_order = {"A": 0, "B": 1, "C": 2, "D": 3, "X": 4}
    min_quality_idx = quality_order.get(min_quality.upper(), 0)

    filtered = [
        r for r in recordings
        if r.get("q", "X") in quality_order and quality_order.get(r.get("q", "X"), 4) <= min_quality_idx
    ]

    logger.info(f"Filtered from {len(recordings)} to {len(filtered)} recordings (min quality: {min_quality})")
    return filtered


def download_audio(recording_id: str, output_dir: Path, overwrite: bool = False) -> Optional[Path]:
    """
    Download a single audio recording.

    Args:
        recording_id: Xeno-canto recording ID
        output_dir: Directory to save the audio file
        overwrite: Whether to overwrite existing files

    Returns:
        Path to downloaded file, or None if failed
    """
    audio_url = f"https://xeno-canto.org/{recording_id}.mp3"
    output_path = output_dir / f"{recording_id}.mp3"

    if output_path.exists() and not overwrite:
        logger.debug(f"Audio already exists: {output_path}")
        return output_path

    try:
        response = requests.get(audio_url, timeout=60)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(response.content)

        logger.info(f"Downloaded: {output_path}")
        return output_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {recording_id}: {e}")
        return None


def download_batch_audio(recordings: List[Dict[str, Any]], output_dir: Path, max_concurrent: int = 5) -> List[Path]:
    """
    Download multiple audio recordings.

    Args:
        recordings: List of recording metadata
        output_dir: Directory to save audio files
        max_concurrent: Maximum concurrent downloads

    Returns:
        List of paths to successfully downloaded files
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    for i, rec in enumerate(recordings):
        rec_id = rec.get("id")
        if rec_id:
            result = download_audio(rec_id, output_dir)
            if result:
                downloaded.append(result)

            # Rate limiting
            if (i + 1) % 10 == 0:
                time.sleep(1)

    logger.info(f"Downloaded {len(downloaded)}/{len(recordings)} audio files")
    return downloaded


def create_metadata_csv(recordings: List[Dict[str, Any]], output_path: Path) -> Path:
    """
    Create a CSV file from recording metadata.

    Args:
        recordings: List of recording metadata
        output_path: Path to output CSV

    Returns:
        Path to created CSV file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Flatten and select relevant fields
    rows = []
    for rec in recordings:
        row = {
            "recording_id": rec.get("id"),
            "species_id": rec.get("species"),
            "species_name": rec.get("speciesname"),
            "file": rec.get("file"),
            "loc": rec.get("loc"),
            "lat": rec.get("lat"),
            "lon": rec.get("lon"),
            "quality": rec.get("q"),
            "date": rec.get("date"),
            "recorder": rec.get("rec"),
            "country": rec.get("cnt"),
            "language": rec.get("lang"),
            "sex": rec.get("sex"),
            "age": rec.get("age"),
            "behavior": rec.get("beh"),
            "filetype": rec.get("filetype"),
            "views": rec.get("views"),
            "downloaded": rec.get("downloads"),
            "rating": rec.get("rating"),
            "uploaded": rec.get("uploaded"),
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Created metadata CSV: {output_path} with {len(df)} rows")

    return output_path


def get_osm_land_use(lat: float, lon: float, network_type: str = "drive", timeout: int = 30) -> Optional[str]:
    """
    Query OpenStreetMap for land-use at given coordinates.

    Args:
        lat: Latitude
        lon: Longitude
        network_type: OSM network type for querying
        timeout: Request timeout in seconds

    Returns:
        Land-use tag string or None if not found
    """
    try:
        # Use Nominatim to reverse geocode and get place details
        geolocator = Nominatim(user_agent="llmXive_avian_project")
        location = geolocator.reverse(f"{lat}, {lon}", timeout=timeout)

        if not location or not location.raw:
            logger.debug(f"No location data for {lat}, {lon}")
            return None

        raw = location.raw
        tags = raw.get("address", {})

        # Try to find land-use or landuse tag
        land_use_keys = ["landuse", "land-use", "leisure", "natural", "place", "area", "building"]
        for key in land_use_keys:
            if key in tags:
                return str(tags[key]).lower()

        # Fallback to place type
        if "place" in tags:
            return str(tags["place"]).lower()

        logger.debug(f"No land-use tag found for {lat}, {lon}, address keys: {list(tags.keys())}")
        return None

    except Exception as e:
        logger.warning(f"OSM query failed for {lat}, {lon}: {e}")
        return None


def map_land_use_to_noise(land_use: str) -> int:
    """
    Map OSM land-use tag to noise level in dB.

    Args:
        land_use: Land-use tag string

    Returns:
        Noise level in dB
    """
    if not land_use:
        return NOISE_LEVELS["default"]

    land_use_lower = land_use.lower().strip()

    # Direct match
    if land_use_lower in NOISE_LEVELS:
        return NOISE_LEVELS[land_use_lower]

    # Partial match for common variations
    partial_matches = {
        "city": "urban",
        "town": "urban",
        "suburb": "urban",
        "residential": "residential",
        "industrial": "industrial",
        "commercial": "commercial",
        "forest": "forest",
        "woods": "forest",
        "wilderness": "wild",
        "rural": "rural",
        "farm": "agricultural",
        "agriculture": "agricultural",
        "water": "water",
        "lake": "water",
        "river": "water",
        "grass": "grassland",
        "meadow": "grassland",
        "wetland": "wetland",
        "swamp": "wetland",
        "mountain": "mountain",
        "hill": "mountain",
        "park": "park",
        "garden": "green_space",
        "green": "green_space",
    }

    for pattern, mapped in partial_matches.items():
        if pattern in land_use_lower:
            return NOISE_LEVELS.get(mapped, NOISE_LEVELS["default"])

    return NOISE_LEVELS["default"]


def map_noise_levels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add noise_level_db column to dataframe based on land-use.

    Args:
        df: DataFrame with land_use column

    Returns:
        DataFrame with added noise_level_db column
    """
    df = df.copy()

    if "land_use" not in df.columns:
        logger.warning("DataFrame missing 'land_use' column")
        return df

    def get_noise(row):
        return map_land_use_to_noise(row.get("land_use"))

    df["noise_level_db"] = df.apply(get_noise, axis=1)
    logger.info(f"Mapped noise levels for {len(df)} records")

    return df


def save_noise_mapped_data(df: pd.DataFrame, dropped_df: pd.DataFrame) -> Tuple[Path, Path]:
    """
    Save noise-mapped data and dropped records to CSV files.

    Args:
        df: DataFrame with noise-mapped records
        dropped_df: DataFrame with dropped records (missing OSM)

    Returns:
        Tuple of (noise_mapped_path, dropped_path)
    """
    interim_dir = get_interim_data_dir()
    interim_dir.mkdir(parents=True, exist_ok=True)

    noise_mapped_path = interim_dir / "noise_mapped.csv"
    dropped_path = interim_dir / "dropped_missing_osm.csv"

    df.to_csv(noise_mapped_path, index=False)
    dropped_df.to_csv(dropped_path, index=False)

    logger.info(f"Saved noise-mapped data: {noise_mapped_path} ({len(df)} records)")
    logger.info(f"Saved dropped records: {dropped_path} ({len(dropped_df)} records)")

    return noise_mapped_path, dropped_path


def process_recordings_with_osm(recordings: List[Dict[str, Any]], rate_limit: float = 1.0) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Process recordings: fetch OSM land-use and map to noise levels.

    Args:
        recordings: List of recording metadata
        rate_limit: Seconds to wait between OSM queries

    Returns:
        Tuple of (noise_mapped_df, dropped_df)
    """
    processed_rows = []
    dropped_rows = []

    logger.info(f"Processing {len(recordings)} recordings with OSM queries")

    for i, rec in enumerate(recordings):
        lat = rec.get("lat")
        lon = rec.get("lon")

        # Skip if no coordinates
        if lat is None or lon is None:
            dropped_rows.append({
                "recording_id": rec.get("id"),
                "species_id": rec.get("species"),
                "reason": "missing_coordinates"
            })
            continue

        # Query OSM for land-use
        land_use = get_osm_land_use(float(lat), float(lon))

        if land_use is None:
            dropped_rows.append({
                "recording_id": rec.get("id"),
                "species_id": rec.get("species"),
                "lat": lat,
                "lon": lon,
                "reason": "missing_osm_data"
            })
            continue

        # Map to noise level
        noise_db = map_land_use_to_noise(land_use)

        processed_rows.append({
            "recording_id": rec.get("id"),
            "species_id": rec.get("species"),
            "species_name": rec.get("speciesname"),
            "lat": lat,
            "lon": lon,
            "land_use": land_use,
            "noise_level_db": noise_db,
            "quality": rec.get("q"),
            "country": rec.get("cnt"),
            "date": rec.get("date")
        })

        # Rate limiting
        if i < len(recordings) - 1:
            time.sleep(rate_limit)

    processed_df = pd.DataFrame(processed_rows) if processed_rows else pd.DataFrame()
    dropped_df = pd.DataFrame(dropped_rows) if dropped_rows else pd.DataFrame()

    logger.info(f"Processed: {len(processed_df)}, Dropped: {len(dropped_df)}")

    return processed_df, dropped_df


def main():
    """
    Main entry point for T015: OSM-based noise level mapping.

    This function:
    1. Fetches metadata from Xeno-canto
    2. Queries OSM for land-use at each recording location
    3. Maps land-use to noise levels
    4. Saves noise_mapped.csv and dropped_missing_osm.csv
    """
    logger.info("Starting T015: OSM noise level mapping")

    # Fetch metadata (use a small subset for testing if needed)
    # In production, this would use a proper species query
    recordings = fetch_metadata(query="all", max_records=50)

    if not recordings:
        logger.error("No recordings fetched from Xeno-canto")
        return

    # Filter by quality
    filtered_recordings = filter_records_by_quality(recordings, min_quality="B")

    if not filtered_recordings:
        logger.warning("No recordings passed quality filter")
        return

    # Process with OSM queries
    noise_mapped_df, dropped_df = process_recordings_with_osm(
        filtered_recordings,
        rate_limit=1.0  # 1 second between OSM queries
    )

    # Save outputs
    if not noise_mapped_df.empty:
        noise_mapped_path, dropped_path = save_noise_mapped_data(noise_mapped_df, dropped_df)
        logger.info(f"T015 completed successfully")
        logger.info(f"  - Noise mapped: {noise_mapped_path}")
        logger.info(f"  - Dropped records: {dropped_path}")
    else:
        logger.warning("No records were successfully mapped to noise levels")
        # Still save dropped records if any
        if not dropped_df.empty:
            dropped_path = get_interim_data_dir() / "dropped_missing_osm.csv"
            dropped_df.to_csv(dropped_path, index=False)
            logger.info(f"  - Dropped records: {dropped_path}")


if __name__ == "__main__":
    main()
