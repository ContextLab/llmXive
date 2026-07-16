"""
State management utilities for tracking artifact hashes and integrity.

This module implements Constitution Principle V by tracking artifact
hashes and ensuring data integrity throughout the pipeline.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional
import yaml

STATE_DIR = Path("state")
ARTIFACT_HASHES_FILE = STATE_DIR / "artifact_hashes.yaml"

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hexadecimal string of the SHA-256 hash.
    
    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def update_artifact_hash(path: Path) -> None:
    """
    Compute SHA-256 hash of an artifact and append to state file.
    
    Args:
        path: Path to the artifact file.
    
    Raises:
        FileNotFoundError: If the file doesn't exist.
    """
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Compute hash
    file_hash = compute_sha256(path)
    
    # Load existing hashes
    hashes = {}
    if ARTIFACT_HASHES_FILE.exists():
        with open(ARTIFACT_HASHES_FILE, 'r') as f:
            hashes = yaml.safe_load(f) or {}
    
    # Update hash for this artifact
    artifact_key = str(path.relative_to(Path.cwd()))
    hashes[artifact_key] = {
        "hash": file_hash,
        "updated_at": str(Path.cwd().joinpath("state").parent / "state" / "artifact_hashes.yaml".parent / "state" / "artifact_hashes.yaml")  # Simplified for now
    }
    
    # Save updated hashes
    with open(ARTIFACT_HASHES_FILE, 'w') as f:
        yaml.dump(hashes, f, default_flow_style=False)

def verify_artifact_integrity(path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verify the integrity of an artifact by comparing its hash.
    
    Args:
        path: Path to the artifact file.
        expected_hash: Expected SHA-256 hash. If None, loads from state file.
    
    Returns:
        True if integrity is verified, False otherwise.
    
    Raises:
        FileNotFoundError: If the file or expected hash is not found.
    """
    if not path.exists():
        raise FileNotFoundError(f"Artifact not found: {path}")
    
    current_hash = compute_sha256(path)
    
    if expected_hash is None:
        # Load expected hash from state file
        if not ARTIFACT_HASHES_FILE.exists():
            raise FileNotFoundError(f"State file not found: {ARTIFACT_HASHES_FILE}")
        
        with open(ARTIFACT_HASHES_FILE, 'r') as f:
            hashes = yaml.safe_load(f) or {}
        
        artifact_key = str(path.relative_to(Path.cwd()))
        if artifact_key not in hashes:
            raise FileNotFoundError(f"No hash recorded for artifact: {artifact_key}")
        
        expected_hash = hashes[artifact_key]["hash"]
    
    return current_hash == expected_hash

def main():
    """Main function for testing state management utilities."""
    # Create a test file
    test_file = Path("test_artifact.txt")
    test_file.write_text("Test content for hashing")
    
    try:
        # Compute hash
        file_hash = compute_sha256(test_file)
        print(f"SHA-256 hash: {file_hash}")
        
        # Update artifact hash
        update_artifact_hash(test_file)
        print(f"Updated artifact hash in {ARTIFACT_HASHES_FILE}")
        
        # Verify integrity
        is_valid = verify_artifact_integrity(test_file)
        print(f"Integrity verified: {is_valid}")
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()

if __name__ == "__main__":
    main()
