"""
Validation utilities for checksum verification and file integrity checks.

Implements Constitution Principle III: Data integrity and reproducibility.
"""
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from logging_config import get_logger

logger = get_logger(__name__)

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of the file checksum
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def verify_file_integrity(
    file_path: Path, 
    expected_checksum: str, 
    actual_checksum: Optional[str] = None
) -> bool:
    """
    Verify file integrity by comparing checksums.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        actual_checksum: Optional pre-computed checksum (if None, will compute)
        
    Returns:
        True if checksums match, False otherwise
    """
    if actual_checksum is None:
        actual_checksum = compute_file_checksum(file_path)
    
    is_valid = actual_checksum == expected_checksum
    
    if not is_valid:
        logger.error(f"Checksum mismatch for {file_path}")
        logger.error(f"Expected: {expected_checksum}")
        logger.error(f"Actual:   {actual_checksum}")
    else:
        logger.debug(f"Checksum verified for {file_path}")
    
    return is_valid

def create_manifest(directory: Path, patterns: Optional[list] = None) -> Dict[str, str]:
    """
    Create a manifest of files in a directory with their checksums.
    
    Args:
        directory: Directory to scan
        patterns: Optional list of filename patterns to include
        
    Returns:
        Dictionary mapping relative paths to checksums
    """
    manifest = {}
    patterns = patterns or ['*.json', '*.csv', '*.txt', '*.dat']
    
    import fnmatch
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Check if file matches any pattern
            if patterns:
                if not any(fnmatch.fnmatch(file, pattern) for pattern in patterns):
                    continue
            
            file_path = Path(root) / file
            rel_path = file_path.relative_to(directory)
            
            try:
                checksum = compute_file_checksum(file_path)
                manifest[str(rel_path)] = checksum
            except Exception as e:
                logger.warning(f"Could not compute checksum for {file_path}: {e}")
    
    return manifest

def verify_manifest(manifest_path: Path) -> Tuple[bool, Dict[str, str]]:
    """
    Verify files against a manifest.
    
    Args:
        manifest_path: Path to the manifest JSON file
        
    Returns:
        Tuple of (all_valid, failed_files) where failed_files maps path to error
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    all_valid = True
    failed_files = {}
    
    base_dir = manifest_path.parent
    
    for rel_path, expected_checksum in manifest.items():
        file_path = base_dir / rel_path
        
        if not file_path.exists():
            all_valid = False
            failed_files[rel_path] = "File not found"
            continue
        
        actual_checksum = compute_file_checksum(file_path)
        
        if actual_checksum != expected_checksum:
            all_valid = False
            failed_files[rel_path] = f"Checksum mismatch: expected {expected_checksum}, got {actual_checksum}"
    
    return all_valid, failed_files

def check_file_age(file_path: Path, max_age_hours: float) -> bool:
    """
    Check if a file is newer than a specified age.
    
    Args:
        file_path: Path to the file
        max_age_hours: Maximum age in hours
        
    Returns:
        True if file is newer than max_age_hours, False otherwise
    """
    if not file_path.exists():
        return False
    
    file_mtime = file_path.stat().st_mtime
    current_time = time.time()
    
    age_seconds = current_time - file_mtime
    age_hours = age_seconds / 3600
    
    is_fresh = age_hours <= max_age_hours
    
    if not is_fresh:
        logger.warning(f"File {file_path} is {age_hours:.2f} hours old (max: {max_age_hours})")
    
    return is_fresh

def save_manifest(manifest: Dict[str, str], output_path: Path) -> Path:
    """
    Save a manifest to a JSON file.
    
    Args:
        manifest: Dictionary mapping paths to checksums
        output_path: Path to save the manifest
        
    Returns:
        Path to the saved manifest
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest saved to {output_path}")
    return output_path

def main():
    """
    Main entry point for validation utilities demonstration.
    """
    setup_logging()
    
    # Example usage
    sample_dir = Path("data/raw")
    if sample_dir.exists():
        logger.info(f"Creating manifest for {sample_dir}")
        manifest = create_manifest(sample_dir)
        manifest_path = sample_dir / "manifest.json"
        save_manifest(manifest, manifest_path)
        
        logger.info(f"Verifying manifest {manifest_path}")
        is_valid, failures = verify_manifest(manifest_path)
        
        if is_valid:
            logger.info("All files verified successfully")
        else:
            logger.error(f"Verification failed for {len(failures)} files")
            for path, error in failures.items():
                logger.error(f"  {path}: {error}")
    else:
        logger.warning(f"Directory {sample_dir} does not exist")

if __name__ == "__main__":
    main()
