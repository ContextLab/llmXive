import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from loguru import logger

def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    
    return sha256_hash.hexdigest()

def generate_manifest(
    file_paths: List[Union[str, Path]],
    output_path: Union[str, Path],
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a JSON manifest containing SHA-256 hashes for a list of files.

    Args:
        file_paths: List of file paths to hash.
        output_path: Path where the manifest JSON will be written.
        exclude_patterns: Optional list of glob patterns to exclude (not implemented in core logic, 
                          but structure prepared for future expansion).

    Returns:
        Dictionary containing the manifest data.
    """
    manifest = {
        "files": {},
        "generated_at": str(Path(output_path).parent), # Placeholder for timestamp if needed
        "algorithm": "sha256"
    }

    output_path = Path(output_path)
    
    for file_path in file_paths:
        file_path = Path(file_path)
        if not file_path.exists():
            logger.warning(f"Skipping non-existent file in manifest: {file_path}")
            continue
        if file_path.is_dir():
            logger.warning(f"Skipping directory in manifest: {file_path}")
            continue

        try:
            file_hash = calculate_sha256(file_path)
            manifest["files"][str(file_path)] = {
                "hash": file_hash,
                "size_bytes": file_path.stat().st_size
            }
            logger.debug(f"Hashed file: {file_path} -> {file_hash[:16]}...")
        except Exception as e:
            logger.error(f"Failed to hash file {file_path}: {e}")
            raise

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest written to: {output_path}")
    return manifest

def verify_manifest(
    manifest_path: Union[str, Path],
    base_dir: Optional[Union[str, Path]] = None
) -> bool:
    """
    Verify the integrity of files listed in a manifest against their stored hashes.

    Args:
        manifest_path: Path to the manifest JSON file.
        base_dir: Optional base directory to resolve relative paths in the manifest.

    Returns:
        True if all files match their hashes, False otherwise.

    Raises:
        FileNotFoundError: If the manifest file or any listed file is missing.
        json.JSONDecodeError: If the manifest is malformed.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files_to_check = manifest.get("files", {})
    if not files_to_check:
        logger.warning("Manifest contains no files to verify.")
        return True

    all_valid = True

    for relative_path, metadata in files_to_check.items():
        expected_hash = metadata.get("hash")
        
        # Resolve path relative to base_dir if provided, otherwise use absolute
        if base_dir:
            full_path = Path(base_dir) / relative_path
        else:
            full_path = Path(relative_path)

        if not full_path.exists():
            logger.error(f"File missing during verification: {full_path}")
            all_valid = False
            continue

        try:
            actual_hash = calculate_sha256(full_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {full_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                logger.debug(f"Hash verified: {full_path}")
        except Exception as e:
            logger.error(f"Error verifying {full_path}: {e}")
            all_valid = False

    if all_valid:
        logger.info("Manifest verification successful: all hashes match.")
    else:
        logger.error("Manifest verification failed: some hashes do not match.")
    
    return all_valid

def log_hash_to_file(file_path: Union[str, Path], log_path: Union[str, Path]) -> None:
    """
    Calculate the hash of a file and append it to a log file in a standard format.
    Used for pipeline logs to record artifact integrity.

    Args:
        file_path: Path to the file to hash.
        log_path: Path to the log file to append to.
    """
    file_path = Path(file_path)
    log_path = Path(log_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Cannot hash non-existent file: {file_path}")

    file_hash = calculate_sha256(file_path)
    file_name = file_path.name
    
    # Format: [TIMESTAMP] [HASH] [FILENAME] [SIZE]
    size = file_path.stat().st_size
    log_entry = f"[HASH] {file_hash} | {file_name} | {size} bytes\n"

    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)

    logger.debug(f"Logged hash for {file_name} to {log_path}")

def log_manifest_entry(manifest_path: Union[str, Path], log_path: Union[str, Path]) -> None:
    """
    Read a manifest file and log all its entries to a log file.
    
    Args:
        manifest_path: Path to the manifest JSON.
        log_path: Path to the log file to append to.
    """
    manifest_path = Path(manifest_path)
    log_path = Path(log_path)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    files = manifest.get("files", {})
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, "a", encoding="utf-8") as f:
        for file_path, metadata in files.items():
            hash_val = metadata.get("hash", "N/A")
            size = metadata.get("size_bytes", "N/A")
            f.write(f"[MANIFEST_ENTRY] {file_path} | Hash: {hash_val} | Size: {size} bytes\n")
    
    logger.info(f"Logged {len(files)} manifest entries to {log_path}")
