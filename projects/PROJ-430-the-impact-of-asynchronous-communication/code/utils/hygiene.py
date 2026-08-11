import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

MANIFEST_FILE = "manifest.json"

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.
    Reads the file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the manifest JSON file if it exists, otherwise return an empty dict.
    """
    if not manifest_path.exists():
        return {}
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_manifest(manifest_path: Path, manifest: Dict[str, Any]):
    """
    Save the manifest dictionary to a JSON file with indentation.
    """
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

def update_state_manifest(file_path: Path, manifest_path: Path):
    """
    Hash the artifact, add metadata (size, timestamp), and persist the manifest.
    Implements Constitution Principle V (State Integrity).
    
    This function:
    1. Loads the existing manifest (or creates a new one if missing).
    2. Computes the SHA-256 hash of the provided file.
    3. Updates the manifest entry for the file with hash, size, and mtime.
    4. Saves the updated manifest back to disk.
    """
    manifest = load_manifest(manifest_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot update manifest for non-existent file: {file_path}")
    
    file_name = file_path.name
    file_hash = compute_sha256(file_path)
    file_stat = file_path.stat()
    
    manifest[file_name] = {
        "hash": file_hash,
        "size": file_stat.st_size,
        "updated_at": str(file_stat.st_mtime)
    }
    
    save_manifest(manifest_path, manifest)
