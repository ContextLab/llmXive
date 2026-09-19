import json
import hashlib
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from fetcher import fetch_all_backends
from config import load_config

logger = logging.getLogger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_data_raw_dir() -> Path:
    """Ensure the data/raw directory exists."""
    data_raw = Path("data/raw")
    data_raw.mkdir(parents=True, exist_ok=True)
    return data_raw

def save_backend_snapshot(backend_name: str, properties: Dict[str, Any], timestamp: datetime) -> Path:
    """
    Save a raw JSON snapshot of backend properties.
    Returns the path to the saved file.
    """
    raw_dir = ensure_data_raw_dir()
    # Sanitize filename
    safe_name = backend_name.replace(" ", "_").replace("/", "_")
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp_str}.json"
    file_path = raw_dir / filename

    # Prepare payload with metadata
    payload = {
        "backend_name": backend_name,
        "fetched_at": timestamp.isoformat(),
        "properties": properties
    }

    with open(file_path, "w") as f:
        json.dump(payload, f, indent=2)

    checksum = compute_sha256(file_path)

    logger.info(f"Saved snapshot: {file_path} (SHA256: {checksum})")
    return file_path

def main():
    """
    Main entry point to fetch backend data and save raw JSON snapshots.
    """
    logger.info("Starting snapshot generation for all accessible backends.")
    config = load_config()
    
    # Fetch all backends using existing fetcher logic
    backends_data = fetch_all_backends()
    
    if not backends_data:
        logger.warning("No backends were fetched or processed.")
        return

    saved_count = 0
    for backend_name, properties in backends_data.items():
        if properties is None:
            logger.warning(f"Skipping {backend_name}: properties were None or invalid.")
            continue
        
        try:
            save_backend_snapshot(backend_name, properties, datetime.now())
            saved_count += 1
        except Exception as e:
            logger.error(f"Failed to save snapshot for {backend_name}: {e}")

    logger.info(f"Successfully saved {saved_count} raw JSON snapshots.")

if __name__ == "__main__":
    main()
