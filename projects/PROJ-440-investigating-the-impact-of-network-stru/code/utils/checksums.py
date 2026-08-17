"""
Checksum utilities for data integrity verification.
"""
import hashlib
import os
import json
from typing import Dict, List, Optional
from pathlib import Path


def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hexadecimal checksum string
    """
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def generate_checksum_file(file_paths: List[str], output_path: str) -> Dict[str, str]:
    """
    Generate a checksum file for multiple files.
    
    Args:
        file_paths: List of file paths to checksum
        output_path: Path to write the checksum JSON file
    
    Returns:
        Dictionary mapping file paths to their checksums
    """
    checksums = {}
    for file_path in file_paths:
        if os.path.exists(file_path):
          checksums[file_path] = compute_file_checksum(file_path)
        else:
          raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(output_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    return checksums


def verify_checksums(checksum_file_path: str) -> bool:
    """
    Verify checksums from a JSON file.
    
    Args:
        checksum_file_path: Path to the checksum JSON file
    
    Returns:
        True if all checksums match, False otherwise
    """
    with open(checksum_file_path, 'r') as f:
        checksums = json.load(f)
    
    all_valid = True
    for file_path, expected_checksum in checksums.items():
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            all_valid = False
            continue
        
        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum != expected_checksum:
            print(f"Checksum mismatch for {file_path}")
            print(f"  Expected: {expected_checksum}")
            print(f"  Actual:   {actual_checksum}")
            all_valid = False
        else:
            print(f"✓ Verified: {file_path}")
    
    return all_valid


def verify_single_file(file_path: str, expected_checksum: str) -> bool:
    """
    Verify a single file against an expected checksum.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
    
    Returns:
        True if checksum matches, False otherwise
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    actual_checksum = compute_file_checksum(file_path)
    return actual_checksum == expected_checksum


def setup_data_directories(base_dir: str) -> Dict[str, Path]:
    """
    Setup the data directory structure.
    
    Args:
        base_dir: Base directory path
    
    Returns:
        Dictionary of created directory paths
    """
    base_path = Path(base_dir)
    
    directories = {
        'raw': base_path / 'raw',
        'processed': base_path / 'processed',
        'analysis': base_path / 'analysis'
    }
    
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
    
    return directories
