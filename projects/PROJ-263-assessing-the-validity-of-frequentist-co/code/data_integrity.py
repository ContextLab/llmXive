"""
Data Integrity Module for llmXive Project PROJ-263.

Implements checksum generation for raw data upon creation (Per Principle III).
Ensures data integrity by computing SHA-256 hashes of files in data/raw/
and storing them in data/processed/checksums.json.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# Import project configuration
from config import get_data_dir, get_output_dir, load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 checksum for a single file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without memory issues
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute hash for {file_path}: {e}")
        raise


def generate_checksums_for_raw_data() -> Dict[str, Any]:
    """
    Scan data/raw/ directory, compute SHA-256 checksums for all files,
    and return a structured record.

    Returns:
        Dictionary containing metadata and checksums for all raw data files.
    """
    raw_dir = get_data_dir() / "raw"
    processed_dir = get_data_dir() / "processed"

    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist. Nothing to checksum.")
        return {"status": "skipped", "reason": "raw_dir_missing", "files": []}

    if not processed_dir.exists():
        processed_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created processed directory: {processed_dir}")

    checksums_record: Dict[str, Any] = {
        "version": "1.0",
        "algorithm": "sha256",
        "generated_at": None,  # Will be set by caller if needed
        "source_directory": str(raw_dir),
        "files": []
    }

    file_count = 0
    for file_path in sorted(raw_dir.iterdir()):
        if file_path.is_file():
            file_checksum = compute_file_sha256(file_path)
            record_entry = {
                "filename": file_path.name,
                "relative_path": str(file_path.relative_to(raw_dir)),
                "size_bytes": file_path.stat().st_size,
                "checksum": file_checksum
            }
            checksums_record["files"].append(record_entry)
            file_count += 1
            logger.info(f"Checksummed: {file_path.name} -> {file_checksum[:16]}...")

    checksums_record["total_files"] = file_count
    return checksums_record


def save_checksums(checksums_record: Dict[str, Any], output_path: Optional[Path] = None) -> Path:
    """
    Save the checksums record to a JSON file.

    Args:
        checksums_record: The dictionary containing checksum data.
        output_path: Optional specific path to save to. Defaults to data/processed/checksums.json.

    Returns:
        Path to the saved file.
    """
    if output_path is None:
        output_path = get_data_dir() / "processed" / "checksums.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums_record, f, indent=2)

    logger.info(f"Checksums saved to: {output_path}")
    return output_path


def verify_checksums() -> bool:
    """
    Verify existing checksums against current files in data/raw/.

    Returns:
        True if all files match their recorded checksums, False otherwise.
    """
    checksums_path = get_data_dir() / "processed" / "checksums.json"

    if not checksums_path.exists():
        logger.warning(f"Checksum file {checksums_path} not found. Cannot verify.")
        return False

    with open(checksums_path, "r", encoding="utf-8") as f:
        record = json.load(f)

    if not record.get("files"):
        logger.warning("No files recorded in checksum file.")
        return False

    raw_dir = get_data_dir() / "raw"
    all_valid = True

    for file_entry in record["files"]:
        file_path = raw_dir / file_entry["relative_path"]
        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            all_valid = False
            continue

        current_hash = compute_file_sha256(file_path)
        recorded_hash = file_entry["checksum"]

        if current_hash != recorded_hash:
            logger.error(f"Checksum mismatch for {file_path.name}: "
                         f"expected {recorded_hash[:16]}..., got {current_hash[:16]}...")
            all_valid = False
        else:
            logger.debug(f"Verified: {file_path.name}")

    return all_valid


def main():
    """
    Entry point for generating checksums for raw data.
    """
    logger.info("Starting checksum generation for raw data...")
    record = generate_checksums_for_raw_data()
    
    if record.get("total_files", 0) > 0:
        output_path = save_checksums(record)
        logger.info(f"Successfully processed {record['total_files']} files.")
        logger.info(f"Output written to: {output_path}")
    else:
        logger.info("No files found to checksum.")
    
    return record


if __name__ == "__main__":
    main()
