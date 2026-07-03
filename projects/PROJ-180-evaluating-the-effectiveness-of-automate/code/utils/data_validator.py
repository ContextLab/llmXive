"""
Data directory structure and checksum validation logic.

This module ensures the integrity of raw and processed data directories
by creating necessary structure and validating file checksums against
stored manifests.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from utils.config import get_data_raw_dir, get_data_processed_dir
from utils.hasher import hash_file, generate_manifest, verify_manifest

logger = logging.getLogger(__name__)


def ensure_data_structure() -> Dict[str, Path]:
    """
    Ensures the required data directory structure exists.
    
    Creates:
      - data/raw/
      - data/processed/
      - data/raw/.checksums/
      - data/processed/.checksums/
    
    Returns:
        Dict mapping directory names to their Path objects.
    """
    raw_dir = get_data_raw_dir()
    processed_dir = get_data_processed_dir()
    
    dirs = {
        'raw': raw_dir,
        'processed': processed_dir,
        'raw_checksums': raw_dir / '.checksums',
        'processed_checksums': processed_dir / '.checksums'
    }
    
    for name, path in dirs.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")
    
    return dirs


def validate_raw_data() -> Tuple[bool, List[str]]:
    """
    Validates checksums of all files in data/raw/ against stored manifest.
    
    Returns:
        Tuple of (is_valid, list_of_invalid_files)
    """
    raw_dir = get_data_raw_dir()
    checksums_dir = raw_dir / '.checksums'
    manifest_path = checksums_dir / 'manifest.json'
    
    if not manifest_path.exists():
        logger.warning(f"No manifest found at {manifest_path}. Generating one.")
        return generate_manifest(raw_dir, checksums_dir), []
    
    is_valid, invalid_files = verify_manifest(manifest_path)
    
    if not is_valid:
        logger.error(f"Checksum validation failed for {len(invalid_files)} files in data/raw/")
    else:
        logger.info("All files in data/raw/ passed checksum validation.")
    
    return is_valid, invalid_files


def validate_processed_data() -> Tuple[bool, List[str]]:
    """
    Validates checksums of all files in data/processed/ against stored manifest.
    
    Returns:
        Tuple of (is_valid, list_of_invalid_files)
    """
    processed_dir = get_data_processed_dir()
    checksums_dir = processed_dir / '.checksums'
    manifest_path = checksums_dir / 'manifest.json'
    
    if not manifest_path.exists():
        logger.warning(f"No manifest found at {manifest_path}. Generating one.")
        return generate_manifest(processed_dir, checksums_dir), []
    
    is_valid, invalid_files = verify_manifest(manifest_path)
    
    if not is_valid:
        logger.error(f"Checksum validation failed for {len(invalid_files)} files in data/processed/")
    else:
        logger.info("All files in data/processed/ passed checksum validation.")
    
    return is_valid, invalid_files


def refresh_manifests() -> Dict[str, str]:
    """
    Regenerates checksum manifests for both raw and processed data.
    
    Returns:
        Dict with status messages for each directory.
    """
    dirs = ensure_data_structure()
    results = {}
    
    # Refresh raw
    raw_manifest_path = dirs['raw_checksums'] / 'manifest.json'
    generate_manifest(dirs['raw'], dirs['raw_checksums'])
    results['raw'] = f"Manifest updated at {raw_manifest_path}"
    
    # Refresh processed
    processed_manifest_path = dirs['processed_checksums'] / 'manifest.json'
    generate_manifest(dirs['processed'], dirs['processed_checksums'])
    results['processed'] = f"Manifest updated at {processed_manifest_path}"
    
    return results


def main():
    """
    CLI entry point for data validation and structure setup.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger.info("Starting data directory structure and checksum validation...")
    
    # Ensure structure
    dirs = ensure_data_structure()
    logger.info(f"Data structure ready: raw={dirs['raw']}, processed={dirs['processed']}")
    
    # Validate
    raw_valid, raw_invalid = validate_raw_data()
    proc_valid, proc_invalid = validate_processed_data()
    
    # Report
    print("\n=== Data Validation Report ===")
    print(f"Raw Data Valid: {raw_valid}")
    if raw_invalid:
        print(f"  Invalid files: {raw_invalid}")
    print(f"Processed Data Valid: {proc_valid}")
    if proc_invalid:
        print(f"  Invalid files: {proc_invalid}")
    
    if not raw_valid or not proc_valid:
        print("\nChecksum mismatches detected. Running refresh...")
        refresh_manifests()
        print("Manifests refreshed.")
    else:
        print("\nAll data integrity checks passed.")


if __name__ == '__main__':
    main()
