"""
Checksum utilities for artifact verification.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest of the SHA256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_file_hash(file_path: Path) -> str:
    """Alias for calculate_sha256."""
    return calculate_sha256(file_path)

def verify_file_hash(file_path: Path, expected_hash: str) -> bool:
    """
    Verify a file's hash against an expected value.
    
    Returns:
        True if hashes match, False otherwise.
    """
    try:
        actual_hash = calculate_sha256(file_path)
        return actual_hash == expected_hash
    except FileNotFoundError:
        return False

def generate_checksum_manifest(directory: Path) -> Dict[str, str]:
    """
    Generate a manifest of checksums for all files in a directory.
    
    Args:
        directory: Path to the directory.
        
    Returns:
        Dictionary mapping filenames to their SHA256 hashes.
    """
    manifest = {}
    if directory.exists():
        for f in directory.iterdir():
            if f.is_file() and f.name != ".gitkeep":
                manifest[f.name] = calculate_sha256(f)
    return manifest

def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        Dictionary of checksums.
        
    Raises:
        FileNotFoundError: If manifest does not exist.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_manifest(directory: Path, manifest_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify all files in a directory against a manifest.
    
    Returns:
        Tuple of (all_valid, list_of_errors).
    """
    errors = []
    try:
        manifest = load_checksum_manifest(manifest_path)
    except FileNotFoundError as e:
        return False, [str(e)]
    except json.JSONDecodeError as e:
        return False, [f"Invalid manifest JSON: {e}"]

    for filename, expected_hash in manifest.items():
        file_path = directory / filename
        if not file_path.exists():
            errors.append(f"Missing file: {filename}")
            continue
        
        actual_hash = calculate_sha256(file_path)
        if actual_hash != expected_hash:
            errors.append(f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
    
    return len(errors) == 0, errors

def get_checksum_report(directory: Path) -> str:
    """
    Generate a text report of checksums for files in a directory.
    """
    report_lines = []
    if directory.exists():
        for f in sorted(directory.iterdir()):
            if f.is_file() and f.name != ".gitkeep":
                h = calculate_sha256(f)
                report_lines.append(f"{f.name}: {h}")
    return "\n".join(report_lines)

def main():
    """CLI entry point for checksum utilities."""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python checksums.py <command> [args]")
        print("Commands: verify <file> <expected_hash>, generate <dir>")
        return 1
    
    command = sys.argv[1]
    
    if command == "verify":
        if len(sys.argv) < 4:
            print("Usage: verify <file> <expected_hash>")
            return 1
        file_path = Path(sys.argv[2])
        expected = sys.argv[3]
        if verify_file_hash(file_path, expected):
            print(f"OK: {file_path}")
            return 0
        else:
            print(f"FAIL: {file_path}")
            return 1
    
    elif command == "generate":
        if len(sys.argv) < 3:
            print("Usage: generate <directory>")
            return 1
        dir_path = Path(sys.argv[2])
        manifest = generate_checksum_manifest(dir_path)
        print(json.dumps(manifest, indent=2))
        return 0
    
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
