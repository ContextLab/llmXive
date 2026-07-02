"""
Fetch real avian acoustic metadata from Xeno-Canto API.

This script downloads a sample of real recording metadata (species_id, lat, lon)
from the Xeno-Canto API, saves it to data/raw/xeno_canto_sample.csv, records
the SHA256 checksum to data/checksums.txt, and aborts on fetch failure.
"""

import os
import sys
import csv
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config
from data_setup import initialize_checksums_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Xeno-Canto API configuration
XENO_CANTO_API_URL = "https://www.xeno-canto.org/api/2/recordings"
# Request a manageable sample of 100 records for initial processing
SAMPLE_SIZE = 100

def fetch_xeno_canto_data(max_records: int = SAMPLE_SIZE) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch real recording metadata from Xeno-Canto API.

    Args:
        max_records: Maximum number of records to fetch.

    Returns:
        List of dictionaries containing recording metadata, or None on failure.
    """
    params = {
        'query': 'country:US',  # Filter for US records to ensure quality data
        'format': 'json',
        'page': 1,
        'per_page': max_records
    }

    try:
        logger.info(f"Fetching {max_records} records from Xeno-Canto API...")
        response = requests.get(XENO_CANTO_API_URL, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        recordings = data.get('recordings', [])

        if not recordings:
            logger.warning("No recordings found in API response.")
            return None

        logger.info(f"Successfully fetched {len(recordings)} recordings.")
        return recordings

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from Xeno-Canto API: {e}")
        return None
    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        return None

def extract_metadata(recordings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract required metadata fields from Xeno-Canto recordings.

    Args:
        recordings: List of raw recording dictionaries.

    Returns:
        List of dictionaries with extracted fields: species_id, lat, lon.
    """
    extracted = []
    for rec in recordings:
        # Xeno-Canto returns 'sp' for species, 'lat' and 'lon' for coordinates
        # We need to map 'sp' to a species_id format (using the species code)
        species_code = rec.get('sp')
        lat = rec.get('lat')
        lon = rec.get('lon')

        # Skip records with missing critical data
        if not species_code or lat is None or lon is None:
            continue

        # Convert lat/lon to float if they are strings
        try:
            lat_val = float(lat)
            lon_val = float(lon)
        except (ValueError, TypeError):
            continue

        extracted.append({
            'species_id': species_code,
            'lat': lat_val,
            'lon': lon_val,
            'recording_id': rec.get('id'),
            'file_type': rec.get('file-type'),
            'quality': rec.get('q')
        })

    logger.info(f"Extracted metadata for {len(extracted)} valid records.")
    return extracted

def save_to_csv(data: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Save extracted metadata to a CSV file.

    Args:
        data: List of dictionaries to save.
        output_path: Path to the output CSV file.

    Returns:
        True if successful, False otherwise.
    """
    if not data:
        logger.error("No data to save.")
        return False

    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write CSV
        fieldnames = ['species_id', 'lat', 'lon', 'recording_id', 'file_type', 'quality']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Saved {len(data)} records to {output_path}")
        return True

    except IOError as e:
        logger.error(f"Failed to write CSV file: {e}")
        return False

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA256 hash string.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Failed to calculate checksum: {e}")
        raise

def update_checksums_file(file_path: Path, checksums_path: Path) -> None:
    """
    Update the checksums file with the new file's checksum.

    Args:
        file_path: Path to the file being checksummed.
        checksums_path: Path to the checksums file.
    """
    checksum = calculate_sha256(file_path)
    relative_path = file_path.relative_to(PROJECT_ROOT)

    # Initialize checksums file if it doesn't exist
    initialize_checksums_file(checksums_path)

    # Read existing checksums
    checksums = {}
    if checksums_path.exists():
        with open(checksums_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ':' in line:
                    path, hash_val = line.split(':', 1)
                    checksums[path.strip()] = hash_val.strip()

    # Update or add the new checksum
    checksums[str(relative_path)] = checksum

    # Write back to file
    with open(checksums_path, 'w', encoding='utf-8') as f:
        for path, hash_val in checksums.items():
            f.write(f"{path}: {hash_val}\n")

    logger.info(f"Updated checksum for {relative_path} in {checksums_path}")

def main():
    """Main entry point for fetching Xeno-Canto data."""
    config = Config()
    data_dir = config.data_dir
    raw_dir = data_dir / "raw"
    checksums_file = data_dir / "checksums.txt"
    output_file = raw_dir / "xeno_canto_sample.csv"

    # Ensure raw directory exists
    raw_dir.mkdir(parents=True, exist_ok=True)

    # Fetch data
    recordings = fetch_xeno_canto_data()
    if recordings is None:
        logger.error("Aborting: Failed to fetch data from Xeno-Canto API.")
        sys.exit(1)

    # Extract metadata
    metadata = extract_metadata(recordings)
    if not metadata:
        logger.error("Aborting: No valid metadata extracted.")
        sys.exit(1)

    # Save to CSV
    if not save_to_csv(metadata, output_file):
        logger.error("Aborting: Failed to save data to CSV.")
        sys.exit(1)

    # Calculate and record checksum
    try:
        update_checksums_file(output_file, checksums_file)
    except Exception as e:
        logger.error(f"Aborting: Failed to update checksums: {e}")
        sys.exit(1)

    logger.info("Xeno-Canto data fetch completed successfully.")

if __name__ == "__main__":
    main()
