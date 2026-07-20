"""
Artifact Hashing Module.

Implements checksum verification for versioning and integrity.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_hash(s: str) -> str:
    """
    Compute the SHA-256 hash of a string.
    
    Args:
        s: Input string.
        
    Returns:
        Hexadecimal string of the hash.
    """
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def hash_artifact_manifest(manifest: Dict[str, Any]) -> str:
    """
    Compute a hash of a manifest dictionary.
    
    Args:
        manifest: Dictionary of artifact paths and hashes.
        
    Returns:
        Hexadecimal string of the hash.
    """
    # Sort keys for deterministic hashing
    sorted_manifest = json.dumps(manifest, sort_keys=True)
    return compute_string_hash(sorted_manifest)

def save_hash_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Save a hash manifest to a JSON file.
    
    Args:
        manifest: Dictionary of artifact paths and hashes.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def load_hash_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load a hash manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        Dictionary of artifact paths and hashes.
    """
    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_artifact_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verify the integrity of an artifact against an expected hash.
    
    Args:
        file_path: Path to the artifact.
        expected_hash: Expected SHA-256 hash.
        
    Returns:
        True if the hash matches, False otherwise.
    """
    if not file_path.exists():
        return False
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash
