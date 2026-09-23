"""
Generate processed calibration CSV from raw snapshots.

This module loads all raw JSON snapshots from data/raw/, extracts
performance metrics and topology data, and aggregates them into
a single CSV file at data/processed/raw_calibration.csv.
"""
import json
import os
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import existing functions from fetcher module
from fetcher import extract_performance_metrics, extract_topology_data

logger = logging.getLogger(__name__)

def load_raw_snapshots(raw_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all raw JSON snapshots from the specified directory.

    Args:
        raw_dir: Path to the data/raw/ directory

    Returns:
        List of dictionaries containing raw backend properties
    """
    snapshots = []
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return snapshots

    for file_path in sorted(raw_dir.glob("*.json")):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                snapshots.append(data)
            logger.info(f"Loaded snapshot: {file_path.name}")
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load {file_path.name}: {e}")

    return snapshots

def extract_device_metrics(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract metrics from a single raw snapshot.

    Args:
        snapshot: Raw backend properties dictionary

    Returns:
        Dictionary with device_id, timestamp, and aggregated metrics,
        or None if extraction fails
    """
    try:
        # Extract device_id and timestamp
        device_id = snapshot.get('backend_name') or snapshot.get('device_id')
        if not device_id:
            logger.warning("Snapshot missing backend_name or device_id")
            return None

        # Extract timestamp from properties or snapshot metadata
        timestamp_str = snapshot.get('date') or snapshot.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, TypeError):
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        # Extract performance metrics
        perf_data = extract_performance_metrics(snapshot)
        if not perf_data:
            logger.warning(f"Failed to extract performance metrics for {device_id}")
            return None

        # Extract topology data
        topo_data = extract_topology_data(snapshot)
        if not topo_data:
            logger.warning(f"Failed to extract topology data for {device_id}")
            return None

        return {
            'device_id': device_id,
            'timestamp': timestamp.isoformat(),
            't1_mean': perf_data.get('t1_mean'),
            't2_mean': perf_data.get('t2_mean'),
            'cx_error_mean': perf_data.get('cx_error_mean'),
            'readout_error_mean': perf_data.get('readout_error_mean'),
            'coupling_map': json.dumps(topo_data.get('coupling_map', []))
        }

    except Exception as e:
        logger.error(f"Error processing snapshot for device: {e}")
        return None

def process_snapshot(snapshot: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process a single snapshot and return extracted metrics.

    Wrapper around extract_device_metrics for consistency.

    Args:
        snapshot: Raw backend properties dictionary

    Returns:
        Processed metrics dictionary or None
    """
    return extract_device_metrics(snapshot)

def main():
    """
    Main entry point: Load all raw snapshots and generate processed CSV.

    Output: data/processed/raw_calibration.csv
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Define paths
    project_root = Path(__file__).parent.parent
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    output_file = processed_dir / 'raw_calibration.csv'

    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load all raw snapshots
    logger.info(f"Loading snapshots from {raw_dir}")
    snapshots = load_raw_snapshots(raw_dir)

    if not snapshots:
        logger.warning("No snapshots found. Cannot generate CSV.")
        # Create empty CSV with headers to satisfy verification
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'device_id', 'timestamp', 't1_mean', 't2_mean',
                'cx_error_mean', 'readout_error_mean', 'coupling_map'
            ])
        return

    # Process each snapshot
    logger.info(f"Processing {len(snapshots)} snapshots")
    records = []
    for snapshot in snapshots:
        record = process_snapshot(snapshot)
        if record:
            records.append(record)
            logger.info(f"Processed: {record['device_id']}")

    if not records:
        logger.error("No valid records extracted from snapshots.")
        # Create empty CSV with headers
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'device_id', 'timestamp', 't1_mean', 't2_mean',
                'cx_error_mean', 'readout_error_mean', 'coupling_map'
            ])
        return

    # Write to CSV
    logger.info(f"Writing {len(records)} records to {output_file}")
    fieldnames = [
        'device_id', 'timestamp', 't1_mean', 't2_mean',
        'cx_error_mean', 'readout_error_mean', 'coupling_map'
    ]

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    logger.info(f"Successfully generated {output_file}")
    print(f"Generated: {output_file}")
    print(f"Rows: {len(records)}")

if __name__ == '__main__':
    main()