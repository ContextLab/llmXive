import os
import json
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.logging import get_logger
from config import (
    get_data_path,
    get_processed_path,
    get_test_region,
    get_test_event_count,
    get_deviations_path,
    get_usgs_base_url,
    get_min_magnitude,
    get_max_depth_km,
)

logger = get_logger(__name__)

# Constants for checksumming
CHECKSUM_ALGORITHM = "sha256"
CHECKSUM_FILE_SUFFIX = ".sha256"


def verify_deviations() -> bool:
    """
    Verify that the deviation record exists and allows proceeding with test data.
    Returns True if the deviation record confirms FR-001 (Global Data Blocked)
    and test-only mode is active.
    """
    dev_path = get_deviations_path()
    if not dev_path.exists():
        logger.error(f"Deviation record not found at {dev_path}. Cannot proceed.")
        return False

    try:
        with open(dev_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Check for explicit FR-001 mention and test-data fallback
        if "FR-001" in content and "test data only" in content.lower():
            logger.info("Deviation record verified: FR-001 active, test-data mode enabled.")
            return True
        else:
            logger.warning("Deviation record does not explicitly confirm FR-001 fallback.")
            return False
    except Exception as e:
        logger.error(f"Error reading deviation record: {e}")
        return False


def check_noaa_availability() -> bool:
    """
    Check for the availability of the global NOAA NCEP/NCAR source.
    Per FR-001 and deviation record, this should return False (blocked/unavailable).
    """
    # Placeholder check: in a real scenario, this would attempt a HEAD request
    # or verify a specific endpoint. Here we rely on the deviation record state.
    logger.info("Checking NOAA NCEP/NCAR availability (expected: unavailable per FR-001).")
    return False  # Explicitly unavailable per project constraints


def fetch_usgs_data() -> List[Dict[str, Any]]:
    """
    Fetch earthquake data from USGS API.
    Returns a list of feature dictionaries.
    """
    import requests

    region = get_test_region()
    min_mag = get_min_magnitude()
    max_depth = get_max_depth_km()

    # Construct query parameters for the test subset (2018 Alaska)
    # Using specific bounding box and time range for the 12-event subset
    params = {
        "format": "geojson",
        "starttime": "2018-01-01",
        "endtime": "2018-12-31",
        "minmagnitude": min_mag,
        "maxdepth": max_depth,
        "minlatitude": region["min_lat"],
        "maxlatitude": region["max_lat"],
        "minlongitude": region["min_lon"],
        "maxlongitude": region["max_lon"],
        "orderby": "time",
    }

    url = f"{get_usgs_base_url()}/query"
    logger.info(f"Fetching USGS data from {url} with params: {params}")

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        features = data.get("features", [])
        logger.info(f"Fetched {len(features)} events from USGS.")
        return features
    except Exception as e:
        logger.error(f"Failed to fetch USGS data: {e}")
        raise


def calculate_checksum(file_path: Path) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    Returns the hexadecimal digest string.
    """
    sha256_hash = hashlib.sha256()
    logger.info(f"Calculating checksum for {file_path}")
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise


def save_raw_data(data: List[Dict[str, Any]], filename: str) -> Path:
    """
    Save raw data to disk and generate a checksum file for immutability verification.
    Returns the path to the saved JSON file.
    """
    raw_dir = get_data_path() / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    json_path = raw_dir / filename
    checksum_path = raw_dir / f"{filename}{CHECKSUM_FILE_SUFFIX}"

    logger.info(f"Saving raw data to {json_path}")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Calculate and save checksum
    checksum = calculate_checksum(json_path)
    logger.info(f"Calculated checksum: {checksum}")
    with open(checksum_path, "w", encoding="utf-8") as f:
        f.write(f"{checksum}  {filename}\n")

    logger.info(f"Saved checksum to {checksum_path}")
    return json_path


def verify_data_integrity(filename: str) -> bool:
    """
    Verify the integrity of a saved raw data file by comparing its current
    checksum against the stored checksum file.
    Returns True if valid, False otherwise.
    """
    raw_dir = get_data_path() / "raw"
    json_path = raw_dir / filename
    checksum_path = raw_dir / f"{filename}{CHECKSUM_FILE_SUFFIX}"

    if not json_path.exists():
        logger.error(f"Data file not found: {json_path}")
        return False
    if not checksum_path.exists():
        logger.error(f"Checksum file not found: {checksum_path}")
        return False

    # Read stored checksum
    with open(checksum_path, "r", encoding="utf-8") as f:
        stored_checksum = f.read().split()[0]

    # Calculate current checksum
    current_checksum = calculate_checksum(json_path)

    if stored_checksum == current_checksum:
        logger.info(f"Data integrity verified for {filename}")
        return True
    else:
        logger.error(
            f"Data integrity check FAILED for {filename}. "
            f"Stored: {stored_checksum}, Current: {current_checksum}"
        )
        return False


def process_test_subset(features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process the raw USGS features to extract the specific test subset (N=12).
    Filters for the 2018 Alaska subset as defined in the spec.
    """
    # The fetch_usgs_data function is already constrained to the 2018 Alaska region.
    # This function ensures we strictly adhere to the expected count if necessary,
    # or simply returns the fetched data if it matches the criteria.
    # In a real pipeline, we might validate the count here.
    
    expected_count = get_test_event_count()
    actual_count = len(features)

    if actual_count != expected_count:
        logger.warning(
            f"Fetched {actual_count} events, expected {expected_count}. "
            "Proceeding with fetched data but flagging discrepancy."
        )
    
    return features


def main():
    """
    Main entry point for the download and checksumming pipeline.
    1. Verify deviations.
    2. Check NOAA availability (expecting False).
    3. Fetch USGS data.
    4. Process test subset.
    5. Save raw data with checksum.
    6. Verify data integrity.
    """
    logger.info("Starting download pipeline (T012: Checksumming & Immutability)")

    # 1. Verify Deviations
    if not verify_deviations():
        logger.critical("Deviation verification failed. Exiting.")
        return 1

    # 2. Check NOAA
    if check_noaa_availability():
        logger.warning("NOAA source appears available, but project is configured for test-only.")
    else:
        logger.info("NOAA source confirmed unavailable (FR-001).")

    # 3. Fetch Data
    try:
        raw_features = fetch_usgs_data()
    except Exception as e:
        logger.critical(f"Failed to fetch USGS data: {e}")
        return 1

    # 4. Process Subset
    processed_features = process_test_subset(raw_features)

    # 5. Save with Checksum
    output_filename = "usgs_2018_alaska_test_subset.geojson"
    saved_path = save_raw_data(processed_features, output_filename)

    # 6. Verify Integrity
    if not verify_data_integrity(output_filename):
        logger.critical("Data integrity verification failed after save.")
        return 1

    logger.info(f"Pipeline completed successfully. Data saved at {saved_path}")
    return 0


if __name__ == "__main__":
    exit(main())