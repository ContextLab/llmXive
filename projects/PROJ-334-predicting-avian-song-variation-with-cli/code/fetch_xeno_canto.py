import os
import sys
import csv
import hashlib
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests

# Import utilities from the project API surface
from utils import setup_logging, update_state_file, compute_file_hash
from config import load_config

# Project constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUMS_FILE = PROJECT_ROOT / "data" / "checksums.txt"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli.yaml"

# Output file paths
OUTPUT_FILE = DATA_RAW_DIR / "xeno_canto_sample.csv"
SAMPLE_FILE_PATH = str(OUTPUT_FILE)

# Xeno-Canto API configuration
XENO_CANTO_BASE_URL = "https://xeno-canto.org/api/2/recordings"
DEFAULT_LIMIT = 1000  # Limit to prevent overwhelming the API in a single run
STREAMING_CHUNK_SIZE = 100

logger = setup_logging("fetch_xeno_canto")

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums_file(file_path: str, hash_value: str) -> None:
    """Update the checksums.txt file with the new hash."""
    checksums_path = Path(file_path)
    if not checksums_path.exists():
        # Initialize with header if missing
        with open(checksums_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'sha256_hash'])
    
    # Read existing checksums
    existing = {}
    with open(checksums_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing[row['filename']] = row['sha256_hash']
    
    # Update or add the new hash
    filename = os.path.basename(file_path)
    existing[filename] = hash_value
    
    # Write back
    with open(checksums_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['filename', 'sha256_hash'])
        writer.writeheader()
        for fname, hsh in existing.items():
            writer.writerow({'filename': fname, 'sha256_hash': hsh})

def fetch_page(query: str = "all", page: int = 1, limit: int = 100) -> Optional[Dict[str, Any]]:
    """Fetch a single page of recordings from Xeno-Canto API."""
    url = f"{XENO_CANTO_BASE_URL}?query={query}&page={page}&limit={limit}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch page {page}: {e}")
        return None

def fetch_xeno_canto_data(limit: int = DEFAULT_LIMIT) -> List[Dict[str, Any]]:
    """
    Fetch real metadata from Xeno-Canto API.
    Uses streaming/chunked fetching to handle large datasets.
    Returns a list of records containing species_id, lat, lon.
    """
    records = []
    page = 1
    total_fetched = 0
    
    logger.info(f"Starting fetch from Xeno-Canto API (limit: {limit})")
    
    while total_fetched < limit:
        current_limit = min(STREAMING_CHUNK_SIZE, limit - total_fetched)
        data = fetch_page(page=page, limit=current_limit)
        
        if not data or 'recordings' not in data:
            logger.warning("No more data received or invalid response structure.")
            break
        
        recordings = data['recordings']
        if not recordings:
            break
        
        for rec in recordings:
            # Extract required fields: species_id, lat, lon
            # Xeno-Canto returns 'sp' for species, 'lat'/'lon' for coordinates
            # We map 'sp' to 'species_id'
            species = rec.get('sp')
            lat = rec.get('lat')
            lon = rec.get('lon')
            
            # Only include records with valid coordinates and species
            if species and lat is not None and lon is not None:
                try:
                    records.append({
                        'species_id': str(species),
                        'lat': float(lat),
                        'lon': float(lon)
                    })
                except (ValueError, TypeError):
                    logger.warning(f"Skipping record with invalid coordinates: {rec.get('id')}")
        
        total_fetched += len(records)
        logger.info(f"Fetched page {page}, total records so far: {total_fetched}")
        
        # Stop if we hit the limit
        if total_fetched >= limit:
            break
        
        page += 1
    
    if not records:
        raise RuntimeError("Failed to fetch any valid records from Xeno-Canto API.")
    
    logger.info(f"Successfully fetched {len(records)} records.")
    return records

def write_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """Write the fetched data to a CSV file."""
    if not data:
        raise ValueError("No data to write to CSV.")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = ['species_id', 'lat', 'lon']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Wrote {len(data)} records to {output_path}")

def fetch_xeno_canto_data_wrapper() -> None:
    """Main execution function for the task."""
    # Ensure output directory exists
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check if sample file already exists
    if os.path.exists(SAMPLE_FILE_PATH):
        logger.info(f"Found existing file: {SAMPLE_FILE_PATH}. Loading it instead of fetching.")
        # We still need to update the checksum and state file for the existing file
        hash_val = calculate_sha256(SAMPLE_FILE_PATH)
        update_checksums_file(SAMPLE_FILE_PATH, hash_val)
        update_state_file(STATE_FILE, SAMPLE_FILE_PATH, hash_val)
        logger.info("Updated checksums and state file for existing data.")
        return

    # Fetch real data
    logger.info("No existing sample file found. Fetching real data from Xeno-Canto API.")
    try:
        data = fetch_xeno_canto_data()
    except Exception as e:
        logger.critical(f"Failed to fetch real data: {e}")
        # Fail loudly as per requirements
        raise RuntimeError(f"Aborting: Could not fetch real data from Xeno-Canto API. Error: {e}")

    # Write to CSV
    write_to_csv(data, SAMPLE_FILE_PATH)
    
    # Calculate checksum
    hash_val = calculate_sha256(SAMPLE_FILE_PATH)
    logger.info(f"Calculated SHA256 for {SAMPLE_FILE_PATH}: {hash_val}")
    
    # Update checksums file
    update_checksums_file(SAMPLE_FILE_PATH, hash_val)
    
    # Update state file
    update_state_file(STATE_FILE, SAMPLE_FILE_PATH, hash_val)
    
    logger.info("Task completed successfully.")

def main():
    """Entry point."""
    logger.info("Starting Xeno-Canto data fetch task.")
    try:
        fetch_xeno_canto_data_wrapper()
    except Exception as e:
        logger.error(f"Task failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
