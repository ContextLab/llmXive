"""
T017: Generate structured CSV data/processed/raw_calibration.csv containing all valid device metrics.

This script aggregates the performance metrics extracted by T015a and T015b
from the raw JSON snapshots saved by T016, and writes them to a single CSV file.

It relies on the existing API surface in code/fetcher.py for data extraction
and code/snapshot_saver.py for locating raw data.
"""
import json
import os
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from existing API surface
from fetcher import extract_performance_metrics, validate_data_freshness
from snapshot_saver import ensure_data_raw_dir

logger = logging.getLogger(__name__)

def load_raw_snapshots(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all raw JSON calibration snapshots from the data/raw directory.
    
    Args:
        raw_dir: Path to the directory containing raw JSON files.
    
    Returns:
        List of dictionaries containing the raw JSON content.
    """
    snapshots = []
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist. No data to process.")
        return snapshots

    for file_path in raw_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Store metadata about the source file for traceability
                data['_source_file'] = file_path.name
                data['_source_path'] = str(file_path)
                snapshots.append(data)
                logger.info(f"Loaded snapshot: {file_path.name}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to parse {file_path}: {e}")
    return snapshots

def extract_device_metrics(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract performance metrics from a single raw snapshot.
    
    Uses the existing extract_performance_metrics logic from fetcher.py.
    
    Args:
        snapshot: Raw JSON data for a backend.
    
    Returns:
        Dictionary of extracted metrics, or None if the device is invalid/expired.
    """
    try:
        # Extract metrics using the established API
        metrics = extract_performance_metrics(snapshot)
        if not metrics:
            return None

        # Validate freshness (though T016 should have filtered this, we double-check)
        if 'last_update' in metrics:
            if not validate_data_freshness(metrics['last_update']):
                logger.warning(f"Device {metrics.get('device_id', 'unknown')} data too old, excluding.")
                return None

        return metrics
    except Exception as e:
        logger.error(f"Failed to extract metrics from snapshot {snapshot.get('_source_file', 'unknown')}: {e}")
        return None

def process_snapshot(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single snapshot to extract metrics and format for CSV.
    
    Args:
        snapshot: Raw JSON data.
    
    Returns:
        Formatted row dictionary, or None.
    """
    metrics = extract_device_metrics(snapshot)
    if not metrics:
        return None

    # Ensure all required columns are present, filling with None if missing
    row = {
        'device_id': metrics.get('device_id'),
        'timestamp': metrics.get('last_update'),
        'qubit_count': metrics.get('qubit_count'),
        'mean_t1': metrics.get('mean_t1'),
        'mean_t2': metrics.get('mean_t2'),
        'mean_cx_error': metrics.get('mean_cx_error'),
        'mean_readout_error': metrics.get('mean_readout_error'),
        'coupling_map_size': metrics.get('coupling_map_size'),
        'source_file': metrics.get('_source_file')
    }
    return row

def main():
    """
    Main entry point for T017.
    
    Reads all raw JSON snapshots, extracts metrics, and writes a consolidated CSV.
    """
    logging.basicConfig(level=logging.INFO)
    
    raw_dir = Path("data/raw")
    output_path = Path("data/processed/raw_calibration.csv")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading raw snapshots...")
    snapshots = load_raw_snapshots(raw_dir)
    
    if not snapshots:
        logger.error("No raw snapshots found. Ensure T016 has been run.")
        return

    logger.info(f"Processing {len(snapshots)} snapshots...")
    rows = []
    for snap in snapshots:
        row = process_snapshot(snap)
        if row:
            rows.append(row)
    
    if not rows:
        logger.warning("No valid rows extracted. Check logs for errors.")
        return

    logger.info(f"Writing {len(rows)} rows to {output_path}...")
    
    # Define consistent column order
    columns = [
        'device_id', 'timestamp', 'qubit_count', 'mean_t1', 'mean_t2',
        'mean_cx_error', 'mean_readout_error', 'coupling_map_size', 'source_file'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    
    logger.info(f"Successfully generated {output_path}")

if __name__ == "__main__":
    main()