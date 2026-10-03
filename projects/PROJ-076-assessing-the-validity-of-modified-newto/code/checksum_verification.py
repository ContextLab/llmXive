"""
T016: Implement checksum verification and metadata logging for downloaded SPARC data.

This module verifies the integrity of downloaded SPARC data using SHA-256 checksums
and updates the project metadata file (data/metadata.yaml) with verification results.
"""
import os
import logging
import hashlib
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Import existing utilities
from utils import get_logger, get_timestamp, ensure_directory
from config import load_config, create_default_metadata

# Import download functions for re-use
from download import download_file, verify_file_integrity

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum

    Returns:
        Hex digest of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_sparc_data_integrity(raw_data_path: Path, expected_checksum: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify the integrity of downloaded SPARC data.

    Args:
        raw_data_path: Path to the downloaded SPARC data file
        expected_checksum: Optional expected checksum for comparison

    Returns:
        Dictionary with verification results
    """
    logger = get_logger(__name__)
    
    if not raw_data_path.exists():
        logger.error(f"Raw data file not found: {raw_data_path}")
        return {
            "verified": False,
            "error": "File not found",
            "path": str(raw_data_path)
        }

    try:
        actual_checksum = calculate_sha256(raw_data_path)
        file_size = raw_data_path.stat().st_size
        file_mtime = datetime.fromtimestamp(raw_data_path.stat().st_mtime).isoformat()

        result = {
            "verified": True,
            "checksum": actual_checksum,
            "file_size": file_size,
            "file_mtime": file_mtime,
            "path": str(raw_data_path)
        }

        if expected_checksum:
            if actual_checksum == expected_checksum:
                logger.info(f"Checksum verification PASSED for {raw_data_path.name}")
            else:
                logger.error(f"Checksum verification FAILED for {raw_data_path.name}")
                logger.error(f"  Expected: {expected_checksum}")
                logger.error(f"  Actual:   {actual_checksum}")
                result["verified"] = False
                result["error"] = "Checksum mismatch"

        return result

    except Exception as e:
        logger.error(f"Error verifying file integrity: {e}")
        return {
            "verified": False,
            "error": str(e),
            "path": str(raw_data_path)
        }

def update_metadata_with_verification(metadata_path: Path, verification_result: Dict[str, Any], 
                                    download_info: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update the metadata.yaml file with verification results.

    Args:
        metadata_path: Path to the metadata.yaml file
        verification_result: Result dictionary from verify_sparc_data_integrity
        download_info: Optional additional download information to log

    Returns:
        True if update was successful, False otherwise
    """
    logger = get_logger(__name__)

    try:
        # Load existing metadata or create default
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = yaml.safe_load(f)
        else:
            metadata = create_default_metadata()

        # Ensure data section exists
        if 'data' not in metadata:
            metadata['data'] = {}

        # Update verification information
        metadata['data']['verification'] = {
            "verified": verification_result.get("verified", False),
            "checksum": verification_result.get("checksum"),
            "file_size": verification_result.get("file_size"),
            "verification_timestamp": get_timestamp(),
            "error": verification_result.get("error") if not verification_result.get("verified") else None
        }

        # Update download timestamp if provided
        if download_info and "timestamp" in download_info:
            metadata['data']['download_timestamp'] = download_info["timestamp"]
        
        if download_info and "version" in download_info:
            metadata['data']['version'] = download_info["version"]

        # Ensure directory exists
        ensure_directory(metadata_path.parent)

        # Write updated metadata
        with open(metadata_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Metadata updated successfully at {metadata_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")
        return False

def main():
    """
    Main entry point for checksum verification and metadata logging.
    
    This function:
    1. Loads configuration to get data paths
    2. Verifies the integrity of the downloaded SPARC data
    3. Updates data/metadata.yaml with verification results
    """
    logger = get_logger(__name__)
    logger.info("Starting SPARC data checksum verification (T016)")

    try:
        # Load configuration
        config = load_config()
        metadata_path = Path(config.get('paths', {}).get('metadata', 'data/metadata.yaml'))
        raw_data_path = Path(config.get('paths', {}).get('raw_data', 'data/raw/sparc_data.zip'))

        # Ensure metadata file exists
        if not metadata_path.exists():
            logger.info("Creating initial metadata file")
            create_default_metadata(metadata_path)

        # Verify data integrity
        logger.info(f"Verifying integrity of {raw_data_path}")
        verification_result = verify_sparc_data_integrity(raw_data_path)

        if verification_result["verified"]:
            logger.info(f"Checksum: {verification_result['checksum']}")
            logger.info(f"File size: {verification_result['file_size']} bytes")
        else:
            logger.warning(f"Verification failed: {verification_result.get('error', 'Unknown error')}")

        # Update metadata
        download_info = {
            "timestamp": get_timestamp(),
            "version": "1.0"
        }
        
        success = update_metadata_with_verification(metadata_path, verification_result, download_info)

        if success:
            logger.info("T016 completed successfully: Checksum verification and metadata logging complete")
            return 0
        else:
            logger.error("T016 failed: Could not update metadata")
            return 1

    except Exception as e:
        logger.error(f"T016 failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
