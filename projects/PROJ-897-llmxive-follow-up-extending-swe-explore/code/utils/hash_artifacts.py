"""
Utility functions for hashing artifacts to ensure data integrity.
Implements Constitution Principle V.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
    
    Returns:
        Hex digest of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def hash_directory(
    directory_path: Path,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Hash all files in a directory.
    
    Args:
        directory_path: Path to the directory.
        extensions: Optional list of file extensions to include.
    
    Returns:
        Dictionary mapping relative file paths to their hashes.
    """
    hashes = {}
    
    if not directory_path.exists():
        return hashes
    
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or any(file_path.suffix == ext for ext in extensions):
                rel_path = file_path.relative_to(directory_path)
                hashes[str(rel_path)] = compute_sha256(file_path)
    
    return hashes


def generate_manifest(
    hashes: Dict[str, str],
    directory_path: Path,
    output_path: Optional[Path] = None
) -> Path:
    """
    Generate a manifest file containing hashes.
    
    Args:
        hashes: Dictionary of file paths to hashes.
        directory_path: Base directory path.
        output_path: Optional output path for manifest.
    
    Returns:
        Path to the generated manifest.
    """
    if output_path is None:
        output_path = directory_path / "manifest.json"
    
    manifest = {
        "directory": str(directory_path),
        "file_hashes": hashes,
        "total_files": len(hashes)
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return output_path


def verify_manifest(
    manifest_path: Path,
    directory_path: Path
) -> Dict[str, bool]:
    """
    Verify file hashes against a manifest.
    
    Args:
        manifest_path: Path to the manifest file.
        directory_path: Base directory path.
    
    Returns:
        Dictionary mapping file paths to verification status (True/False).
    """
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    results = {}
    expected_hashes = manifest.get("file_hashes", {})
    
    for rel_path, expected_hash in expected_hashes.items():
        file_path = directory_path / rel_path
        if file_path.exists():
            actual_hash = compute_sha256(file_path)
            results[rel_path] = (actual_hash == expected_hash)
        else:
            results[rel_path] = False
    
    return results


def main():
    """Main entry point for testing hashing utilities."""
    print("Testing Hash Artifacts...")
    
    # Test compute_sha256
    test_file = Path(__file__)
    hash_val = compute_sha256(test_file)
    print(f"Hash of {test_file.name}: {hash_val}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
