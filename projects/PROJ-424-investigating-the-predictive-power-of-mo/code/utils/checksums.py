"""
Checksum utilities for artifact verification in the research pipeline.

Provides functions to compute, verify, and manage file checksums
to ensure data integrity and reproducibility.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime


ALGORITHM = "sha256"
CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def compute_file_hash(file_path: Path, algorithm: str = ALGORITHM) -> str:
    """
    Compute the cryptographic hash of a file.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the file hash
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            hasher.update(chunk)
    
    return hasher.hexdigest()


def verify_file_hash(file_path: Path, expected_hash: str, algorithm: str = ALGORITHM) -> bool:
    """
    Verify that a file's hash matches the expected value.
    
    Args:
        file_path: Path to the file to verify
        expected_hash: Expected hash value (hex string)
        algorithm: Hash algorithm to use
        
    Returns:
        True if the hash matches, False otherwise
    """
    try:
        actual_hash = compute_file_hash(file_path, algorithm)
        return actual_hash.lower() == expected_hash.lower()
    except FileNotFoundError:
        return False


def generate_checksum_manifest(
    file_paths: List[Path],
    output_path: Optional[Path] = None,
    algorithm: str = ALGORITHM,
) -> Dict[str, str]:
    """
    Generate a manifest of file checksums.
    
    Args:
        file_paths: List of file paths to include in the manifest
        output_path: Optional path to write the manifest JSON
        algorithm: Hash algorithm to use
        
    Returns:
        Dictionary mapping file paths to their checksums
    """
    manifest: Dict[str, str] = {}
    
    for file_path in file_paths:
        if file_path.exists():
          try:
              checksum = compute_file_hash(file_path, algorithm)
              manifest[str(file_path)] = {
                  "hash": checksum,
                  "algorithm": algorithm,
                  "size_bytes": file_path.stat().st_size,
                  "timestamp": datetime.utcnow().isoformat()
              }
          except (PermissionError, OSError) as e:
              manifest[str(file_path)] = {
                  "error": f"Could not compute hash: {str(e)}"
              }
        else:
          manifest[str(file_path)] = {
              "error": "File not found"
          }
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(manifest, f, indent=2)
    
    return manifest


def load_checksum_manifest(manifest_path: Path) -> Dict[str, Dict]:
    """
    Load a checksum manifest from a JSON file.
    
    Args:
        manifest_path: Path to the manifest JSON file
        
    Returns:
        Dictionary containing the manifest data
        
    Raises:
        FileNotFoundError: If the manifest file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    with open(manifest_path, "r") as f:
        return json.load(f)


def verify_manifest(manifest_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify all files against a checksum manifest.
    
    Args:
        manifest_path: Path to the manifest JSON file
        
    Returns:
        Tuple of (all_valid, list_of_failed_files)
    """
    manifest = load_checksum_manifest(manifest_path)
    failed_files: List[str] = []
    
    for file_path_str, metadata in manifest.items():
        if "error" in metadata:
            failed_files.append(f"{file_path_str}: {metadata['error']}")
            continue
        
        file_path = Path(file_path_str)
        expected_hash = metadata.get("hash")
        algorithm = metadata.get("algorithm", ALGORITHM)
        
        if not file_path.exists():
            failed_files.append(f"{file_path_str}: File not found")
            continue
        
        if not verify_file_hash(file_path, expected_hash, algorithm):
            failed_files.append(f"{file_path_str}: Hash mismatch")
    
    return len(failed_files) == 0, failed_files


def get_checksum_report(file_paths: List[Path], algorithm: str = ALGORITHM) -> str:
    """
    Generate a human-readable report of file checksums.
    
    Args:
        file_paths: List of file paths to include
        algorithm: Hash algorithm to use
        
    Returns:
        Formatted string report
    """
    lines = [
        f"Checksum Report ({algorithm.upper()})",
        "=" * 50,
        f"Generated: {datetime.utcnow().isoformat()}",
        f"Files: {len(file_paths)}",
        "-" * 50,
    ]
    
    for file_path in file_paths:
        if file_path.exists():
            try:
                checksum = compute_file_hash(file_path, algorithm)
                size = file_path.stat().st_size
                lines.append(f"{file_path.name:<30} {checksum} ({size:,} bytes)")
            except Exception as e:
                lines.append(f"{file_path.name:<30} ERROR: {str(e)}")
        else:
            lines.append(f"{file_path.name:<30} NOT FOUND")
    
    return "\n".join(lines)
