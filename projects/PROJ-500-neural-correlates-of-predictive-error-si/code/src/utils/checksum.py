"""
Checksum utility module for data hygiene (FR-009, Constitution Principle III).

Provides functions to compute SHA-256 checksums for files and directories,
save/load checksum manifests, and verify data integrity.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
import logging

# Configure logger
logger = logging.getLogger(__name__)

BLOCK_SIZE = 65536  # 64KB blocks for efficient file reading


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a single file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(BLOCK_SIZE), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()


def compute_directory_checksums(
    directory_path: Path,
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory.
    
    Args:
        directory_path: Path to the directory.
        recursive: If True, traverse subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                    If None, all files are included.
                    
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")
    
    checksums = {}
    
    if recursive:
        iterator = directory_path.rglob('*')
    else:
        iterator = directory_path.glob('*')
    
    for file_path in iterator:
        if file_path.is_file():
            # Filter by extension if specified
            if extensions is not None:
                if file_path.suffix not in extensions:
                    continue
            
            # Skip hidden files
            if file_path.name.startswith('.'):
                continue
                
            try:
                relative_path = file_path.relative_to(directory_path)
                checksum = compute_file_sha256(file_path)
                checksums[str(relative_path)] = checksum
            except PermissionError as e:
                logger.warning(f"Permission denied reading file: {file_path}")
                logger.debug(f"Error details: {e}")
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
    
    return checksums


def save_checksum_manifest(
    checksums: Dict[str, str],
    manifest_path: Path,
    source_directory: Optional[Path] = None
) -> None:
    """
    Save checksums to a JSON manifest file.
    
    Args:
        checksums: Dictionary of relative paths to checksums.
        manifest_path: Path where the manifest will be saved.
        source_directory: Optional source directory path to include in metadata.
    """
    manifest_data = {
        "version": "1.0",
        "algorithm": "sha256",
        "source_directory": str(source_directory) if source_directory else None,
        "checksums": checksums
    }
    
    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Checksum manifest saved to {manifest_path}")


def load_checksum_manifest(manifest_path: Path) -> Tuple[Dict[str, str], Optional[Path]]:
    """
    Load checksums from a JSON manifest file.
    
    Args:
        manifest_path: Path to the manifest file.
        
    Returns:
        Tuple of (checksums dictionary, source_directory path or None).
        
    Raises:
        FileNotFoundError: If the manifest does not exist.
        json.JSONDecodeError: If the manifest is invalid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest_data = json.load(f)
    
    checksums = manifest_data.get("checksums", {})
    source_dir_str = manifest_data.get("source_directory")
    source_directory = Path(source_dir_str) if source_dir_str else None
    
    return checksums, source_directory


def verify_checksums(
    manifest_path: Path,
    base_directory: Optional[Path] = None
) -> Tuple[bool, List[str], List[str]]:
    """
    Verify files against a checksum manifest.
    
    Args:
        manifest_path: Path to the manifest file.
        base_directory: Directory to verify files against. If None, uses the
                        source_directory from the manifest or the manifest's parent.
                        
    Returns:
        Tuple of (all_valid, passed_files, failed_files).
        all_valid: True if all files match their checksums.
        passed_files: List of files that passed verification.
        failed_files: List of files that failed verification or are missing.
    """
    checksums, manifest_source_dir = load_checksum_manifest(manifest_path)
    
    if base_directory is None:
        if manifest_source_dir:
            base_directory = manifest_source_dir
        else:
            base_directory = manifest_path.parent
    
    passed = []
    failed = []
    all_valid = True
    
    for relative_path_str, expected_checksum in checksums.items():
        file_path = base_directory / relative_path_str
        
        if not file_path.exists():
            failed.append(f"MISSING: {relative_path_str}")
            all_valid = False
            logger.warning(f"File missing during verification: {file_path}")
            continue
        
        try:
            actual_checksum = compute_file_sha256(file_path)
            if actual_checksum == expected_checksum:
                passed.append(relative_path_str)
            else:
                failed.append(f"MISMATCH: {relative_path_str}")
                all_valid = False
                logger.error(f"Checksum mismatch for {file_path}")
                logger.error(f"  Expected: {expected_checksum}")
                logger.error(f"  Actual:   {actual_checksum}")
        except Exception as e:
            failed.append(f"ERROR: {relative_path_str} ({str(e)})")
            all_valid = False
            logger.error(f"Error verifying {file_path}: {e}")
    
    return all_valid, passed, failed


def generate_and_save_manifest(
    directory_path: Path,
    manifest_path: Path,
    recursive: bool = True,
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Generate checksums for a directory and save to a manifest.
    
    Args:
        directory_path: Directory to checksum.
        manifest_path: Path to save the manifest.
        recursive: Whether to traverse subdirectories.
        extensions: Optional list of file extensions to include.
                    
    Returns:
        The generated checksums dictionary.
    """
    logger.info(f"Generating checksum manifest for {directory_path}")
    checksums = compute_directory_checksums(directory_path, recursive, extensions)
    save_checksum_manifest(checksums, manifest_path, directory_path)
    logger.info(f"Generated {len(checksums)} checksums")
    return checksums
