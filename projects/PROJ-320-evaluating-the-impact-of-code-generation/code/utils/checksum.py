"""
Checksum utilities for data integrity verification.

Provides SHA-256 generation and verification for raw JSON artifacts
to ensure data provenance and detect corruption.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Union, Optional


def calculate_checksum(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def verify_checksum(file_path: Union[str, Path], expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected SHA-256 hex string.
        
    Returns:
        True if the checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual_checksum = calculate_checksum(file_path)
    return actual_checksum.lower() == expected_checksum.lower()


def generate_checksum_manifest(data_dir: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> dict:
    """
    Generate a manifest of SHA-256 checksums for all JSON files in a directory.
    
    Args:
        data_dir: Directory containing the files to checksum.
        output_path: Optional path to save the manifest as JSON.
        
    Returns:
        Dictionary mapping filenames to their SHA-256 checksums.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    data_dir = Path(data_dir)
    if not data_dir.exists() or not data_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {data_dir}")
    
    manifest = {}
    json_files = list(data_dir.glob("**/*.json"))
    
    for file_path in json_files:
        relative_path = file_path.relative_to(data_dir)
        checksum = calculate_checksum(file_path)
        manifest[str(relative_path)] = checksum
    
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
    
    return manifest


def load_checksum_manifest(manifest_path: Union[str, Path]) -> dict:
    """
    Load a checksum manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest JSON file.
        
    Returns:
        Dictionary mapping filenames to checksums.
        
    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest is invalid JSON.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)