"""
Task T012f: Record computed SHA-256 checksum in data/raw/checksums.json.

This script computes the SHA-256 hash of the downloaded ADReSS dataset archive
(assumed to be present in data/raw/) and records the filename and hash in
data/raw/checksums.json.

Dependencies:
- code/config.py (for path resolution)
- code/ingestion.py (for compute_sha256 function)
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_path, ensure_dirs
from ingestion import compute_sha256
from utils import setup_logging, get_logger

def load_existing_checksums(checksums_path: Path) -> Dict[str, Any]:
    """Load existing checksums file if it exists, otherwise return empty dict."""
    if checksums_path.exists():
        with open(checksums_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"checksums": []}

def save_checksums(checksums_path: Path, data: Dict[str, Any]) -> None:
    """Save checksums to JSON file."""
    checksums_path.parent.mkdir(parents=True, exist_ok=True)
    with open(checksums_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def find_dataset_archive(raw_dir: Path) -> Optional[Path]:
    """
    Find the ADReSS dataset archive in data/raw/.
    Looks for .zip, .tar.gz, .tar, .tgz files.
    """
    if not raw_dir.exists():
        logging.warning(f"Raw data directory does not exist: {raw_dir}")
        return None

    # Look for common archive extensions
    archive_extensions = ['.zip', '.tar.gz', '.tar', '.tgz', '.7z']
    archives = []

    for ext in archive_extensions:
        matches = list(raw_dir.glob(f"*{ext}"))
        archives.extend(matches)

    if not archives:
        logging.warning(f"No dataset archive found in {raw_dir}")
        return None

    # If multiple archives, prefer the one with 'ADReSS' or 'adress' in name
    for archive in archives:
        if 'ADReSS' in archive.name or 'adress' in archive.name:
            return archive

    # Return the first one found
    return archives[0]

def main():
    """Main entry point for T012f."""
    setup_logging()
    logger = get_logger("T012f")

    # Get paths
    raw_dir = get_path("data_raw")
    checksums_path = get_path("data_raw_checksums")

    # Ensure directories exist
    ensure_dirs([raw_dir])

    logger.info("Starting T012f: Record SHA-256 checksum")

    # Find the dataset archive
    archive_path = find_dataset_archive(raw_dir)

    if archive_path is None:
        logger.error("No dataset archive found. Please run T012 first to download the data.")
        sys.exit(1)

    logger.info(f"Found dataset archive: {archive_path.name}")

    # Compute SHA-256 hash
    file_hash = compute_sha256(archive_path)
    logger.info(f"SHA-256 hash: {file_hash}")

    # Load existing checksums
    existing_data = load_existing_checksums(checksums_path)

    # Check if this file is already recorded
    updated = False
    for i, entry in enumerate(existing_data.get("checksums", [])):
        if entry.get("filename") == archive_path.name:
            existing_data["checksums"][i]["hash"] = file_hash
            existing_data["checksums"][i]["verified"] = True
            updated = True
            break

    if not updated:
        # Add new entry
        existing_data["checksums"].append({
            "filename": archive_path.name,
            "hash": file_hash,
            "verified": True
        })

    # Save checksums
    save_checksums(checksums_path, existing_data)
    logger.info(f"Checksums saved to {checksums_path}")

    # Log success
    logger.info("T012f completed successfully")
    print(f"Checksum recorded: {archive_path.name} -> {file_hash}")

if __name__ == "__main__":
    main()
