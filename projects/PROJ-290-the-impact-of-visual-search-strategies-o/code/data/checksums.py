"""
Task T015: Create data/raw/ directory structure and save downloaded dataset checksums.

This script ensures the `data/raw/` directory exists and computes SHA-256 checksums
for all files found in that directory (populated by T010). It saves the results
to `state/dataset_checksums.json` to support artifact verification (Constitution Principle V).
"""
import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List

# Import existing utilities from the project
from config import get_config
from utils.logging import get_logger
from utils.hash_artifacts import calculate_sha256


def get_logger_wrapper(name: str) -> logging.Logger:
    """Wrapper to get a logger configured for this module."""
    return get_logger(name)


def ensure_raw_directory(config: Any) -> Path:
    """
    Ensures the data/raw directory exists.
    Returns the Path object for the directory.
    """
    raw_dir = config.get("paths", {}).get("data_raw")
    if not raw_dir:
        # Fallback to standard path if config is missing key, though T001b should have set it
        base = config.get("paths", {}).get("data_root", Path("data"))
        raw_dir = Path(base) / "raw"
    else:
        raw_dir = Path(raw_dir)

    raw_dir.mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured directory exists: {raw_dir}")
    return raw_dir


def scan_and_hash_directory(directory: Path) -> List[Dict[str, Any]]:
    """
    Scans a directory for files and calculates SHA-256 hashes.
    Returns a list of dicts: [{'path': str, 'hash': str, 'size_bytes': int}, ...]
    """
    results = []
    if not directory.exists():
        logging.warning(f"Directory does not exist, skipping scan: {directory}")
        return results

    for file_path in directory.rglob("*"):
        if file_path.is_file():
            try:
                file_hash = calculate_sha256(file_path)
                results.append({
                    "relative_path": str(file_path.relative_to(directory)),
                    "absolute_path": str(file_path),
                    "sha256": file_hash,
                    "size_bytes": file_path.stat().st_size
                })
            except Exception as e:
                logging.error(f"Failed to hash {file_path}: {e}")
    
    return results


def save_checksums(checksums: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the checksum list to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": None, # Will be filled by caller if needed, or left null for raw hash
            "source_directory": str(output_path.parent),
            "checksums": checksums
        }, f, indent=2)
    logging.info(f"Checksums saved to: {output_path}")


def main() -> int:
    """
    Main entry point for T015.
    1. Ensure data/raw/ exists.
    2. Scan for files.
    3. Compute checksums.
    4. Save to state/dataset_checksums.json.
    """
    logger = get_logger("T015_checksums")
    logger.info("Starting T015: Create data/raw/ structure and save checksums")

    config = get_config()
    
    # 1. Ensure directory structure
    raw_dir = ensure_raw_directory(config)
    
    # 2. Scan and hash
    checksums = scan_and_hash_directory(raw_dir)
    
    if not checksums:
        logger.warning("No files found in data/raw/ to checksum. This may be expected if download hasn't run yet, but T010 should have populated this.")
    
    # 3. Save results
    state_dir = config.get("paths", {}).get("state_root", Path("state"))
    output_file = Path(state_dir) / "dataset_checksums.json"
    
    save_checksums(checksums, output_file)
    
    logger.info(f"T015 completed. Found {len(checksums)} files.")
    return 0


if __name__ == "__main__":
    exit(main())
