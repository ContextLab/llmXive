"""
Module to generate the performance metrics CSV from raw calibration snapshots.
This implements Task T017a: Generate Performance Metrics CSV.
"""
import json
import os
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from existing project modules
from fetcher import extract_performance_metrics, extract_chip_family

logger = logging.getLogger(__name__)

DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
OUTPUT_FILE = DATA_PROCESSED_DIR / "performance_metrics.csv"

def load_raw_snapshots() -> List[Dict[str, Any]]:
    """
    Load all raw JSON snapshots from data/raw directory.
    Returns a list of dictionaries containing device_id, timestamp, and backend properties.
    """
    if not DATA_RAW_DIR.exists():
        logger.warning(f"Directory {DATA_RAW_DIR} does not exist. No snapshots to load.")
        return []

    snapshots = []
    for file_path in DATA_RAW_DIR.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Ensure we have the required fields
                if 'device_id' in data and 'timestamp' in data and 'properties' in data:
                    snapshots.append(data)
                else:
                    logger.warning(f"Skipping {file_path}: missing required fields.")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {file_path}: {e}")
    
    return snapshots

def extract_device_metrics(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract performance metrics and chip family from a raw snapshot.
    Returns a dictionary with device_id, timestamp, t1_mean, t2_mean, 
    cx_error_mean, readout_error_mean, chip_family.
    """
    device_id = snapshot.get('device_id')
    timestamp = snapshot.get('timestamp')
    properties = snapshot.get('properties', {})

    if not device_id or not timestamp:
        logger.warning(f"Skipping snapshot: missing device_id or timestamp.")
        return None

    # Extract performance metrics using existing fetcher logic
    metrics = extract_performance_metrics(properties)
    
    if not metrics:
        logger.warning(f"No performance metrics extracted for {device_id}.")
        return None

    # Extract chip family using existing fetcher logic
    chip_family = extract_chip_family(device_id)

    return {
        'device_id': device_id,
        'timestamp': timestamp,
        't1_mean': metrics.get('t1_mean', 0.0),
        't2_mean': metrics.get('t2_mean', 0.0),
        'cx_error_mean': metrics.get('cx_error_mean', 0.0),
        'readout_error_mean': metrics.get('readout_error_mean', 0.0),
        'chip_family': chip_family
    }

def process_snapshot(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single snapshot and return the performance metrics record.
    """
    return extract_device_metrics(snapshot)

def main():
    """
    Main entry point to generate the performance metrics CSV.
    Reads all raw snapshots, extracts metrics, and writes to CSV.
    """
    # Ensure output directory exists
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Load all raw snapshots
    snapshots = load_raw_snapshots()
    if not snapshots:
        logger.error("No raw snapshots found in data/raw/. Aborting.")
        # Create an empty CSV with headers to satisfy schema validation
        with open(OUTPUT_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'device_id', 'timestamp', 't1_mean', 't2_mean', 
                'cx_error_mean', 'readout_error_mean', 'chip_family'
            ])
            writer.writeheader()
        return

    logger.info(f"Processing {len(snapshots)} raw snapshots...")

    records = []
    for snapshot in snapshots:
        record = process_snapshot(snapshot)
        if record:
            records.append(record)

    if not records:
        logger.error("No valid records extracted. Aborting.")
        return

    # Sort by device_id for consistent output
    records.sort(key=lambda x: x['device_id'])

    # Write to CSV
    fieldnames = [
        'device_id', 'timestamp', 't1_mean', 't2_mean', 
        'cx_error_mean', 'readout_error_mean', 'chip_family'
    ]

    with open(OUTPUT_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Successfully wrote {len(records)} records to {OUTPUT_FILE}")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
