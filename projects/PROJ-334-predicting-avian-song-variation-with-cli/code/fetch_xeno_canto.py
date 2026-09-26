import os
import sys
import csv
import hashlib
import logging
import json
import requests
from pathlib import Path
from typing import Iterator, Dict, Any, List, Optional
from itertools import islice

# Import project utilities matching the API surface
from config import load_config, Config
from state_manager import compute_file_hash, load_state, save_state, register_artifact
from utils import setup_logging

# Constants
XCANTO_API_BASE = "https://xeno-canto.org/api/2/recordings"
XCANTO_QUERY_TEMPLATE = "?q={}&page={}"
XCANTO_LIMIT_PER_PAGE = 500  # Max allowed by API
MAX_PAGES = 1000  # Safety cap to prevent infinite loops
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "xeno_canto_metadata.csv"
CHECKSUMS_FILE = Path("data/checksums.txt")
STATE_FILE = Path("state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml")

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_checksums_file(file_path: Path, checksum: str) -> None:
    """Append or update the checksum in data/checksums.txt."""
    if not CHECKSUMS_FILE.exists():
        # Initialize with header
        with open(CHECKSUMS_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["filename", "hash"])
    
    # Read existing checksums
    existing = {}
    with open(CHECKSUMS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing[row["filename"]] = row["hash"]
    
    # Update or add
    filename = file_path.name
    existing[filename] = checksum
    
    # Write back
    with open(CHECKSUMS_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "hash"])
        writer.writeheader()
        for fname, h in existing.items():
            writer.writerow({"filename": fname, "hash": h})

def update_state_file(file_path: Path, checksum: str) -> None:
    """Update the project state file with the new artifact hash."""
    state = load_state(STATE_FILE)
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Use relative path from project root for the key
    rel_path = str(file_path.relative_to(Path(".")))
    state["artifact_hashes"][rel_path] = {
        "hash": checksum,
        "type": "raw_data",
        "source": "xeno-canto-api",
        "timestamp": "auto"  # Could be replaced with actual timestamp
    }
    
    save_state(STATE_FILE, state)

def fetch_page(page_num: int, species_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch a single page of recordings from Xeno-Canto API."""
    url = XCANTO_API_BASE
    params = {
        "page": page_num,
        "limit": XCANTO_LIMIT_PER_PAGE
    }
    if species_id:
        params["q"] = species_id
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("recordings", [])
    except requests.RequestException as e:
        logging.error(f"Failed to fetch page {page_num}: {e}")
        raise

def fetch_xeno_canto_data(species_id: Optional[str] = None) -> Iterator[Dict[str, Any]]:
    """
    Stream recordings from Xeno-Canto API.
    Yields dictionaries containing: species_id, lat, lon, and other metadata.
    Uses streaming approach to handle large datasets without loading all into memory.
    """
    page = 1
    total_processed = 0
    
    while page <= MAX_PAGES:
        try:
            records = fetch_page(page, species_id)
            if not records:
                logging.info(f"No more records found at page {page}. Stopping.")
                break
            
            for record in records:
                # Extract required fields: species_id, lat, lon
                # Xeno-Canto API returns 'sp' for species, 'lat'/'lon' for coordinates
                species = record.get("sp")
                lat = record.get("lat")
                lon = record.get("lon")
                
                # Skip records without valid coordinates
                if lat is None or lon is None:
                    continue
                
                # Validate coordinates
                try:
                    lat_val = float(lat)
                    lon_val = float(lon)
                    if not (-90 <= lat_val <= 90) or not (-180 <= lon_val <= 180):
                        continue
                except (ValueError, TypeError):
                    continue
                
                # Yield the cleaned record
                yield {
                    "species_id": species,
                    "lat": lat_val,
                    "lon": lon_val,
                    "rec_id": record.get("id"),
                    "file": record.get("file"),
                    "song_type": record.get("type"),
                    "country": record.get("cnt")
                }
                total_processed += 1
            
            # Check if we've received fewer records than the limit (last page)
            if len(records) < XCANTO_LIMIT_PER_PAGE:
                logging.info(f"Reached last page (page {page}) with {len(records)} records.")
                break
            
            page += 1
            
        except requests.RequestException as e:
            logging.error(f"Critical error fetching page {page}: {e}")
            raise

def write_to_csv(records: Iterator[Dict[str, Any]], output_file: Path) -> int:
    """
    Write streamed records to CSV file.
    Returns the number of records written.
    """
    fieldnames = ["species_id", "lat", "lon", "rec_id", "file", "song_type", "country"]
    count = 0
    
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in records:
            writer.writerow(record)
            count += 1
            
            # Log progress every 10,000 records
            if count % 10000 == 0:
                logging.info(f"Processed {count} records...")
    
    return count

def main():
    """Main entry point for fetching Xeno-Canto data."""
    # Setup logging
    logger = setup_logging("fetch_xeno_canto", level=logging.INFO)
    logger.info("Starting Xeno-Canto data fetch...")
    
    # Load configuration (optional species filter)
    try:
        config = load_config()
        species_filter = config.get("xeno_canto", {}).get("species_filter")
    except Exception as e:
        logger.warning(f"Could not load config for species filter: {e}")
        species_filter = None
    
    try:
        # Fetch and write data
        logger.info("Fetching data from Xeno-Canto API...")
        record_count = write_to_csv(
            fetch_xeno_canto_data(species_id=species_filter),
            OUTPUT_FILE
        )
        
        if record_count == 0:
            logger.error("No records were fetched. Aborting.")
            sys.exit(1)
        
        logger.info(f"Fetched {record_count} records successfully.")
        
        # Calculate checksum
        checksum = calculate_sha256(OUTPUT_FILE)
        logger.info(f"SHA256 checksum: {checksum}")
        
        # Update checksums file
        update_checksums_file(OUTPUT_FILE, checksum)
        logger.info(f"Updated checksums file: {CHECKSUMS_FILE}")
        
        # Update state file
        update_state_file(OUTPUT_FILE, checksum)
        logger.info(f"Updated state file: {STATE_FILE}")
        
        logger.info("Xeno-Canto data fetch completed successfully.")
        
    except Exception as e:
        logger.error(f"Critical error during fetch: {e}")
        # Abort on failure - do not create partial artifacts
        sys.exit(1)

if __name__ == "__main__":
    main()
