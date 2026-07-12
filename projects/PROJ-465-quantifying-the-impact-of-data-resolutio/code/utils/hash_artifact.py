"""
Artifact hashing utilities for versioning and integrity checks.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_hash(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def hash_artifact_manifest(manifest: Dict[str, Any]) -> str:
    """Hash a manifest dictionary."""
    return compute_string_hash(json.dumps(manifest, sort_keys=True))

def save_hash_manifest(manifest: Dict[str, Any], output_path: Union[str, Path]):
    """Save a manifest with its hash to a JSON file."""
    manifest_hash = hash_artifact_manifest(manifest)
    manifest['_hash'] = manifest_hash
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def load_hash_manifest(input_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a manifest and return its content."""
    with open(input_path, 'r') as f:
        return json.load(f)

def verify_artifact_integrity(file_path: Union[str, Path], expected_hash: str) -> bool:
    """Verify a file's hash against an expected value."""
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash
