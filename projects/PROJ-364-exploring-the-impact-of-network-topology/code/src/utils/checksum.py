"""
Checksum utilities for data integrity verification.
Provides SHA-256 computation and manifest management for the llmXive pipeline.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

from src.logging_config import get_data_ingestion_logger

# Initialize logger specific to data ingestion tasks
logger = get_data_ingestion_logger()


def compute_string_sha256(data: str) -> str:
    """
    Compute the SHA-256 hash of a string.

    Args:
        data: The string to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    if not isinstance(data, str):
        raise TypeError("Input must be a string")
    
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_file_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file by reading it in chunks.
    This handles large files without loading them entirely into memory.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    sha256_hash = hashlib.sha256()
    chunk_size = 8192  # 8KB chunks

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except PermissionError:
        logger.error(f"Permission denied reading file: {path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {path}: {e}")
        raise


def verify_file_checksum(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify the SHA-256 hash of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected SHA-256 hex string.

    Returns:
        True if the hash matches, False otherwise.
    """
    try:
        actual_hash = compute_file_sha256(file_path)
        if not isinstance(expected_hash, str) or len(expected_hash) != 64:
            logger.warning(f"Invalid expected hash format: {expected_hash}")
            return False
        
        match = actual_hash.lower() == expected_hash.lower()
        if not match:
            logger.warning(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {expected_hash}, Got: {actual_hash}"
            )
        return match
    except Exception as e:
        logger.error(f"Verification failed for {file_path}: {e}")
        return False


def generate_checksum_manifest(
    file_paths: list[Union[str, Path]],
    output_path: Optional[Union[str, Path]] = None
) -> Dict[str, str]:
    """
    Generate a manifest (dictionary) of file paths and their SHA-256 hashes.
    Optionally saves the manifest to a JSON file.

    Args:
        file_paths: List of file paths to include in the manifest.
        output_path: Optional path to save the manifest as JSON.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    manifest = {}
    base_dir = Path.cwd()

    for path_str in file_paths:
        path = Path(path_str)
        
        if not path.exists():
            logger.warning(f"Skipping non-existent file in manifest: {path}")
            continue
        
        if not path.is_file():
            logger.warning(f"Skipping non-file path in manifest: {path}")
            continue

        try:
            file_hash = compute_file_sha256(path)
            # Store relative path for portability
            try:
                relative_path = str(path.relative_to(base_dir))
            except ValueError:
                # If path is not under cwd, use absolute path
                relative_path = str(path.absolute())
            
            manifest[relative_path] = file_hash
            logger.debug(f"Added {relative_path} to manifest: {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute hash for {path}: {e}")
            continue

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest saved to {output_file}")

    return manifest


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary mapping file paths to SHA-256 hashes.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest is invalid JSON.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_manifest(manifest_path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None) -> Dict[str, bool]:
    """
    Verify all files listed in a manifest against their stored hashes.

    Args:
        manifest_path: Path to the manifest JSON file.
        base_dir: Optional base directory to resolve relative paths. Defaults to current working directory.

    Returns:
        Dictionary mapping file paths to verification status (True = valid, False = invalid/missing).
    """
    manifest = load_checksum_manifest(manifest_path)
    results = {}
    base = Path(base_dir) if base_dir else Path.cwd()

    for relative_path, expected_hash in manifest.items():
        # Resolve path: if absolute in manifest, use it; else relative to base
        full_path = Path(relative_path) if Path(relative_path).is_absolute() else base / relative_path
        
        if not full_path.exists():
            results[relative_path] = False
            logger.warning(f"File missing during manifest verification: {full_path}")
            continue

        try:
            if verify_file_checksum(full_path, expected_hash):
                results[relative_path] = True
            else:
                results[relative_path] = False
        except Exception:
            results[relative_path] = False

    return results
