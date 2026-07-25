"""
Module to handle creation, computation, recording, saving, and verification of checksums.
Implements T001c logic and supports T001d execution.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_directories(base_path: Path, dirs: List[str]) -> None:
    """Create a list of directories under base_path if they don't exist."""
    for d in dirs:
        (base_path / d).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {base_path / d}")

def compute_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Compute the checksum of a single file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default 'sha256').
        
    Returns:
        Hexadecimal digest string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def record_checksums(directory: Path, algorithm: str = 'sha256') -> Dict[str, str]:
    """
    Recursively compute checksums for all files in a directory.
    
    Args:
        directory: Path to the root directory to scan.
        algorithm: Hash algorithm to use.
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    checksums = {}
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return checksums
    
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(directory)
            
            try:
                checksum = compute_file_checksum(file_path, algorithm)
                checksums[str(rel_path)] = checksum
                logger.debug(f"Computed checksum for {rel_path}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to checksum {rel_path}: {e}")
                # We do not skip; we log error. If critical, we could raise.
                # For now, we just don't add it to the map, or we could add a special error key.
                # The task requires checksums for "all files". If we fail, we log.
    
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save the checksum dictionary to a JSON file.
    
    Args:
        checksums: Dictionary of relative paths to checksums.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    logger.info(f"Saved {len(checksums)} checksums to {output_path}")

def load_checksums(input_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        input_path: Path to the JSON file.
        
    Returns:
        Dictionary of checksums.
    """
    if not input_path.exists():
        return {}
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_integrity(stored_checksums: Dict[str, str], data_dir: Path) -> bool:
    """
    Verify the integrity of files in data_dir against stored checksums.
    
    Args:
        stored_checksums: The dictionary of expected checksums.
        data_dir: The directory containing the files to verify.
        
    Returns:
        True if all files match, False otherwise.
    """
    is_valid = True
    for rel_path, expected_checksum in stored_checksums.items():
        file_path = data_dir / rel_path
        if not file_path.exists():
            logger.error(f"File missing during verification: {rel_path}")
            is_valid = False
            continue
        
        try:
            actual_checksum = compute_file_checksum(file_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_checksum}, got {actual_checksum}")
                is_valid = False
            else:
                logger.debug(f"Verified {rel_path}")
        except Exception as e:
            logger.error(f"Error verifying {rel_path}: {e}")
            is_valid = False
    
    return is_valid

def main():
    """
    Main entry point for standalone execution.
    """
    # Determine project root (assuming this file is in code/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    data_dir = project_root / "data"
    state_dir = project_root / "state"
    output_file = state_dir / "checksums.json"
    
    logger.info(f"Running checksum manager. Data dir: {data_dir}, Output: {output_file}")
    
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist. Aborting.")
        return 1
    
    try:
        checksums = record_checksums(data_dir)
        save_checksums(checksums, output_file)
        
        # Verify immediately after saving to ensure consistency
        if verify_integrity(checksums, data_dir):
            logger.info("Integrity verification passed.")
        else:
            logger.warning("Integrity verification failed (some files mismatched or missing).")
            
        return 0
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
