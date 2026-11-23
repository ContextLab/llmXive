"""
Data integrity check utility for verifying file checksums.

This module provides functions to compute and verify SHA256 checksums
for data files to ensure integrity during download and processing.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

from utils.logger import get_logger, ProcessingError, DataFetchError

logger = get_logger(__name__)

# Default manifest file name
CHECKSUM_MANIFEST = "checksums.json"

def compute_file_checksum(filepath: Path, algorithm: str = "sha256", chunk_size: int = 8192) -> str:
    """
    Compute the checksum of a file using the specified algorithm.
    
    Args:
        filepath: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        chunk_size: Size of chunks to read (for memory efficiency)
        
    Returns:
        Hexadecimal checksum string
        
    Raises:
        ProcessingError: If file cannot be read or algorithm is unsupported
        FileNotFoundError: If the file does not exist
    """
    if not filepath.exists():
        raise FileNotFoundError(f"Cannot compute checksum: file not found at {filepath}")
    
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ProcessingError(f"Unsupported hash algorithm: {algorithm}") from e
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    
    return hasher.hexdigest()

def verify_file_checksum(filepath: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        filepath: Path to the file to verify
        expected_checksum: Expected hexadecimal checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        True if checksum matches, False otherwise
        
    Raises:
        FileNotFoundError: If the file does not exist
    """
    actual_checksum = compute_file_checksum(filepath, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()

def create_checksum_manifest(data_dir: Path, output_path: Optional[Path] = None, algorithm: str = "sha256") -> Dict[str, str]:
    """
    Create a manifest of checksums for all files in a directory.
    
    Args:
        data_dir: Directory containing files to checksum
        output_path: Optional path to write the manifest JSON file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Dictionary mapping relative file paths to their checksums
        
    Raises:
        ProcessingError: If directory cannot be read
    """
    if not data_dir.exists():
        raise ProcessingError(f"Cannot create manifest: directory not found at {data_dir}")
    
    if not data_dir.is_dir():
        raise ProcessingError(f"Path is not a directory: {data_dir}")
    
    checksums = {}
    
    logger.info(f"Computing checksums for files in {data_dir}")
    
    for file_path in data_dir.rglob('*'):
        if file_path.is_file():
            # Skip the manifest file itself if it exists
            if file_path.name == CHECKSUM_MANIFEST:
                continue
            
            try:
                checksum = compute_file_checksum(file_path, algorithm)
                relative_path = str(file_path.relative_to(data_dir))
                checksums[relative_path] = checksum
                logger.debug(f"Computed checksum for {relative_path}: {checksum[:16]}...")
            except Exception as e:
                logger.warning(f"Failed to compute checksum for {file_path}: {e}")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksum manifest written to {output_path}")
    
    return checksums

def verify_checksum_manifest(data_dir: Path, manifest_path: Optional[Path] = None, algorithm: str = "sha256") -> Dict[str, bool]:
    """
    Verify all files in a directory against a checksum manifest.
    
    Args:
        data_dir: Directory containing files to verify
        manifest_path: Path to the checksum manifest JSON file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Dictionary mapping relative file paths to verification status (True/False)
        
    Raises:
        ProcessingError: If manifest cannot be read
    """
    if manifest_path is None:
        manifest_path = data_dir / CHECKSUM_MANIFEST
    
    if not manifest_path.exists():
        raise ProcessingError(f"Checksum manifest not found at {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            expected_checksums = json.load(f)
    except json.JSONDecodeError as e:
        raise ProcessingError(f"Invalid JSON in checksum manifest: {manifest_path}") from e
    
    results = {}
    all_valid = True
    
    for relative_path, expected_checksum in expected_checksums.items():
        file_path = data_dir / relative_path
        
        if not file_path.exists():
            logger.error(f"File missing during verification: {relative_path}")
            results[relative_path] = False
            all_valid = False
            continue
        
        try:
            is_valid = verify_file_checksum(file_path, expected_checksum, algorithm)
            results[relative_path] = is_valid
            
            if is_valid:
                logger.debug(f"Checksum verified for {relative_path}")
            else:
                logger.error(f"Checksum mismatch for {relative_path}")
                all_valid = False
        except Exception as e:
            logger.error(f"Failed to verify checksum for {relative_path}: {e}")
            results[relative_path] = False
            all_valid = False
    
    if all_valid:
        logger.info("All file checksums verified successfully")
    else:
        failed_files = [f for f, v in results.items() if not v]
        logger.warning(f"Checksum verification failed for {len(failed_files)} files")
    
    return results

def add_file_to_manifest(data_dir: Path, file_path: Path, manifest_path: Optional[Path] = None, algorithm: str = "sha256") -> str:
    """
    Compute checksum for a single file and add/update it in the manifest.
    
    Args:
        data_dir: Base data directory
        file_path: Path to the file to checksum (must be under data_dir)
        manifest_path: Path to the checksum manifest JSON file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        The computed checksum
        
    Raises:
        ProcessingError: If file is not under data_dir
    """
    file_path = Path(file_path)
    data_dir = Path(data_dir)
    
    if not file_path.is_absolute():
        file_path = data_dir / file_path
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not str(file_path.resolve()).startswith(str(data_dir.resolve())):
        raise ProcessingError(f"File must be under data directory: {file_path}")
    
    checksum = compute_file_checksum(file_path, algorithm)
    
    if manifest_path is None:
        manifest_path = data_dir / CHECKSUM_MANIFEST
    
    # Load existing manifest or create new one
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except json.JSONDecodeError:
            manifest = {}
    else:
        manifest = {}
    
    # Update manifest
    relative_path = str(file_path.relative_to(data_dir))
    manifest[relative_path] = checksum
    
    # Write back
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Added/updated checksum for {relative_path} in manifest")
    
    return checksum