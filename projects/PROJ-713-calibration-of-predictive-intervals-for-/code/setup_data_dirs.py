"""
Setup script for data directory structures with checksum verification.

This module creates the required directory structure for raw and processed data
and provides utilities for checksum computation and verification to ensure
data integrity.
"""
import os
import hashlib
import logging
from pathlib import Path
import sys
import json
from typing import Optional, Dict, Any

# Import project configuration
try:
    from config import DATA_RAW_DIR, DATA_PROCESSED_DIR, PROJECT_ROOT
except ImportError:
    # Fallback for direct execution
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
    DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

from utils.logger import get_logger, log_event
from utils.exceptions import DataValidationError, ConfigurationError

logger = get_logger(__name__)


def ensure_dir(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path object representing the directory to create
        
    Returns:
        True if directory exists or was created successfully, False otherwise
        
    Raises:
        ConfigurationError: If directory creation fails due to permissions
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directory ensured: {path}")
        return True
    except PermissionError as e:
        error_msg = f"Permission denied creating directory: {path}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e
    except OSError as e:
        error_msg = f"OS error creating directory {path}: {e}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg) from e


def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the file checksum
        
    Raises:
        DataValidationError: If file does not exist or cannot be read
    """
    if not file_path.exists():
        raise DataValidationError(f"File does not exist: {file_path}")
    
    if not file_path.is_file():
        raise DataValidationError(f"Path is not a file: {file_path}")
    
    try:
        hasher = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        error_msg = f"Failed to read file for checksum: {file_path}"
        logger.error(error_msg)
        raise DataValidationError(error_msg) from e


def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected hexadecimal checksum string
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        True if checksum matches, False otherwise
        
    Raises:
        DataValidationError: If file does not exist or checksum format is invalid
    """
    if not file_path.exists():
        raise DataValidationError(f"File does not exist for checksum verification: {file_path}")
    
    if not file_path.is_file():
        raise DataValidationError(f"Path is not a file: {file_path}")
    
    try:
        computed = compute_file_checksum(file_path, algorithm)
        matches = computed.lower() == expected_checksum.lower()
        
        if not matches:
            logger.warning(
                f"Checksum mismatch for {file_path.name}. "
                f"Expected: {expected_checksum}, Got: {computed}"
            )
        
        return matches
    except DataValidationError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error during checksum verification: {e}"
        logger.error(error_msg)
        raise DataValidationError(error_msg) from e


def create_checksum_manifest(directory: Path, output_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Create a manifest of checksums for all files in a directory.
    
    Args:
        directory: Directory to scan for files
        output_path: Optional path to write the manifest JSON file
        
    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    if not directory.exists():
        raise DataValidationError(f"Directory does not exist: {directory}")
    
    manifest = {}
    
    for file_path in directory.rglob('*'):
        if file_path.is_file():
            try:
                relative_path = file_path.relative_to(directory)
                checksum = compute_file_checksum(file_path)
                manifest[str(relative_path)] = checksum
                logger.debug(f"Computed checksum for {relative_path}: {checksum[:16]}...")
            except DataValidationError as e:
                logger.warning(f"Skipping file {file_path}: {e}")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to {output_path}")
    
    return manifest


def setup_data_directories() -> Dict[str, Path]:
    """
    Initialize the complete data directory structure with verification.
    
    Creates the required directory hierarchy for raw and processed data,
    and generates initial checksum manifests.
    
    Returns:
        Dictionary mapping directory names to their Path objects
        
    Raises:
        ConfigurationError: If directory creation fails
    """
    logger.info("Starting data directory setup...")
    
    directories = {
        'raw': DATA_RAW_DIR,
        'processed': DATA_PROCESSED_DIR,
        'raw/m4': DATA_RAW_DIR / 'm4',
        'raw/uci': DATA_RAW_DIR / 'uci',
        'processed/m4': DATA_PROCESSED_DIR / 'm4',
        'processed/uci': DATA_PROCESSED_DIR / 'uci',
    }
    
    created_dirs = []
    for name, path in directories.items():
        if ensure_dir(path):
            created_dirs.append(str(path))
    
    # Create initial manifests
    manifest_raw = DATA_RAW_DIR / '.checksums.json'
    manifest_processed = DATA_PROCESSED_DIR / '.checksums.json'
    
    create_checksum_manifest(DATA_RAW_DIR, manifest_raw)
    create_checksum_manifest(DATA_PROCESSED_DIR, manifest_processed)
    
    log_event(
        event_type="data_dirs_setup",
        success=True,
        message=f"Created {len(created_dirs)} directories",
        data={
            "directories": created_dirs,
            "manifests": [str(manifest_raw), str(manifest_processed)]
        }
    )
    
    logger.info("Data directory setup completed successfully.")
    return directories


def main():
    """Main entry point for command-line execution."""
    try:
        dirs = setup_data_directories()
        print(f"Successfully created data directories:")
        for name, path in dirs.items():
            print(f"  - {name}: {path}")
        return 0
    except (ConfigurationError, DataValidationError) as e:
        logger.error(f"Setup failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during setup: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())