"""
Snapshot Saver Module for llmXive Project PROJ-163.

This module handles the persistence of raw calibration data from IBM Quantum
backends to the local file system. It ensures data integrity via SHA-256 hashing
and manages unique file naming for multiple snapshots of the same device.
"""

import json
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import config to handle environment variables and paths
from code.config import load_config
from code.logging_config import get_logger

logger = get_logger(__name__)

def ensure_data_raw_dir() -> Path:
    """Ensure the data/raw directory exists, creating it if necessary."""
    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)
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
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def save_backend_snapshot(
    device_id: str,
    backend_properties: Dict[str, Any],
    raw_dir: Optional[Path] = None,
) -> Path:
    """
    Save a raw JSON snapshot of backend properties to disk.

    The file is named {device_id}_{YYYYMMDD_HHMMSS}.json.
    If a file with the same name already exists (collision), a unique suffix
    (_1, _2, etc.) is appended before the extension.

    Args:
        device_id: The ID of the backend device.
        backend_properties: The raw dictionary of properties fetched from the API.
        raw_dir: Optional directory to save to. Defaults to 'data/raw'.

    Returns:
        The Path object of the saved file.

    Raises:
        ValueError: If backend_properties is empty or None (indicating a fetch failure).
        RuntimeError: If the data cannot be serialized to JSON.
    """
    if raw_dir is None:
        raw_dir = ensure_data_raw_dir()

    if not backend_properties or not isinstance(backend_properties, dict):
        # Fail loudly: do not save empty or invalid data
        raise ValueError(
            f"Cannot save snapshot for {device_id}: backend_properties is empty or invalid."
        )

    # Ensure the data contains the required schema fields for validation later
    if "device_id" not in backend_properties:
        backend_properties["device_id"] = device_id
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = f"{device_id}_{timestamp_str}.json"
    file_path = raw_dir / base_filename

    # Handle collision if the exact same second is hit (rare but possible)
    counter = 1
    while file_path.exists():
        new_filename = f"{device_id}_{timestamp_str}_{counter}.json"
        file_path = raw_dir / new_filename
        counter += 1

    try:
        # Serialize to JSON with indentation for readability
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(backend_properties, f, indent=2, default=str)
        
        logger.info(f"Saved snapshot to: {file_path}")
        return file_path

    except (TypeError, ValueError) as e:
        logger.error(f"Failed to serialize data for {device_id}: {e}")
        raise RuntimeError(f"Failed to save snapshot for {device_id}") from e

def main():
    """
    Entry point for saving raw snapshots.
    
    This function is invoked via `python code/fetcher.py --save-snapshots`
    (which delegates to this logic) or directly.
    
    It attempts to fetch backend properties for accessible devices and save them.
    If the IBMQ_TOKEN is missing, it raises an error rather than using mock data.
    """
    logger.info("Starting raw snapshot save process.")
    
    config = load_config()
    token = config.get("IBMQ_TOKEN")
    
    if not token:
        # Fail loudly if token is missing
        logger.error("IBMQ_TOKEN environment variable is missing. Cannot fetch real data.")
        raise EnvironmentError(
            "IBMQ_TOKEN is missing. Please set the environment variable to fetch real data. "
            "Mock data is not permitted."
        )

    # Import the fetcher logic here to avoid circular imports if needed,
    # though fetcher.py is the primary driver.
    # For this specific task, we assume the fetcher calls this function
    # or we provide a self-contained runner that uses the fetcher.
    
    # Since the task requires `python code/fetcher.py --save-snapshots` to work,
    # and fetcher.py imports this module, we implement the logic here
    # that fetcher.py would call.
    
    # We need to fetch the list of backends first.
    # We import from fetcher to keep the flow consistent with the API surface.
    from code.fetcher import fetch_backends_list, fetch_backend_properties, validate_data_freshness

    try:
        backends = fetch_backends_list()
        logger.info(f"Found {len(backends)} accessible backends.")
    except Exception as e:
        logger.error(f"Failed to retrieve backend list: {e}")
        raise

    saved_count = 0
    failed_count = 0

    for backend_name in backends:
        try:
            # Fetch properties
            props = fetch_backend_properties(backend_name)
            
            # Validate freshness
            if not validate_data_freshness(props):
                logger.warning(f"Skipping {backend_name}: data is stale (>30 days).")
                continue
            
            # Save snapshot
            file_path = save_backend_snapshot(backend_name, props)
            saved_count += 1
            
            # Update state file with hash (optional but good practice for hygiene)
            # This is typically handled by hygiene.py, but we can log the hash here
            file_hash = compute_sha256(file_path)
            logger.debug(f"Snapshot hash for {backend_name}: {file_hash}")

        except Exception as e:
            logger.error(f"Failed to process {backend_name}: {e}")
            failed_count += 1
            # Do not break; continue with other devices

    logger.info(f"Snapshot save complete. Saved: {saved_count}, Failed: {failed_count}")
    if failed_count > 0:
        logger.warning("Some snapshots failed to save. Check logs for details.")

    return saved_count, failed_count

if __name__ == "__main__":
    main()
