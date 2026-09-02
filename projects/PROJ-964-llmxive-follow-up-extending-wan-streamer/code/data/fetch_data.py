"""
Canonical entry point for data acquisition.
Wraps logic from T009 (validate_logs) and T040 (Strict Data Fetch Failure).
Invoked by quickstart.md.

Logic:
1. Check for Wan-Streamer v0.1 logs.
2. If missing, fetch the canonical VoxCeleb2 dataset (T040).
3. Fail loudly if neither source is available (no synthetic fallback).
4. Update state.yaml with the dataset hash and source.
"""
import os
import sys
import argparse
import logging
import hashlib
import json
from pathlib import Path
from typing import Optional

# Import existing logic from T009 (validate_logs) and T040 (Strict Data Fetch Failure)
# T009: validate_logs.py
from data.validate_logs import (
    check_logs_exist,
    fetch_voxceleb2_dataset,
    update_state_with_dataset,
    main as validate_logs_main
)
# T040: Strict Data Fetch Failure logic is embedded in fetch_voxceleb2_dataset
# and the flow control here.

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_checksum(file_path: str) -> str:
    """
    Compute MD5 checksum of a file or directory.
    For directories, we hash the sorted list of files and their individual hashes.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {file_path}")

    if path.is_file():
        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    else:
        # For directories, we create a deterministic hash based on file contents
        hash_md5 = hashlib.md5()
        files = sorted([str(p.relative_to(path)) for p in path.rglob('*') if p.is_file()])
        for rel_path in files:
            full_path = path / rel_path
            # Hash the relative path first to include structure
            hash_md5.update(rel_path.encode('utf-8'))
            # Then hash the content
            with open(full_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        return hash_md5.hexdigest()

def main():
    """
    Main entry point for fetching data.
    Orchestrates the check for logs -> fetch VoxCeleb2 -> update state flow.
    """
    parser = argparse.ArgumentParser(description="Fetch data for llmXive pipeline.")
    parser.add_argument(
        '--force-fetch',
        action='store_true',
        help='Force fetching VoxCeleb2 even if Wan-Streamer logs exist.'
    )
    args = parser.parse_args()

    logger.info("Starting data fetch process...")

    # 1. Check for Wan-Streamer v0.1 logs
    logs_path = Path("data/raw/wan-streamer-logs")
    wan_streamer_exists = check_logs_exist()

    source: Optional[str] = None
    data_path: Optional[Path] = None

    if wan_streamer_exists and not args.force_fetch:
        logger.info("Wan-Streamer v0.1 logs found. Using existing logs.")
        source = "wan-streamer"
        data_path = logs_path
    else:
        if wan_streamer_exists:
            logger.info("Wan-Streamer logs found but --force-fetch requested. Fetching VoxCeleb2.")
        
        logger.info("Wan-Streamer logs not found or forced. Attempting to fetch VoxCeleb2...")
        
        try:
            # This function implements T040: Strict Data Fetch Failure
            # It will raise an error if the fetch fails or if no real source is found.
            # It does NOT fall back to synthetic data.
            fetched_path = fetch_voxceleb2_dataset()
            data_path = Path(fetched_path)
            source = "voxceleb2"
            logger.info(f"VoxCeleb2 dataset fetched successfully to: {data_path}")
        except Exception as e:
            logger.error(f"CRITICAL: Failed to fetch data. No real source available. Error: {e}")
            logger.error("Aborting. Do not fabricate data.")
            sys.exit(1)

    if source is None:
        logger.error("CRITICAL: Could not determine data source.")
        sys.exit(1)

    # 2. Update state.yaml with the checksum and source
    if data_path:
        logger.info(f"Updating state.yaml for source: {source} at {data_path}")
        try:
            # Ensure the path is a string for the utility functions
            checksum = compute_checksum(str(data_path))
            update_state_with_dataset(str(data_path), checksum, source)
            logger.info("State updated successfully.")
        except Exception as e:
            logger.error(f"Failed to update state.yaml: {e}")
            sys.exit(1)
    else:
        logger.error("CRITICAL: Data path is None after source determination.")
        sys.exit(1)

    logger.info("Data fetch process completed successfully.")

if __name__ == "__main__":
    main()