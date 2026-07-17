"""
Setup directory structure and checksum utilities for data integrity.

This module creates the required data directories (data/raw, data/processed)
and provides utilities to compute file checksums (SHA-256) for data integrity
verification. This is a prerequisite for T009 and T010.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict

# Import logging utility from the project's existing API
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

logger = get_logger(__name__)


def create_directories() -> Dict[str, Path]:
    """
    Create the required data directory structure if they do not exist.
    
    Creates:
        - data/raw/
        - data/processed/
        - data/interim/ (optional, for intermediate data)
    
    Returns:
        Dict mapping directory names to their Path objects.
    """
    root = get_project_root()
    data_root = root / "data"
    
    directories = {
        "raw": data_root / "raw",
        "processed": data_root / "processed",
        "interim": data_root / "interim",
        "figures": data_root / "figures",
    }
    
    created = []
    for name, path in directories.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            created.append(name)
        else:
            logger.debug(f"Directory already exists: {path}")
    
    if created:
        logger.info(f"Created {len(created)} new directories.")
    else:
        logger.info("All required directories already exist.")
        
    return directories


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
    
    Returns:
        Hexadecimal string of the checksum.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise
    
    return hash_func.hexdigest()


def generate_checksum_manifest(
    directory: Path,
    output_path: Optional[Path] = None,
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Generate a manifest of checksums for all files in a directory.
    
    Recursively scans the directory and computes checksums for all files.
    
    Args:
        directory: Path to the directory to scan.
        output_path: Optional path to write the JSON manifest. If None, 
                    the manifest is not written to disk.
        algorithm: Hash algorithm to use.
    
    Returns:
        Dict mapping relative file paths to their checksums.
    
    Raises:
        NotADirectoryError: If the provided path is not a directory.
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")
    
    manifest = {}
    file_count = 0
    
    logger.info(f"Scanning directory for checksums: {directory}")
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            # Skip hidden files and temporary files
            if file_path.name.startswith(".") or file_path.name.endswith(".tmp"):
                continue
            
            try:
                checksum = compute_file_checksum(file_path, algorithm)
                rel_path = str(file_path.relative_to(directory))
                manifest[rel_path] = checksum
                file_count += 1
            except Exception as e:
                logger.warning(f"Failed to checksum {file_path}: {e}")
    
    logger.info(f"Generated checksum manifest for {file_count} files.")
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        logger.info(f"Wrote checksum manifest to: {output_path}")
    
    return manifest


def verify_checksums(
    manifest_path: Path,
    base_directory: Optional[Path] = None,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify file checksums against a manifest.
    
    Args:
        manifest_path: Path to the JSON manifest file.
        base_directory: Base directory for relative paths in the manifest.
                       Defaults to the parent of the manifest file.
        algorithm: Hash algorithm used for the checksums.
    
    Returns:
        True if all files match their checksums, False otherwise.
    """
    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        return False
    
    if base_directory is None:
        base_directory = manifest_path.parent
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    all_valid = True
    total_files = len(manifest)
    valid_count = 0
    
    logger.info(f"Verifying {total_files} files against manifest...")
    
    for rel_path, expected_checksum in manifest.items():
        file_path = base_directory / rel_path
        
        if not file_path.exists():
            logger.error(f"File missing: {file_path}")
            all_valid = False
            continue
        
        try:
            actual_checksum = compute_file_checksum(file_path, algorithm)
            if actual_checksum == expected_checksum:
                valid_count += 1
            else:
                logger.error(f"Checksum mismatch for {file_path}: "
                           f"expected {expected_checksum}, got {actual_checksum}")
                all_valid = False
        except Exception as e:
            logger.error(f"Error verifying {file_path}: {e}")
            all_valid = False
    
    logger.info(f"Verification complete: {valid_count}/{total_files} files valid.")
    return all_valid


def main() -> int:
    """
    Main entry point for the setup directories and checksum utility.
    
    This function:
    1. Creates the required data directories.
    2. Generates a checksum manifest for any existing files in the data directory.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Configure logging
        configure_root_logger()
        
        logger.info("Starting data directory setup and checksum generation...")
        
        # Create directories
        directories = create_directories()
        
        # Generate checksum manifest for the entire data directory
        data_root = get_project_root() / "data"
        manifest_path = data_root / "checksum_manifest.json"
        
        if data_root.exists():
            manifest = generate_checksum_manifest(data_root, manifest_path)
            logger.info(f"Checksum manifest contains {len(manifest)} entries.")
        else:
            logger.warning("Data root directory does not exist. Skipping checksum generation.")
        
        logger.info("Setup complete.")
        return 0
        
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
