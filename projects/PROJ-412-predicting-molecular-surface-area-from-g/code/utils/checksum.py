"""
Dataset checksumming utility for verifying data integrity and reproducibility.

This module provides functions to calculate and verify checksums for dataset files
to ensure data integrity throughout the pipeline.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .config import get_project_root, get_data_dir
from .logging import get_logger

logger = get_logger(__name__)

# Supported hash algorithms
SUPPORTED_ALGORITHMS = ['sha256', 'sha512', 'md5']
DEFAULT_ALGORITHM = 'sha256'

# Checksum manifest file location
CHECKSUM_MANIFEST = 'data/processed/.checksum_manifest.json'

def calculate_file_checksum(file_path: str, algorithm: str = DEFAULT_ALGORITHM, chunk_size: int = 8192) -> str:
    """
    Calculate the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (sha256, sha512, md5)
        chunk_size: Size of chunks to read at a time for large files
    
    Returns:
        Hexadecimal string of the checksum
    
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If an unsupported algorithm is specified
    """
    if algorithm not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Supported: {SUPPORTED_ALGORITHMS}")
    
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    
    logger.debug(f"Calculating {algorithm} checksum for {file_path}")
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    
    checksum = hasher.hexdigest()
    logger.debug(f"Checksum for {file_path}: {checksum}")
    
    return checksum

def calculate_directory_checksum(dir_path: str, algorithm: str = DEFAULT_ALGORITHM, 
                                 extensions: Optional[list] = None) -> Dict[str, Any]:
    """
    Calculate checksums for all files in a directory and aggregate them.
    
    Args:
        dir_path: Path to the directory
        algorithm: Hash algorithm to use
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.parquet'])
                   If None, all files are included
    
    Returns:
        Dictionary containing:
            - 'dir_checksum': Aggregated checksum of all files
            - 'files': List of dictionaries with file path and individual checksum
            - 'file_count': Number of files processed
            - 'algorithm': Algorithm used
    """
    dir_path = Path(dir_path)
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    file_checksums = []
    all_content = b''
    
    # Get all files recursively, sorted for deterministic ordering
    files = sorted(dir_path.rglob('*'))
    files = [f for f in files if f.is_file()]
    
    if extensions:
        files = [f for f in files if f.suffix.lower() in [ext.lower() for ext in extensions]]
    
    logger.info(f"Processing {len(files)} files in {dir_path}")
    
    for file_path in files:
        try:
            checksum = calculate_file_checksum(file_path, algorithm)
            file_checksums.append({
                'path': str(file_path.relative_to(dir_path)),
                'checksum': checksum
            })
            # Aggregate for directory checksum
            all_content += file_path.read_bytes()
        except Exception as e:
            logger.warning(f"Failed to checksum {file_path}: {e}")
            continue
    
    # Calculate aggregated directory checksum
    dir_hasher = hashlib.new(algorithm)
    dir_hasher.update(all_content)
    dir_checksum = dir_hasher.hexdigest()
    
    result = {
        'dir_checksum': dir_checksum,
        'files': file_checksums,
        'file_count': len(file_checksums),
        'algorithm': algorithm
    }
    
    logger.info(f"Directory checksum for {dir_path}: {dir_checksum} ({len(file_checksums)} files)")
    
    return result

def verify_file_checksum(file_path: str, expected_checksum: str, 
                         algorithm: str = DEFAULT_ALGORITHM) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm used for the expected checksum
    
    Returns:
        True if checksum matches, False otherwise
    """
    actual_checksum = calculate_file_checksum(file_path, algorithm)
    matches = actual_checksum == expected_checksum

    if not matches:
        logger.error(f"Checksum mismatch for {file_path}:")
        logger.error(f"  Expected: {expected_checksum}")
        logger.error(f"  Actual:   {actual_checksum}")
    else:
        logger.debug(f"Checksum verified for {file_path}")

    return matches

def verify_directory_checksum(dir_path: str, expected_checksum: str,
                              algorithm: str = DEFAULT_ALGORITHM) -> bool:
    """
    Verify a directory's aggregated checksum.
    
    Args:
        dir_path: Path to the directory
        expected_checksum: Expected aggregated checksum
        algorithm: Hash algorithm used
    
    Returns:
        True if checksum matches, False otherwise
    """
    result = calculate_directory_checksum(dir_path, algorithm)
    matches = result['dir_checksum'] == expected_checksum

    if not matches:
        logger.error(f"Directory checksum mismatch for {dir_path}:")
        logger.error(f"  Expected: {expected_checksum}")
        logger.error(f"  Actual:   {result['dir_checksum']}")
        logger.error(f"  Files processed: {result['file_count']}")
    else:
        logger.debug(f"Directory checksum verified for {dir_path}")

    return matches

def save_checksum_manifest(file_paths: list, output_path: Optional[str] = None,
                           algorithm: str = DEFAULT_ALGORITHM) -> str:
    """
    Save checksums for multiple files to a manifest file.
    
    Args:
        file_paths: List of file paths to checksum
        output_path: Path for the manifest file (default: data/processed/.checksum_manifest.json)
        algorithm: Hash algorithm to use
    
    Returns:
        Path to the created manifest file
    """
    import json
    from datetime import datetime

    if output_path is None:
        output_path = str(get_project_root() / CHECKSUM_MANIFEST)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        'created_at': datetime.utcnow().isoformat(),
        'algorithm': algorithm,
        'files': []
    }

    for file_path in file_paths:
        try:
            checksum = calculate_file_checksum(file_path, algorithm)
            manifest['files'].append({
                'path': str(file_path),
                'checksum': checksum
            })
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
            manifest['files'].append({
                'path': str(file_path),
                'checksum': None,
                'error': str(e)
            })

    manifest['file_count'] = len(manifest['files'])
    manifest['success_count'] = sum(1 for f in manifest['files'] if f['checksum'] is not None)

    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Checksum manifest saved to {output_path}")
    return str(output_path)

def load_checksum_manifest(manifest_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a checksum manifest file.
    
    Args:
        manifest_path: Path to the manifest file (default: data/processed/.checksum_manifest.json)
    
    Returns:
        Dictionary containing the manifest data
    """
    import json

    if manifest_path is None:
        manifest_path = str(get_project_root() / CHECKSUM_MANIFEST)

    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    logger.debug(f"Loaded checksum manifest from {manifest_path}")
    return manifest

def verify_manifest_checksums(manifest_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify all checksums in a manifest file against actual files.
    
    Args:
        manifest_path: Path to the manifest file
    
    Returns:
        Dictionary with verification results:
            - 'all_passed': Boolean indicating if all checksums match
            - 'total_files': Total number of files in manifest
            - 'passed_count': Number of files that passed verification
            - 'failed_files': List of files that failed verification
    """
    manifest = load_checksum_manifest(manifest_path)

    results = {
        'all_passed': True,
        'total_files': manifest.get('file_count', 0),
        'passed_count': 0,
        'failed_files': []
    }

    for file_entry in manifest.get('files', []):
        file_path = file_entry.get('path')
        expected_checksum = file_entry.get('checksum')

        if not file_path or expected_checksum is None:
            continue

        if verify_file_checksum(file_path, expected_checksum, manifest.get('algorithm', DEFAULT_ALGORITHM)):
            results['passed_count'] += 1
        else:
            results['all_passed'] = False
            results['failed_files'].append({
                'path': file_path,
                'expected': expected_checksum,
                'actual': calculate_file_checksum(file_path, manifest.get('algorithm', DEFAULT_ALGORITHM))
            })

    logger.info(f"Manifest verification: {results['passed_count']}/{results['total_files']} files passed")

    return results
