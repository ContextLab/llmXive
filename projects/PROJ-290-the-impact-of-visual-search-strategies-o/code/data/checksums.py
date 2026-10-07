"""
Data Checksums Module.

Provides utilities to generate SHA-256 hashes for artifacts in the data directory.
Implements the Constitution Principle V for data integrity tracking.
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

from config import get_config
from utils.logging import get_logger


def get_logger_wrapper(name: str):
    """Helper to get a logger with a specific name."""
    return get_logger(name)


def ensure_raw_directory(raw_data_path: str | Path) -> Path:
    """
    Ensures the raw data directory exists. Creates it if missing.

    Args:
        raw_data_path: Path to the raw data directory.

    Returns:
        The Path object for the raw data directory.
    """
    raw_path = Path(raw_data_path)
    if not raw_path.exists():
        logging.info(f"Creating raw data directory: {raw_path}")
        raw_path.mkdir(parents=True, exist_ok=True)
    return raw_path


def calculate_sha256(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logging.error(f"Failed to hash file {file_path}: {e}")
        raise


def scan_and_hash_directory(directory_path: str | Path) -> List[Dict[str, Any]]:
    """
    Scans a directory recursively for files and calculates their SHA-256 hashes.

    Args:
        directory_path: Path to the directory to scan.

    Returns:
        A list of dictionaries containing file path (relative) and hash.
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        logging.warning(f"Directory does not exist: {dir_path}. Returning empty list.")
        return []

    checksums = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            file_path = Path(root) / file
            # Calculate relative path from the directory root
            relative_path = file_path.relative_to(dir_path)
            
            try:
                file_hash = calculate_sha256(file_path)
                checksums.append({
                    "file": str(relative_path),
                    "sha256": file_hash,
                    "size_bytes": file_path.stat().st_size
                })
            except Exception as e:
                logging.error(f"Skipping file {file_path} due to error: {e}")
    
    return checksums


def save_checksums(checksums: List[Dict[str, Any]], output_path: str | Path) -> None:
    """
    Saves the list of checksums to a JSON file.

    Args:
        checksums: List of checksum dictionaries.
        output_path: Path where the JSON file will be saved.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "generated_from": str(output_file.parent.parent), # Contextual root
        "checksums": checksums
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logging.info(f"Checksums saved to {output_file}")


def main():
    """
    Command-line entry point for manual execution if needed.
    """
    logger = get_logger("checksums_main")
    config = get_config()
    
    raw_dir = config.get("paths.raw_data")
    state_dir = config.get("paths.state")
    
    ensure_raw_directory(raw_dir)
    checksums = scan_and_hash_directory(raw_dir)
    save_checksums(checksums, state_dir / "checksums_raw.json")
    
    logger.info("Done.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
