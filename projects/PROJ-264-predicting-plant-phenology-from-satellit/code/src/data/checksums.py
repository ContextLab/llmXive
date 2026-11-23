"""
Checksum utilities for data integrity verification.

This module provides functions to compute, save, load, and verify
file and directory checksums (SHA-256) for the project's data directories.
"""
import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from src.lib.utils import setup_logging

# Initialize logger
logger = setup_logging(__name__)

# Default checksum file name
CHECKSUM_FILE = "checksums.json"

# Patterns to exclude from checksum calculation
EXCLUDE_PATTERNS = {
    ".gitkeep",
    ".DS_Store",
    "checksums.json",
    ".pyc",
    "__pycache__"
}

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a single file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal checksum string
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def compute_directory_checksums(
    directory: Path,
    algorithm: str = "sha256",
    exclude_patterns: Optional[set] = None
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory recursively.
    
    Args:
        directory: Path to the directory
        algorithm: Hash algorithm to use
        exclude_patterns: Set of filename patterns to exclude
        
    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    if exclude_patterns is None:
        exclude_patterns = EXCLUDE_PATTERNS
        
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
        
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    checksums = {}
    exclude_patterns = set(exclude_patterns)
    
    for root, _, files in os.walk(directory):
        root_path = Path(root)
        for filename in files:
            # Skip excluded patterns
            if any(filename.endswith(pattern) or pattern in filename 
                   for pattern in exclude_patterns):
                continue
                
            file_path = root_path / filename
            rel_path = file_path.relative_to(directory)
            
            try:
                checksum = compute_file_checksum(file_path, algorithm)
                checksums[str(rel_path)] = checksum
            except (FileNotFoundError, IOError) as e:
                logger.warning(f"Could not compute checksum for {file_path}: {e}")
    
    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary of checksums to save
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    metadata = {
        "created_at": datetime.utcnow().isoformat(),
        "algorithm": "sha256",
        "checksums": checksums
    }
    
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"Saved checksums to {output_path}")

def load_checksums(checksum_path: Path) -> Dict[str, str]:
    """
    Load checksums from a JSON file.
    
    Args:
        checksum_path: Path to the checksum JSON file
        
    Returns:
        Dictionary of checksums
        
    Raises:
        FileNotFoundError: If the checksum file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    """
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
    
    with open(checksum_path, 'r') as f:
        data = json.load(f)
    
    return data.get("checksums", {})

def verify_checksums(
    directory: Path,
    stored_checksums: Dict[str, str],
    exclude_patterns: Optional[set] = None
) -> Dict[str, bool]:
    """
    Verify files against stored checksums.
    
    Args:
        directory: Directory containing the files to verify
        stored_checksums: Dictionary of expected checksums
        exclude_patterns: Patterns to exclude from verification
        
    Returns:
        Dictionary mapping file paths to verification status (True = valid)
    """
    results = {}
    
    # Check all stored files
    for rel_path, expected_checksum in stored_checksums.items():
        file_path = directory / rel_path
        
        if not file_path.exists():
            results[rel_path] = False
            logger.error(f"Missing file: {rel_path}")
            continue
        
        try:
            actual_checksum = compute_file_checksum(file_path)
            is_valid = actual_checksum == expected_checksum
            results[rel_path] = is_valid
            
            if not is_valid:
                logger.error(f"Checksum mismatch for {rel_path}")
        except Exception as e:
            results[rel_path] = False
            logger.error(f"Error verifying {rel_path}: {e}")
    
    return results

def generate_checksums_for_directories(
    directories: List[Path],
    output_dir: Optional[Path] = None
) -> Dict[str, Dict[str, str]]:
    """
    Generate checksums for multiple directories and save them.
    
    Args:
        directories: List of directories to checksum
        output_dir: Directory to save checksum files (default: same as input dirs)
        
    Returns:
        Dictionary mapping directory paths to their checksums
    """
    if output_dir is None:
        output_dir = Path(".")
        
    all_checksums = {}
    
    for directory in directories:
        if not directory.exists():
            logger.warning(f"Skipping non-existent directory: {directory}")
            continue
        
        logger.info(f"Generating checksums for {directory}")
        checksums = compute_directory_checksums(directory)
        
        # Save checksums
        checksum_file = output_dir / directory.name / CHECKSUM_FILE
        save_checksums(checksums, checksum_file)
        
        all_checksums[str(directory)] = checksums
    
    return all_checksums

def verify_all_checksums(
    directories: List[Path],
    checksum_dir: Optional[Path] = None
) -> bool:
    """
    Verify all files in directories against their stored checksums.
    
    Args:
        directories: List of directories to verify
        checksum_dir: Directory containing checksum files (default: same as input dirs)
        
    Returns:
        True if all checksums are valid, False otherwise
    """
    if checksum_dir is None:
        checksum_dir = Path(".")
        
    all_valid = True
    
    for directory in directories:
        if not directory.exists():
            logger.warning(f"Directory not found, skipping: {directory}")
            continue
        
        checksum_file = checksum_dir / directory.name / CHECKSUM_FILE
        
        if not checksum_file.exists():
            logger.warning(f"No checksum file found for {directory}")
            continue
        
        logger.info(f"Verifying checksums for {directory}")
        
        try:
            stored_checksums = load_checksums(checksum_file)
            results = verify_checksums(directory, stored_checksums)
            
            if not all(results.values()):
                all_valid = False
                failed = [k for k, v in results.items() if not v]
                logger.error(f"Verification failed for {len(failed)} files in {directory}")
            else:
                logger.info(f"All {len(results)} files in {directory} verified successfully")
                
        except Exception as e:
            logger.error(f"Error verifying {directory}: {e}")
            all_valid = False
    
    return all_valid

def main() -> int:
    """
    Main entry point for the checksum script.
    
    Usage:
        python -m src.data.checksums generate <dir1> [dir2 ...]
        python -m src.data.checksums verify <dir1> [dir2 ...]
        
    Returns:
        0 on success, 1 on failure
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python -m src.data.checksums <generate|verify> <dir1> [dir2 ...]")
        return 1
    
    command = sys.argv[1]
    dirs = [Path(d) for d in sys.argv[2:]]
    
    if command == "generate":
        generate_checksums_for_directories(dirs)
        return 0
    elif command == "verify":
        success = verify_all_checksums(dirs)
        return 0 if success else 1
    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
