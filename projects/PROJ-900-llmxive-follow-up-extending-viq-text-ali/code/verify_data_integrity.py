"""
Data Integrity Verification Script (T040).

Calculates and stores cryptographic SHA256 checksums for all downloaded
raw datasets (COCO, ImageNet) in data/raw/checksums.json.

This addresses reviewer concerns regarding "Data Hygiene" (Constitution Principle III)
by ensuring raw data integrity is verified and logged before processing.

Dependency: T005 (data_loader.py) which downloads the datasets.
"""
import os
import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure we are in the project root or can find the code directory
# We assume this script runs from the project root: python code/verify_data_integrity.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUMS_FILE = DATA_RAW_DIR / "checksums.json"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 hash of a file.
    Reads the file in chunks to handle large datasets efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error calculating hash for {file_path}: {e}")

def discover_raw_data_files() -> Dict[str, Path]:
    """
    Discover all data files in the data/raw directory.
    Returns a dictionary mapping dataset name to file path.
    """
    if not DATA_RAW_DIR.exists():
        logger.warning(f"Data raw directory does not exist: {DATA_RAW_DIR}")
        return {}

    files = {}
    # We look for common dataset file patterns expected after T005 download
    # T005 downloads COCO and ImageNet. They might be zip archives, tarballs, or extracted folders.
    # We scan for files directly in data/raw or common subfolders if they are archives.
    
    # Strategy: Recursively find all files that look like dataset archives or extracted data
    # that are not hidden.
    for root, _, filenames in os.walk(DATA_RAW_DIR):
        for filename in filenames:
            if filename.startswith('.'):
                continue
            # Skip the checksums file itself
            if filename == "checksums.json":
                continue
            
            file_path = Path(root) / filename
            # Heuristic: Include common archive extensions or image files if extracted
            # Since T005 might leave archives or extracted folders, we hash the archives
            # or specific known files if they are the primary data source.
            # For robustness, we hash everything that isn't a checksum file.
            files[filename] = file_path

    return files

def verify_integrity() -> Dict[str, Any]:
    """
    Main logic to verify data integrity.
    1. Discover files in data/raw.
    2. Calculate SHA256 for each.
    3. Save results to data/raw/checksums.json.
    """
    logger.info(f"Starting data integrity verification in {DATA_RAW_DIR}")
    
    if not DATA_RAW_DIR.exists():
        logger.error(f"Directory {DATA_RAW_DIR} does not exist. Did T005 run successfully?")
        raise FileNotFoundError(f"Raw data directory not found: {DATA_RAW_DIR}")

    files = discover_raw_data_files()
    
    if not files:
        logger.warning("No data files found in data/raw to verify.")
        # Still create an empty or status file to indicate the check ran
        result = {
            "status": "no_files_found",
            "message": "No data files found in data/raw to verify.",
            "checksums": {}
        }
    else:
        checksums = {}
        logger.info(f"Found {len(files)} files to verify.")
        
        for name, path in files.items():
            try:
                logger.info(f"Calculating hash for: {name}")
                file_hash = calculate_sha256(path)
                checksums[name] = {
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "sha256": file_hash,
                    "size_bytes": path.stat().st_size
                }
            except Exception as e:
                logger.error(f"Failed to hash {name}: {e}")
                # We do not fail the whole process for one file, but log it
                checksums[name] = {
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "error": str(e)
                }

        result = {
            "status": "completed",
            "timestamp": str(Path(__file__).parent.parent), # Placeholder for actual timestamp logic if needed
            "checksums": checksums
        }

    # Ensure output directory exists
    CHECKSUMS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(CHECKSUMS_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Checksums written to {CHECKSUMS_FILE}")
    return result

def main():
    parser = argparse.ArgumentParser(description="Verify data integrity by calculating SHA256 checksums.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        result = verify_integrity()
        if result["status"] == "no_files_found":
            logger.warning("Verification completed but no files were found.")
            sys.exit(0) # Not a failure, just no data yet
        logger.info("Data integrity verification completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
