import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
    
    Returns:
        Hexadecimal checksum string
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def verify_file_integrity(file_path: Path, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify a file's integrity against an expected checksum.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum string
        algorithm: Hash algorithm to use
    
    Returns:
        True if checksum matches, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File not found for integrity check: {file_path}")
        return False
    
    actual_checksum = compute_file_checksum(file_path, algorithm)
    if actual_checksum.lower() != expected_checksum.lower():
        logger.error(f"Checksum mismatch for {file_path}. Expected: {expected_checksum}, Got: {actual_checksum}")
        return False
    
    logger.debug(f"Integrity check passed for {file_path}")
    return True

def create_manifest(file_paths: List[Path], output_path: Path) -> Dict[str, str]:
    """
    Create a manifest file containing checksums for a list of files.
    
    Args:
        file_paths: List of file paths to include in manifest
        output_path: Path to save the manifest JSON
    
    Returns:
        Dictionary mapping file paths to checksums
    """
    manifest = {}
    for fp in file_paths:
        if fp.exists():
            manifest[str(fp)] = compute_file_checksum(fp)
        else:
            logger.warning(f"File not found for manifest: {fp}")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest created at {output_path}")
    return manifest

def verify_manifest(manifest_path: Path) -> bool:
    """
    Verify all files listed in a manifest against their stored checksums.
    
    Args:
        manifest_path: Path to the manifest JSON
    
    Returns:
        True if all files verify, False otherwise
    """
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return False
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    all_valid = True
    for file_str, expected_checksum in manifest.items():
        file_path = Path(file_str)
        if not verify_file_integrity(file_path, expected_checksum):
            all_valid = False
    
    return all_valid

def check_file_age(file_path: Path, max_age_hours: float = 24.0) -> bool:
    """
    Check if a file is older than a specified age.
    
    Args:
        file_path: Path to the file
        max_age_hours: Maximum age in hours
    
    Returns:
        True if file is within age limit, False otherwise
    """
    if not file_path.exists():
        return False
    
    mtime = file_path.stat().st_mtime
    current_time = time.time()
    age_seconds = current_time - mtime
    age_hours = age_seconds / 3600.0
    
    is_fresh = age_hours <= max_age_hours
    if not is_fresh:
        logger.warning(f"File {file_path} is older than {max_age_hours} hours ({age_hours:.2f}h)")
    
    return is_fresh

def save_manifest(manifest: Dict[str, str], output_path: Path):
    """
    Save a manifest dictionary to a JSON file.
    
    Args:
        manifest: Dictionary of file paths to checksums
        output_path: Path to save the manifest
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {output_path}")

def main():
    """Test validation utilities."""
    logger.info("Validation Utils Module Started")
    # Example: compute checksum of this file
    # checksum = compute_file_checksum(Path(__file__))
    # print(f"Checksum: {checksum}")

if __name__ == "__main__":
    main()