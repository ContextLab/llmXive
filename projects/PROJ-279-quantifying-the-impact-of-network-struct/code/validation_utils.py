import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

from logging_config import get_logger

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_file_integrity(file_path: Path, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify a file's checksum against an expected value.
    Returns True if match, False otherwise.
    Raises exception on file not found.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = compute_file_checksum(file_path, algorithm)
    if actual_checksum != expected_checksum:
        logger.error(f"Integrity check failed for {file_path}. "
                     f"Expected: {expected_checksum}, Got: {actual_checksum}")
        return False
    
    logger.info(f"Integrity check passed for {file_path}")
    return True

def create_manifest(file_paths: List[Path], output_path: Path) -> Dict[str, str]:
    """
    Create a manifest (dictionary of file path -> checksum).
    """
    manifest = {}
    for path in file_paths:
        if path.exists():
            manifest[str(path)] = compute_file_checksum(path)
        else:
            logger.warning(f"Skipping non-existent file in manifest: {path}")
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest created at {output_path}")
    return manifest

def verify_manifest(manifest_path: Path, root_dir: Optional[Path] = None) -> bool:
    """
    Verify all files in a manifest against their stored checksums.
    Returns True if all pass, False otherwise.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    all_valid = True
    for file_str, expected_checksum in manifest.items():
        file_path = Path(file_str)
        if root_dir and not file_path.is_absolute():
            file_path = root_dir / file_path
        
        if not file_path.exists():
            logger.error(f"File missing in verification: {file_path}")
            all_valid = False
            continue
        
        if not verify_file_integrity(file_path, expected_checksum):
            all_valid = False
    
    if all_valid:
        logger.info("Manifest verification passed.")
    else:
        logger.error("Manifest verification failed.")
    
    return all_valid

def check_file_age(file_path: Path, max_age_hours: float = 24.0) -> bool:
    """
    Check if a file is older than max_age_hours.
    Returns True if file is fresh (age <= max_age), False if too old.
    """
    if not file_path.exists():
        return False
    
    mtime = os.path.getmtime(file_path)
    age_seconds = time.time() - mtime
    age_hours = age_seconds / 3600
    
    if age_hours > max_age_hours:
        logger.warning(f"File {file_path} is older than {max_age_hours} hours ({age_hours:.1f}h).")
        return False
    
    return True

def save_manifest(manifest: Dict[str, str], output_path: Path) -> Path:
    """
    Save a manifest dictionary to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {output_path}")
    return output_path

def main():
    """
    Entry point for basic validation utils demonstration.
    """
    logger.info("Validation Utils module loaded.")
    return 0
