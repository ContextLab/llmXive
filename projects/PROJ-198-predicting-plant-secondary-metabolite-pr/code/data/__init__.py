"""
Data module initialization.

This module provides utilities for managing the data directory structure
and verifying file integrity via checksums.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional, Tuple

from config import get_data_path, get_config
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Standard directory structure relative to the data root
DATA_DIRS = [
    "raw",
    "raw/genomes",
    "raw/metabolites",
    "raw/phylogeny",
    "interim",
    "processed",
    "figures",
    "cache",
]

# Checksum manifest filename
CHECKSUM_MANIFEST = "checksums.json"


def ensure_data_structure() -> Path:
    """
    Create the standard data directory structure if it doesn't exist.
    
    Returns:
        Path: The root data directory path.
    """
    data_root = get_data_path()
    logger.info(f"Ensuring data directory structure at: {data_root}")
    
    if not data_root.exists():
        data_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created root data directory: {data_root}")
    
    for subdir in DATA_DIRS:
        dir_path = data_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created subdirectory: {dir_path}")
    
    return data_root


def calculate_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        str: Hexadecimal checksum string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot calculate checksum: file not found at {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating checksum for {file_path}: {e}")
        raise


def save_checksums(manifest_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Calculate and save checksums for all files in the data directory.
    
    Args:
        manifest_path: Optional path for the manifest file. Defaults to 
                     {data_root}/checksums.json.
                     
    Returns:
        Dict[str, str]: Dictionary mapping relative file paths to checksums.
    """
    data_root = get_data_path()
    ensure_data_structure()
    
    if manifest_path is None:
        manifest_path = data_root / CHECKSUM_MANIFEST
    
    checksums: Dict[str, str] = {}
    files_processed = 0
    
    logger.info(f"Scanning {data_root} for checksums...")
    
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            # Skip the manifest itself to avoid self-referential issues
            if file_path == manifest_path:
                continue
            
            try:
                relative_path = str(file_path.relative_to(data_root))
                checksum = calculate_checksum(file_path)
                checksums[relative_path] = checksum
                files_processed += 1
                logger.debug(f"Checksummed: {relative_path}")
            except Exception as e:
                logger.warning(f"Skipped file {file_path} due to error: {e}")
    
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Saved checksum manifest to {manifest_path} ({files_processed} files)")
    except Exception as e:
        logger.error(f"Failed to save checksum manifest: {e}")
        raise
    
    return checksums


def verify_checksums(manifest_path: Optional[Path] = None) -> Tuple[bool, Dict[str, str]]:
    """
    Verify file integrity against stored checksums.
    
    Args:
        manifest_path: Optional path for the manifest file. Defaults to 
                     {data_root}/checksums.json.
                     
    Returns:
        Tuple[bool, Dict[str, str]]: 
            - True if all verifications passed, False otherwise.
            - Dictionary of failed files with error messages.
    """
    data_root = get_data_path()
    
    if manifest_path is None:
        manifest_path = data_root / CHECKSUM_MANIFEST
    
    if not manifest_path.exists():
        logger.warning(f"No checksum manifest found at {manifest_path}. "
                     "Run `save_checksums()` first.")
        return False, {"manifest": "Checksum manifest not found"}
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            stored_checksums = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum manifest: {e}")
        return False, {"manifest": f"Invalid JSON: {e}"}
    
    failures: Dict[str, str] = {}
    verified_count = 0
    
    logger.info(f"Verifying checksums against {manifest_path}...")
    
    for relative_path, expected_checksum in stored_checksums.items():
        file_path = data_root / relative_path
        
        if not file_path.exists():
            failures[relative_path] = "File not found"
            logger.warning(f"Verification failed (missing): {relative_path}")
            continue
        
        try:
            actual_checksum = calculate_checksum(file_path)
            if actual_checksum == expected_checksum:
                verified_count += 1
                logger.debug(f"Verified: {relative_path}")
            else:
                failures[relative_path] = f"Checksum mismatch (expected: {expected_checksum}, got: {actual_checksum})"
                logger.error(f"Verification failed (mismatch): {relative_path}")
        except Exception as e:
            failures[relative_path] = str(e)
            logger.error(f"Verification error for {relative_path}: {e}")
    
    if not failures:
        logger.info(f"Verification successful: {verified_count} files checked.")
        return True, {}
    else:
        logger.warning(f"Verification completed with {len(failures)} failures.")
        return False, failures


def initialize() -> Path:
    """
    Main entry point to initialize the data directory structure and 
    generate initial checksums if the manifest doesn't exist.
    
    Returns:
        Path: The root data directory.
    """
    data_root = ensure_data_structure()
    manifest_path = data_root / CHECKSUM_MANIFEST
    
    if not manifest_path.exists():
        logger.info("No existing checksum manifest found. Generating initial manifest...")
        save_checksums(manifest_path)
    else:
        logger.info("Existing checksum manifest found. Skipping initial generation.")
        
    return data_root