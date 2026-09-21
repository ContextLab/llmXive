"""
Validation Utilities for File Integrity and Checksum Verification.

Implements Constitution Principle III: Data Integrity Verification.
Provides functions for computing checksums, verifying file integrity,
and managing manifests for data provenance.
"""
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from config.env_config import get_data_dir

# Configure logging
logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the cryptographic checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).
        
    Returns:
        Hexadecimal digest string of the file's checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without loading entirely into memory
            for chunk in iter(lambda: f.read(65536), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except PermissionError:
        logger.error(f"Permission denied reading file for checksum: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise


def verify_file_integrity(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> Tuple[bool, str]:
    """
    Verify a file's integrity against an expected checksum.
    
    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected checksum string (hex).
        algorithm: Hash algorithm used for the checksum.
        
    Returns:
        Tuple of (is_valid: bool, message: str).
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for verification: {file_path}")
    
    actual_checksum = compute_file_checksum(file_path, algorithm)
    
    if actual_checksum.lower() == expected_checksum.lower():
        logger.info(f"Integrity verified for {file_path.name}: {actual_checksum[:16]}...")
        return True, "Integrity verified"
    else:
        error_msg = (
            f"Integrity check FAILED for {file_path.name}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
        logger.error(error_msg)
        return False, error_msg


def create_manifest(file_paths: List[Path], output_path: Path, algorithm: str = "sha256") -> Dict[str, Any]:
    """
    Create a manifest file containing checksums for a list of files.
    
    Args:
        file_paths: List of paths to include in the manifest.
        output_path: Path where the manifest JSON will be saved.
        algorithm: Hash algorithm to use.
        
    Returns:
        The manifest dictionary.
    """
    logger.info(f"Creating manifest for {len(file_paths)} files at {output_path}")
    
    manifest = {
        "algorithm": algorithm,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "files": {}
    }
    
    for f_path in file_paths:
        if not f_path.exists():
            logger.warning(f"Skipping missing file in manifest: {f_path}")
            continue
        
        checksum = compute_file_checksum(f_path, algorithm)
        manifest["files"][str(f_path)] = {
            "checksum": checksum,
            "size_bytes": f_path.stat().st_size,
            "modified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(f_path.stat().st_mtime))
        }
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Manifest saved to {output_path}")
    return manifest


def verify_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Verify all files listed in a manifest against their recorded checksums.
    
    Args:
        manifest_path: Path to the manifest JSON file.
        
    Returns:
        Dictionary with verification results:
            - "all_valid": bool
            - "verified": List[str] (paths)
            - "failed": List[str] (paths)
            - "missing": List[str] (paths)
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    algorithm = manifest.get("algorithm", "sha256")
    results = {
        "all_valid": True,
        "verified": [],
        "failed": [],
        "missing": []
    }
    
    for file_str, file_info in manifest["files"].items():
        f_path = Path(file_str)
        
        if not f_path.exists():
            results["missing"].append(file_str)
            results["all_valid"] = False
            logger.warning(f"Missing file in manifest verification: {file_str}")
            continue
        
        is_valid, msg = verify_file_integrity(f_path, file_info["checksum"], algorithm)
        
        if is_valid:
            results["verified"].append(file_str)
        else:
            results["failed"].append(file_str)
            results["all_valid"] = False
            logger.error(f"Verification failed for {file_str}: {msg}")
    
    return results


def check_file_age(file_path: Path, max_age_seconds: int) -> bool:
    """
    Check if a file is older than a specified age in seconds.
    
    Args:
        file_path: Path to the file.
        max_age_seconds: Maximum allowed age in seconds.
        
    Returns:
        True if file is older than max_age_seconds, False otherwise.
    """
    if not file_path.exists():
        return True  # Consider missing files as "too old" (need refresh)
    
    mtime = file_path.stat().st_mtime
    current_time = time.time()
    age = current_time - mtime
    
    is_old = age > max_age_seconds
    if is_old:
        logger.debug(f"File {file_path.name} is {age:.1f}s old (limit: {max_age_seconds}s)")
    return is_old


def save_manifest(manifest: Dict[str, Any], output_path: Path) -> None:
    """
    Save a manifest dictionary to a JSON file.
    
    Args:
        manifest: The manifest dictionary to save.
        output_path: Path where the manifest will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {output_path}")


def main() -> None:
    """
    Command-line entry point for validation utilities.
    Demonstrates checksum computation and manifest creation.
    """
    # Setup logging for CLI usage
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    data_dir = get_data_dir()
    raw_dir = data_dir / "raw"
    
    if not raw_dir.exists():
        logger.error(f"Data directory does not exist: {raw_dir}")
        return
    
    # Find all files in raw directory
    files = list(raw_dir.rglob("*"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        logger.info("No files found in raw directory to process.")
        return
    
    logger.info(f"Found {len(files)} files in {raw_dir}")
    
    # Create manifest
    manifest_path = data_dir / "processed" / "manifest.json"
    manifest = create_manifest(files, manifest_path)
    
    # Verify manifest
    logger.info("Verifying manifest...")
    verification_results = verify_manifest(manifest_path)
    
    if verification_results["all_valid"]:
        logger.info("Manifest verification PASSED: All files are intact.")
    else:
        logger.error("Manifest verification FAILED:")
        if verification_results["failed"]:
            logger.error(f"  Corrupted: {verification_results['failed']}")
        if verification_results["missing"]:
            logger.error(f"  Missing: {verification_results['missing']}")


if __name__ == "__main__":
    main()