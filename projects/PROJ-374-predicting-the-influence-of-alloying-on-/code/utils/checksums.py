"""
Data hygiene utilities for computing and verifying file checksums.

This module provides functions to calculate SHA-256 checksums for data files
and verify integrity during the data processing pipeline.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Union


def compute_file_checksum(
    file_path: Union[str, Path], 
    algorithm: str = "sha256", 
    chunk_size: int = 8192
) -> str:
    """
    Compute the checksum of a file using the specified hashing algorithm.
    
    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: 'sha256').
        chunk_size: Size of chunks to read at a time.
        
    Returns:
        Hexadecimal string of the checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e
    
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def compute_string_checksum(data: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a string.
    
    Args:
        data: The string to hash.
        algorithm: Hash algorithm to use (default: 'sha256').
        
    Returns:
        Hexadecimal string of the checksum.
        
    Raises:
        ValueError: If the algorithm is not supported.
    """
    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e
    
    hasher.update(data.encode("utf-8"))
    return hasher.hexdigest()


def verify_file_checksum(
    file_path: Union[str, Path], 
    expected_checksum: str, 
    algorithm: str = "sha256"
) -> bool:
    """
    Verify that a file's checksum matches the expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected checksum value.
        algorithm: Hash algorithm to use (default: 'sha256').
        
    Returns:
        True if checksums match, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual_checksum = compute_file_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()


def generate_checksum_manifest(
    file_paths: list[Union[str, Path]], 
    output_path: Union[str, Path], 
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Generate a JSON manifest of checksums for multiple files.
    
    Args:
        file_paths: List of file paths to checksum.
        output_path: Path to save the JSON manifest.
        algorithm: Hash algorithm to use (default: 'sha256').
        
    Returns:
        Dictionary mapping file paths to their checksums.
        
    Raises:
        FileNotFoundError: If any file does not exist.
    """
    manifest = {}
    missing_files = []
    
    for file_path in file_paths:
        file_path = Path(file_path)
        if not file_path.exists():
            missing_files.append(str(file_path))
        else:
            checksum = compute_file_checksum(file_path, algorithm)
            manifest[str(file_path)] = checksum
    
    if missing_files:
        raise FileNotFoundError(f"Missing files: {', '.join(missing_files)}")
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    return manifest


def verify_checksum_manifest(
    manifest_path: Union[str, Path], 
    algorithm: str = "sha256"
) -> Dict[str, bool]:
    """
    Verify files against a stored checksum manifest.
    
    Args:
        manifest_path: Path to the JSON manifest file.
        algorithm: Hash algorithm to use (default: 'sha256').
        
    Returns:
        Dictionary mapping file paths to verification status (True/False).
        
    Raises:
        FileNotFoundError: If the manifest or any referenced file is missing.
        json.JSONDecodeError: If the manifest is invalid JSON.
    """
    manifest_path = Path(manifest_path)
    
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    results = {}
    for file_path, expected_checksum in manifest.items():
        if not Path(file_path).exists():
            results[file_path] = False
        else:
            actual_checksum = compute_file_checksum(file_path, algorithm)
            results[file_path] = actual_checksum.lower() == expected_checksum.lower()
    
    return results


def get_file_metadata(file_path: Union[str, Path]) -> Dict:
    """
    Get basic metadata about a file including size, checksum, and modification time.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Dictionary with file metadata.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    stat_info = file_path.stat()
    
    return {
        "path": str(file_path),
        "size_bytes": stat_info.st_size,
        "modified_timestamp": stat_info.st_mtime,
        "sha256": compute_file_checksum(file_path, "sha256"),
        "exists": True
    }