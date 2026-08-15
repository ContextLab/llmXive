"""
Snapshot Saver for IBM Quantum Calibration Data (Task T016)

This module implements the logic to save raw JSON snapshots of backend properties
to the data/raw/ directory. It ensures each snapshot includes:
1. A timestamp in the filename.
2. A SHA256 checksum of the content for integrity verification.
3. Metadata regarding the source and timestamp of the fetch.
"""
import json
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from logger import setup_logger

# Ensure logger is configured
logger = setup_logger(__name__)

DATA_RAW_DIR = Path("data/raw")

def compute_sha256(content: str) -> str:
    """Compute SHA256 hash of a string content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def ensure_data_raw_dir() -> Path:
    """Ensure the data/raw directory exists, creating it if necessary."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_RAW_DIR

def save_backend_snapshot(
    device_id: str,
    properties: Dict[str, Any],
    fetch_timestamp: Optional[datetime] = None
) -> str:
    """
    Save a raw JSON snapshot of backend properties to data/raw/.

    The filename format is: {device_id}_{timestamp}.json
    A corresponding checksum file {device_id}_{timestamp}.sha256 is also created.

    Args:
        device_id: The ID of the backend (e.g., 'ibmq_manila').
        properties: The raw dictionary of backend properties.
        fetch_timestamp: Optional datetime. If None, current time is used.

    Returns:
        The path to the saved JSON file.

    Raises:
        ValueError: If properties is empty or invalid.
        IOError: If writing to disk fails.
    """
    if not properties:
        raise ValueError(f"Cannot save snapshot for {device_id}: properties dictionary is empty.")

    if fetch_timestamp is None:
        fetch_timestamp = datetime.utcnow()

    # Format timestamp for filename (ISO 8601 basic, safe for filenames)
    timestamp_str = fetch_timestamp.strftime("%Y%m%d_%H%M%S_%f")
    
    # Ensure directory exists
    base_dir = ensure_data_raw_dir()

    # Construct filenames
    json_filename = f"{device_id}_{timestamp_str}.json"
    checksum_filename = f"{device_id}_{timestamp_str}.sha256"
    
    json_path = base_dir / json_filename
    checksum_path = base_dir / checksum_filename

    # Prepare content with metadata
    snapshot_data = {
        "device_id": device_id,
        "fetched_at_utc": fetch_timestamp.isoformat(),
        "data": properties
    }

    # Serialize to JSON with indentation for readability
    json_content = json.dumps(snapshot_data, indent=2, default=str)
    
    # Compute checksum
    content_hash = compute_sha256(json_content)

    try:
        # Write JSON
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_content)
        
        # Write checksum
        with open(checksum_path, 'w', encoding='utf-8') as f:
            f.write(f"{content_hash}  {json_filename}\n")
        
        logger.info(f"Saved raw snapshot for {device_id} to {json_path} (SHA256: {content_hash[:16]}...)")
        return str(json_path)

    except IOError as e:
        logger.error(f"Failed to write snapshot for {device_id}: {e}")
        raise

def main():
    """
    Entry point for the snapshot saver.
    
    This function is intended to be called by the main pipeline after 
    fetching backend properties. It iterates through a list of valid 
    devices and saves their raw data.
    
    For demonstration purposes in this standalone script, it logs 
    what it would do if called with data. In the real pipeline, 
    fetcher.py will call save_backend_snapshot directly.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Snapshot Saver Module Loaded. Ready to save raw calibration data.")
    
    # Example usage (commented out to prevent accidental execution without data):
    # sample_props = {"backend_name": "test", "qubits": []}
    # save_backend_snapshot("test_device", sample_props)

if __name__ == "__main__":
    main()
