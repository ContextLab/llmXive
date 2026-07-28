"""
Module for verifying raw data integrity via SHA-256 hashes.

This module provides utilities to compute, store, and verify SHA-256 checksums
for raw data files downloaded by the pipeline. It ensures data integrity
against corruption or tampering.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, List


def compute_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
            
    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify a file's SHA-256 hash against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected SHA-256 hex string.
        
    Returns:
        True if the computed hash matches the expected hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the expected_hash format is invalid.
    """
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ValueError("Expected hash must be a 64-character hex string.")
        
    computed_hash = compute_sha256(file_path)
    return computed_hash.lower() == expected_hash.lower()


def generate_manifest(file_paths: List[str], output_path: str) -> Dict[str, str]:
    """
    Generate a manifest file containing SHA-256 hashes for multiple files.
    
    Args:
        file_paths: List of file paths to include in the manifest.
        output_path: Path where the JSON manifest will be saved.
        
    Returns:
        Dictionary mapping file paths to their SHA-256 hashes.
        
    Raises:
        FileNotFoundError: If any file in file_paths does not exist.
    """
    manifest = {}
    for file_path in file_paths:
        manifest[file_path] = compute_sha256(file_path)
        
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return manifest


def verify_manifest(manifest_path: str) -> Dict[str, bool]:
    """
    Verify all files listed in a manifest against their stored hashes.
    
    Args:
        manifest_path: Path to the JSON manifest file.
        
    Returns:
        Dictionary mapping file paths to verification status (True/False).
        
    Raises:
        FileNotFoundError: If the manifest file or any listed file is missing.
        json.JSONDecodeError: If the manifest file is not valid JSON.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    results = {}
    for file_path, expected_hash in manifest.items():
        try:
            results[file_path] = verify_checksum(file_path, expected_hash)
        except FileNotFoundError:
            results[file_path] = False
            
    return results


def update_manifest_if_changed(file_path: str, manifest_path: str) -> bool:
    """
    Update the manifest for a single file if its hash has changed.
    
    Args:
        file_path: Path to the file to check.
        manifest_path: Path to the manifest file.
        
    Returns:
        True if the manifest was updated, False otherwise.
        
    Raises:
        FileNotFoundError: If the file or manifest does not exist.
    """
    manifest = {}
    if Path(manifest_path).exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
    current_hash = compute_sha256(file_path)
    stored_hash = manifest.get(file_path)
    
    if stored_hash != current_hash:
        manifest[file_path] = current_hash
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        return True
        
    return False