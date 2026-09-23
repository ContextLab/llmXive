"""
Module to save raw IBM Quantum backend calibration snapshots to disk.

Handles file naming, directory creation, JSON serialization, and SHA-256 hashing
for data integrity verification against the project state file.
"""
import json
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from config import load_config

logger = logging.getLogger(__name__)

def ensure_data_raw_dir() -> Path:
    """Ensure the data/raw directory exists, creating it if necessary."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {raw_dir}")
    return raw_dir

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_backend_snapshot(
    device_id: str,
    properties_data: Dict[str, Any],
    raw_dir: Optional[Path] = None
) -> Path:
    """
    Save a raw backend properties snapshot to disk.
    
    Args:
        device_id: The IBM Quantum device identifier (e.g., 'ibmq_manila').
        properties_data: The raw JSON data fetched from the API.
        raw_dir: Optional override for the raw data directory. Defaults to 'data/raw'.
        
    Returns:
        Path to the saved JSON file.
        
    Raises:
        ValueError: If properties_data is None or empty.
        IOError: If the file cannot be written.
    """
    if not properties_data:
        raise ValueError(f"Cannot save empty snapshot for device {device_id}")

    if raw_dir is None:
        raw_dir = ensure_data_raw_dir()

    # Generate timestamped filename: {device_id}_{YYYYMMDD_HHMMSS}.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{device_id}_{timestamp}.json"
    file_path = raw_dir / filename

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(properties_data, f, indent=2, default=str)
        logger.info(f"Saved raw snapshot to {file_path}")
    except IOError as e:
        logger.error(f"Failed to write snapshot for {device_id}: {e}")
        raise

    return file_path

def main():
    """
    Main entry point for the snapshot saver script.
    
    This script attempts to:
    1. Load configuration (checks for IBMQ_TOKEN).
    2. If token exists, fetches a sample backend (e.g., 'ibmq_manila') using fetcher logic.
       (Note: Since fetcher.py is not imported here to avoid circular deps, we simulate
       the fetch logic or import specifically if needed. However, the task requires
       using the fixture if token is missing. We will implement the logic to fetch
       from the fixture if no token, or attempt a real fetch if token exists.)
    3. Save the raw JSON to data/raw/.
    4. Compute SHA-256 and log it.
    
    For the purpose of this specific task implementation (T016), we assume the
    fetch logic is handled by the caller or we invoke the fetcher module directly.
    To make this script runnable as a standalone artifact for T016 verification:
    - If IBMQ_TOKEN is set: attempts to fetch 'ibmq_manila' (or first available) via fetcher.
    - If IBMQ_TOKEN is NOT set: loads the mock fixture from tests/fixtures/mock_backend_properties.json
      and saves it as if it were a real snapshot.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = load_config()
    raw_dir = ensure_data_raw_dir()

    # Determine data source
    if config.ibmq_token:
        logger.info("IBMQ_TOKEN found. Attempting to fetch real data...")
        try:
            # Import fetcher here to avoid circular imports if main.py imports this
            from fetcher import fetch_backend_properties
            device_id = "ibmq_manila" # Default target for verification
            logger.info(f"Fetching properties for {device_id}...")
            properties_data = fetch_backend_properties(device_id)
            
            if properties_data is None:
                logger.warning(f"Failed to fetch {device_id}. Exiting.")
                return
            
            saved_path = save_backend_snapshot(device_id, properties_data, raw_dir)
            sha_hash = compute_sha256(saved_path)
            logger.info(f"Success. File: {saved_path}, SHA256: {sha_hash}")
            
        except Exception as e:
            logger.error(f"Error during real fetch: {e}")
            raise
    else:
        logger.info("IBMQ_TOKEN not found. Using mock fixture (T006b) as per spec.")
        fixture_path = Path("tests/fixtures/mock_backend_properties.json")
        if not fixture_path.exists():
            raise FileNotFoundError(f"Mock fixture not found at {fixture_path}. Please run T006b first.")
        
        with open(fixture_path, "r", encoding="utf-8") as f:
            mock_data = json.load(f)
        
        # Treat mock data as if it came from a device named 'mock_device'
        # Or extract device_id from mock if available, otherwise use a generic name
        mock_device_id = mock_data.get("backend_name", "mock_device")
        saved_path = save_backend_snapshot(mock_device_id, mock_data, raw_dir)
        sha_hash = compute_sha256(saved_path)
        logger.info(f"Saved mock snapshot. File: {saved_path}, SHA256: {sha_hash}")

if __name__ == "__main__":
    main()
