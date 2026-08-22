"""
Artifact hashing utilities for the evolutionary pressure pipeline.

Provides functions to generate SHA-256 checksums for all intermediate and final
files, generate manifests, and verify file integrity against manifests.
"""
import hashlib
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger

# Constants
HASH_ALGORITHM = "sha256"
MANIFEST_FILENAME = "artifacts_manifest.json"
PIPELINE_LOG_FILENAME = "pipeline.log"


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if file_path.is_dir():
        raise IsADirectoryError(f"Cannot hash a directory: {file_path}")
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (e.g., BAMs)
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    
    return sha256_hash.hexdigest()


def generate_manifest(
    directory: Path,
    output_path: Optional[Path] = None,
    extensions: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Generate a manifest of SHA-256 hashes for all files in a directory.

    Args:
        directory: Root directory to scan for artifacts.
        output_path: Optional path to write the manifest JSON. If None, 
                    manifest is returned as dict only.
        extensions: Optional list of file extensions to include (e.g., ['.bam', '.tsv']).
                   If None, all files are included.
        exclude_patterns: Optional list of filename patterns to exclude (e.g., ['*.log', '.*']).

    Returns:
        Dictionary containing manifest metadata and file hashes.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not directory.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    manifest = {
        "algorithm": HASH_ALGORITHM,
        "directory": str(directory.resolve()),
        "files": {}
    }
    
    logger.info(f"Generating manifest for directory: {directory}")
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(directory)
            file_str = str(relative_path)
            
            # Check extensions filter
            if extensions:
                if file_path.suffix not in extensions:
                    continue
            
            # Check exclude patterns
            if exclude_patterns:
                import fnmatch
                if any(fnmatch.fnmatch(file_str, pattern) for pattern in exclude_patterns):
                    continue
            
            # Skip the manifest file itself to avoid circular dependency
            if file_path.name == MANIFEST_FILENAME:
                continue
            
            try:
                file_hash = calculate_sha256(file_path)
                manifest["files"][file_str] = file_hash
                logger.debug(f"Hashed: {file_str} -> {file_hash[:16]}...")
            except Exception as e:
                logger.warning(f"Failed to hash {file_str}: {e}")
    
    manifest["file_count"] = len(manifest["files"])
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to: {output_path}")
    
    return manifest


def verify_manifest(
    manifest_path: Path,
    directory: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Verify file integrity against a manifest.

    Args:
        manifest_path: Path to the manifest JSON file.
        directory: Optional base directory for relative paths. If None, 
                  uses the directory recorded in the manifest.

    Returns:
        Dictionary with verification results:
        {
            "valid": bool,
            "verified_count": int,
            "failed_count": int,
            "missing_count": int,
            "details": List[Dict]
        }

    Raises:
        FileNotFoundError: If manifest file or directory not found.
        json.JSONDecodeError: If manifest is not valid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    base_dir = Path(manifest["directory"]) if directory is None else directory
    
    if not base_dir.exists():
        raise FileNotFoundError(f"Base directory not found: {base_dir}")
    
    results = {
        "valid": True,
        "verified_count": 0,
        "failed_count": 0,
        "missing_count": 0,
        "details": []
    }
    
    logger.info(f"Verifying {len(manifest['files'])} files against manifest")
    
    for relative_path, expected_hash in manifest["files"].items():
        file_path = base_dir / relative_path
        
        if not file_path.exists():
            results["missing_count"] += 1
            results["valid"] = False
            results["details"].append({
                "file": relative_path,
                "status": "MISSING",
                "expected": expected_hash,
                "actual": None
            })
            logger.warning(f"Missing file: {relative_path}")
            continue
        
        try:
            actual_hash = calculate_sha256(file_path)
            
            if actual_hash == expected_hash:
                results["verified_count"] += 1
                results["details"].append({
                    "file": relative_path,
                    "status": "OK",
                    "expected": expected_hash,
                    "actual": actual_hash
                })
            else:
                results["failed_count"] += 1
                results["valid"] = False
                results["details"].append({
                    "file": relative_path,
                    "status": "MISMATCH",
                    "expected": expected_hash,
                    "actual": actual_hash
                })
                logger.error(f"Hash mismatch for {relative_path}")
        except Exception as e:
            results["failed_count"] += 1
            results["valid"] = False
            results["details"].append({
                "file": relative_path,
                "status": "ERROR",
                "error": str(e),
                "expected": expected_hash,
                "actual": None
            })
            logger.error(f"Error verifying {relative_path}: {e}")
    
    return results


def log_hash_to_file(
    file_path: Path,
    log_path: Path,
    step_name: str
) -> str:
    """
    Calculate hash of a file and append the result to a log file.

    Args:
        file_path: Path to the file to hash.
        log_path: Path to the pipeline log file.
        step_name: Name of the pipeline step for logging context.

    Returns:
        The calculated hash string.

    Raises:
        FileNotFoundError: If file or log path does not exist.
    """
    file_hash = calculate_sha256(file_path)
    
    log_entry = f"[{step_name}] SHA-256({file_path.name}): {file_hash}\n"
    
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)
    
    logger.debug(f"Logged hash for {file_path.name}: {file_hash[:16]}...")
    return file_hash
