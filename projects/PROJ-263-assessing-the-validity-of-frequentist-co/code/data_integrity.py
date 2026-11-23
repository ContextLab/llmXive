import os
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

from config import get_raw_data_dir, get_processed_data_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def generate_checksums_for_raw_data() -> Dict[str, Any]:
    """
    Scan the raw data directory for all files and generate checksums.

    This function implements Principle III: Data Integrity via Checksums.
    It ensures that every file in the raw data directory has a verified hash.

    Returns:
        Dictionary containing file paths and their SHA-256 checksums.
    """
    raw_dir = get_raw_data_dir()
    if not raw_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_dir}")
        return {}

    checksums = {}
    files_processed = 0

    for file_path in raw_dir.iterdir():
        if file_path.is_file():
            # Skip hidden files or temporary files
            if file_path.name.startswith('.'):
                continue

            try:
                checksum = compute_file_sha256(file_path)
                checksums[str(file_path)] = checksum
                files_processed += 1
                logger.info(f"Generated checksum for {file_path.name}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to generate checksum for {file_path}: {e}")

    logger.info(f"Generated checksums for {files_processed} files in {raw_dir}")
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Save the generated checksums to a JSON file.

    Args:
        checksums: Dictionary of file paths to checksums.
        output_path: Optional specific path to save the checksums. Defaults to data/processed/checksums.json.

    Returns:
        Path to the saved checksum file.
    """
    if output_path is None:
        processed_dir = get_processed_data_dir()
        processed_dir.mkdir(parents=True, exist_ok=True)
        output_path = processed_dir / "checksums.json"
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksums saved to {output_path}")
        return output_path
    except IOError as e:
        logger.error(f"Failed to save checksums to {output_path}: {e}")
        raise

def verify_checksums(checksums_path: Optional[Path] = None) -> bool:
    """
    Verify the integrity of raw data files against stored checksums.

    Args:
        checksums_path: Path to the checksums JSON file. Defaults to data/processed/checksums.json.

    Returns:
        True if all files match their checksums, False otherwise.
    """
    if checksums_path is None:
        processed_dir = get_processed_data_dir()
        checksums_path = processed_dir / "checksums.json"

    if not checksums_path.exists():
        logger.error(f"Checksums file not found: {checksums_path}")
        return False

    try:
        with open(checksums_path, 'r') as f:
            stored_checksums = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksums file: {e}")
        return False

    all_valid = True
    for file_path_str, expected_checksum in stored_checksums.items():
        file_path = Path(file_path_str)
        if not file_path.exists():
            logger.warning(f"File missing during verification: {file_path}")
            all_valid = False
            continue

        try:
            actual_checksum = compute_file_sha256(file_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {file_path}: Expected {expected_checksum}, got {actual_checksum}")
                all_valid = False
            else:
                logger.info(f"Verified {file_path.name}: OK")
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            all_valid = False

    return all_valid

def main():
    """
    Main entry point for the data integrity module.
    Generates checksums for all raw data files and saves them.
    """
    logger.info("Starting data integrity checksum generation...")
    
    # Generate checksums for all files in the raw data directory
    checksums = generate_checksums_for_raw_data()
    
    if not checksums:
        logger.warning("No files found to generate checksums for.")
        return

    # Save the checksums
    save_checksums(checksums)
    
    # Optionally verify immediately
    logger.info("Verifying generated checksums...")
    if verify_checksums():
        logger.info("Verification successful: All checksums match.")
    else:
        logger.error("Verification failed: Some checksums did not match.")

if __name__ == "__main__":
    main()
