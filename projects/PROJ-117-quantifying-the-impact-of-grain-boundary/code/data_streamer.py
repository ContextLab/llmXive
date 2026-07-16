"""
Data Streamer Module for Large Grain Boundary Datasets.

This module implements file-level streaming to handle datasets exceeding 7GB RAM.
It downloads individual structure files (CIF/POSCAR) sequentially, verifies them
via SHA-256 checksum, and processes them in batches to stay within memory limits.
"""
import os
import sys
import json
import logging
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
import time

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils import compute_sha256, setup_logging

# Configure logging
logger = setup_logging("data_streamer")

# Configuration constants
MAX_FILE_SIZE_MB = 100  # Safety limit for single file download
BATCH_SIZE = 50  # Number of records to process in one batch
CHUNK_SIZE_BYTES = 8192  # Download chunk size
TIMEOUT_SECONDS = 60  # Request timeout

def download_file_streaming(url: str, dest_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Downloads a file from a URL in streaming chunks to avoid high memory usage.

    Args:
        url: The URL to download from.
        dest_path: Local path where the file will be saved.
        expected_hash: Optional SHA-256 hash to verify against.

    Returns:
        True if download and verification succeeded, False otherwise.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Downloading {url} to {dest_path}...")

    try:
        response = requests.get(url, stream=True, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE_BYTES):
                if chunk:
                    f.write(chunk)

        # Verify checksum if expected hash is provided
        if expected_hash:
            actual_hash = compute_sha256(dest_path)
            if actual_hash.lower() != expected_hash.lower():
                logger.error(f"Checksum mismatch for {dest_path}. Expected: {expected_hash}, Got: {actual_hash}")
                os.remove(dest_path)
                return False
            logger.info(f"Checksum verified for {dest_path}.")
        else:
            logger.warning(f"No expected hash provided for {dest_path}. Skipping verification.")

        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        if dest_path.exists():
            os.remove(dest_path)
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        if dest_path.exists():
            os.remove(dest_path)
        return False

def process_file_batch(file_batch: List[Dict[str, Any]], output_dir: Path) -> int:
    """
    Processes a batch of file records. This simulates the parsing step
    that would normally happen in geometry_parser.py but keeps memory low
    by processing one file at a time and discarding the structure object.

    Args:
        file_batch: List of dicts containing 'url', 'dest_filename', 'expected_hash', 'record_id'.
        output_dir: Directory to store raw files.

    Returns:
        Count of successfully processed records.
    """
    count = 0
    for record in file_batch:
        file_path = output_dir / record['dest_filename']
        if download_file_streaming(record['url'], file_path, record.get('expected_hash')):
            # Simulate parsing/processing logic here.
            # In a real scenario, this would call geometry_parser.parse_structure_file(file_path)
            # and append to a running dataframe, but we keep it lightweight here.
            logger.debug(f"Successfully processed {record['record_id']}")
            count += 1
        else:
            logger.error(f"Failed to process record {record['record_id']}")
    return count

def stream_data_source(
    source_manifest: str,
    raw_data_dir: Path,
    batch_size: int = BATCH_SIZE
) -> Dict[str, Any]:
    """
    Main streaming entry point. Reads a manifest of files, downloads them
    sequentially, and processes them in batches.

    Args:
        source_manifest: Path to a JSON file containing the list of records to fetch.
        raw_data_dir: Directory to save raw files.
        batch_size: Number of files to process in one batch.

    Returns:
        Dictionary with 'total_downloaded', 'total_processed', 'failed_count'.
    """
    if not source_manifest.exists():
        logger.error(f"Source manifest not found: {source_manifest}")
        return {'total_downloaded': 0, 'total_processed': 0, 'failed_count': 0}

    with open(source_manifest, 'r') as f:
        records = json.load(f)

    if not isinstance(records, list):
        logger.error("Manifest must be a list of records.")
        return {'total_downloaded': 0, 'total_processed': 0, 'failed_count': 0}

    logger.info(f"Starting streaming of {len(records)} records.")
    total_processed = 0
    failed_count = 0

    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} (size: {len(batch)})")
        
        batch_success = process_file_batch(batch, raw_data_dir)
        total_processed += batch_success
        failed_count += (len(batch) - batch_success)

        # Optional: Yield progress or perform intermediate cleanup
        # For now, we just log progress
        logger.info(f"Batch complete. Total processed: {total_processed}, Failed: {failed_count}")

    return {
        'total_downloaded': len(records),
        'total_processed': total_processed,
        'failed_count': failed_count
    }

def main():
    """
    Entry point for the data streamer script.
    Expects a manifest file path as an argument or uses a default.
    """
    if len(sys.argv) > 1:
        manifest_path = Path(sys.argv[1])
    else:
        manifest_path = PROJECT_ROOT / "data" / "raw_manifest.json"
    
    if not manifest_path.exists():
        logger.error(f"Manifest file not found at {manifest_path}. Please generate a manifest first.")
        sys.exit(1)

    raw_dir = PROJECT_ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Streaming data from {manifest_path} to {raw_dir}")
    result = stream_data_source(manifest_path, raw_dir)

    logger.info("Streaming complete.")
    logger.info(f"Results: {result}")

    # If the result indicates failure (e.g., 0 processed), we might want to exit with an error
    # depending on the downstream logic (T011 will handle the count check).
    if result['total_processed'] == 0:
        logger.error("No records were successfully processed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
