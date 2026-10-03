import os
import sys
import csv
import logging
import math
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Importing from local project modules as per API surface
# Note: These imports assume the script is run from the code/ directory or added to sys.path
try:
    from utils import update_state_file, compute_file_hash
except ImportError:
    # Fallback for direct execution context if utils is not importable as a module
    # In a real pipeline, this would be handled by the runner setting up the path
    pass

# Configuration loading (assuming config.py is in the same directory)
try:
    from config import load_config, Config
except ImportError:
    load_config = None
    Config = None

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {filepath}")

def update_checksums_file(filepath: str, checksums_path: str, logger: logging.Logger):
    """Append the checksum of a file to the checksums CSV."""
    try:
        with open(checksums_path, 'r', newline='') as f:
            reader = list(csv.reader(f))
            if not reader or reader[0] != ['filename', 'sha256_hash']:
                reader = [['filename', 'sha256_hash']] + reader

        filename = os.path.basename(filepath)
        hash_val = calculate_sha256(filepath)

        # Check if already exists
        exists = False
        new_rows = [reader[0]]
        for row in reader[1:]:
            if row[0] == filename:
                new_rows.append([filename, hash_val])
                exists = True
            else:
                new_rows.append(row)
        
        if not exists:
            new_rows.append([filename, hash_val])

        with open(checksums_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(new_rows)
        
        logger.info(f"Updated checksums file: {filename} -> {hash_val}")
    except Exception as e:
        logger.error(f"Failed to update checksums file: {e}")
        raise

def load_song_records(filepath: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """Load song records from a processed CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Song records file not found: {filepath}")
    
    records = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Ensure numeric conversion for coordinates
            try:
                row['lat'] = float(row['lat'])
                row['lon'] = float(row['lon'])
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping row due to invalid coordinates: {e}")
                continue
            records.append(row)
    return records

def load_climate_snapshots(filepath: str, logger: logging.Logger) -> List[Dict[str, Any]]:
    """Load climate snapshots from a processed CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Climate snapshots file not found: {filepath}")
    
    records = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row['lat'] = float(row['lat'])
                row['lon'] = float(row['lon'])
                row['temperature'] = float(row.get('temperature', 0.0))
                row['precipitation'] = float(row.get('precipitation', 0.0))
                row['elevation'] = float(row.get('elevation', 0.0))
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping climate row due to invalid data: {e}")
                continue
            records.append(row)
    return records

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points on earth (in km)."""
    R = 6371.0  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def perform_spatial_join(song_records: List[Dict], climate_snapshots: List[Dict], 
                         join_radius_km: float, logger: logging.Logger) -> List[Dict]:
    """Perform spatial join by finding climate points within radius for each song record."""
    joined_records = []
    excluded_ids = []
    
    logger.info(f"Starting spatial join with radius: {join_radius_km} km")
    logger.info(f"Song records: {len(song_records)}, Climate points: {len(climate_snapshots)}")

    for song in song_records:
        matched_climate = None
        min_dist = float('inf')
        
        # Naive O(N*M) join for simplicity; production might use KDTree or RTree
        # Given the context of "sample" data, this is acceptable.
        for climate in climate_snapshots:
            dist = haversine_distance(
                song['lat'], song['lon'],
                climate['lat'], climate['lon']
            )
            if dist <= join_radius_km and dist < min_dist:
                min_dist = dist
                matched_climate = climate

        if matched_climate:
            merged = {**song, **matched_climate}
            merged['distance_to_climate_km'] = min_dist
            joined_records.append(merged)
        else:
            excluded_ids.append(song.get('species_id', 'unknown'))
      
    return joined_records, excluded_ids

def verify_no_duplicates(records: List[Dict], logger: logging.Logger) -> bool:
    """Verify no duplicate rows based on primary keys."""
    seen = set()
    duplicates = 0
    # Assuming species_id + lat + lon + song_metric_1 + song_metric_2 is unique enough
    # or just species_id + lat + lon for this specific dataset context
    for record in records:
        key = (record.get('species_id'), record.get('lat'), record.get('lon'))
        if key in seen:
            duplicates += 1
            logger.warning(f"Duplicate found: {key}")
        else:
            seen.add(key)
    
    if duplicates > 0:
        logger.error(f"Found {duplicates} duplicate records.")
        return False
    return True

def calculate_match_rate(total: int, matched: int, logger: logging.Logger):
    """Calculate and log match rate."""
    if total == 0:
        rate = 0.0
    else:
        rate = matched / total
    logger.info(f"Match Rate: {matched}/{total} ({rate:.2%})")
    return rate

def save_processed_data(records: List[Dict], output_path: str, logger: logging.Logger):
    """Save the unified analysis dataset to CSV."""
    if not records:
        logger.warning("No records to save.")
        return

    if not os.path.exists(os.dirname(output_path)):
        os.makedirs(os.dirname(output_path))

    with open(output_path, 'w', newline='') as f:
        if records:
            fieldnames = list(records[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
    logger.info(f"Saved {len(records)} records to {output_path}")

def log_excluded_species(excluded_ids: List[str], output_path: str, logger: logging.Logger):
    """Log excluded species to a JSON file."""
    if not os.path.exists(os.dirname(output_path)):
        os.makedirs(os.dirname(output_path))
    
    data = {
        "excluded_ids": excluded_ids,
        "count": len(excluded_ids),
        "reason": "No climate data found within join radius"
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Logged {len(excluded_ids)} excluded species to {output_path}")

def main():
    logger = setup_logging()
    
    # Load configuration
    config = None
    if load_config:
        config = load_config()
    join_radius_km = config.get('join_radius_km', 10.0) if config else 10.0
    
    # Paths
    song_path = "data/raw/xeno_canto_sample.csv"
    climate_path = "data/raw/worldclim_sample.csv"
    output_path = "data/processed/analysis_dataset.csv"
    excluded_log_path = "data/logs/excluded_species.json"
    checksums_path = "data/checksums.txt"
    state_file_path = "state/projects/PROJ-334-predicting-avian-song-variation-with-cli.yaml"
    
    # Load Data
    logger.info("Loading song records...")
    song_records = load_song_records(song_path, logger)
    
    logger.info("Loading climate snapshots...")
    climate_snapshots = load_climate_snapshots(climate_path, logger)
    
    # Perform Spatial Join
    joined_records, excluded_ids = perform_spatial_join(
        song_records, climate_snapshots, join_radius_km, logger
    )
    
    # Calculate Match Rate
    total_song = len(song_records)
    matched = len(joined_records)
    calculate_match_rate(total_song, matched, logger)
    
    # Verify No Duplicates
    if not verify_no_duplicates(joined_records, logger):
        logger.warning("Duplicates detected. Proceeding with saved data but check logs.")
    
    # Log Excluded Species
    log_excluded_species(excluded_ids, excluded_log_path, logger)
    
    # Save Processed Data
    save_processed_data(joined_records, output_path, logger)
    
    # Update Checksums
    update_checksums_file(output_path, checksums_path, logger)
    
    # Update State File
    if os.path.exists(state_file_path):
        try:
            update_state_file(state_file_path, output_path, logger)
            logger.info("State file updated successfully.")
        except Exception as e:
            logger.error(f"Failed to update state file: {e}")
    else:
        logger.warning(f"State file not found at {state_file_path}. Skipping update.")

    logger.info("Ingestion pipeline T017 completed.")

if __name__ == "__main__":
    main()