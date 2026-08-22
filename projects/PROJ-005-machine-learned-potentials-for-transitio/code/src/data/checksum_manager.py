"""
Checksum Manager for verifying downloaded artifacts.

This module provides utilities to compute, store, and verify SHA-256 checksums
for files in the data/raw directory. It ensures data integrity by comparing
computed checksums against a manifest.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import logging setup from existing project utilities
try:
    from src.utils.logging import get_logger
except ImportError:
    # Fallback if utils/logging.py is not yet fully ready or path differs
    def get_logger(name: str):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)

MANIFEST_FILENAME = "checksums.json"

def get_project_root() -> Path:
    """Determine the project root directory (parent of 'code')."""
    current_file = Path(__file__).resolve()
    # Assuming structure: code/src/data/checksum_manager.py -> root is 3 levels up
    return current_file.parent.parent.parent

def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a regular file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files without memory issues
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def load_checksum_manifest(manifest_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load the checksum manifest from disk.

    Args:
        manifest_path: Optional path to the manifest. Defaults to data/raw/checksums.json.

    Returns:
        Dictionary mapping relative file paths to their expected checksums.
    """
    if manifest_path is None:
        project_root = get_project_root()
        manifest_path = project_root / "data" / "raw" / MANIFEST_FILENAME

    if not manifest_path.exists():
        logger.warning(f"Checksum manifest not found at {manifest_path}. Returning empty manifest.")
        return {}

    try:
        with open(manifest_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum manifest: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading manifest: {e}")
        raise

def save_checksum_manifest(checksums: Dict[str, str], manifest_path: Optional[Path] = None) -> None:
    """
    Save the checksum manifest to disk.

    Args:
        checksums: Dictionary mapping relative file paths to checksums.
        manifest_path: Optional path to save the manifest.
    """
    if manifest_path is None:
        project_root = get_project_root()
        raw_dir = project_root / "data" / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = raw_dir / MANIFEST_FILENAME

    try:
        with open(manifest_path, "w") as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksum manifest saved to {manifest_path}")
    except IOError as e:
        logger.error(f"Error writing manifest: {e}")
        raise

def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a single file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected SHA-256 hex string.
        algorithm: Hash algorithm.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        computed = compute_file_checksum(file_path, algorithm)
        if computed.lower() == expected_checksum.lower():
            logger.info(f"Checksum verified for {file_path.name}")
            return True
        else:
            logger.error(f"Checksum MISMATCH for {file_path.name}")
            logger.error(f"  Expected: {expected_checksum}")
            logger.error(f"  Computed: {computed}")
            return False
    except Exception as e:
        logger.error(f"Error verifying checksum for {file_path}: {e}")
        return False

def verify_all_files(manifest_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Verify all files listed in the checksum manifest.

    Args:
        manifest_path: Optional path to the manifest.

    Returns:
        Tuple of (all_passed: bool, failed_files: List[str]).
    """
    checksums = load_checksum_manifest(manifest_path)
    if not checksums:
        logger.warning("Manifest is empty. Nothing to verify.")
        return True, []

    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    failed_files = []

    for relative_path, expected_checksum in checksums.items():
        full_path = raw_dir / relative_path
        if not full_path.exists():
            logger.error(f"File missing in manifest verification: {full_path}")
            failed_files.append(relative_path)
            continue

        if not verify_checksum(full_path, expected_checksum):
            failed_files.append(relative_path)

    all_passed = len(failed_files) == 0
    if all_passed:
        logger.info("All files verified successfully.")
    else:
        logger.error(f"Verification failed for {len(failed_files)} file(s).")

    return all_passed, failed_files

def update_checksum_for_file(file_path: Path, manifest_path: Optional[Path] = None) -> None:
    """
    Compute checksum for a file and update the manifest.
    This is used when a new file is downloaded.

    Args:
        file_path: Path to the file to checksum.
        manifest_path: Optional path to the manifest.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot update checksum for missing file: {file_path}")

    relative_path = file_path.relative_to(get_project_root() / "data" / "raw")
    checksum = compute_file_checksum(file_path)

    checksums = load_checksum_manifest(manifest_path)
    checksums[str(relative_path)] = checksum
    save_checksum_manifest(checksums, manifest_path)

def main() -> int:
    """
    CLI entry point for checksum management.

    Usage:
      python -m src.data.checksum_manager verify-all
      python -m src.data.checksum_manager update <file_path>
      python -m src.data.checksum_manager compute <file_path>
    """
    if len(sys.argv) < 2:
        print("Usage: python -m src.data.checksum_manager <command> [args]")
        print("Commands:")
        print("  verify-all              Verify all files in data/raw against manifest")
        print("  update <file_path>      Compute checksum and update manifest for file")
        print("  compute <file_path>     Compute and print checksum for file only")
        return 1

    command = sys.argv[1]
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"

    if not raw_dir.exists():
        logger.warning(f"Data raw directory does not exist yet: {raw_dir}")
        # Create it to allow subsequent operations if needed, or just warn
        # For this task, we ensure the directory exists as part of setup
        raw_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {raw_dir}")

    if command == "verify-all":
        success, failed = verify_all_files()
        return 0 if success else 1

    elif command == "update":
        if len(sys.argv) < 3:
            print("Error: update command requires a file path argument.")
            return 1
        file_path = Path(sys.argv[2])
        if not file_path.is_absolute():
            file_path = raw_dir / file_path
        try:
            update_checksum_for_file(file_path)
            print(f"Updated checksum for {file_path.name}")
            return 0
        except Exception as e:
            print(f"Error updating checksum: {e}")
            return 1

    elif command == "compute":
        if len(sys.argv) < 3:
            print("Error: compute command requires a file path argument.")
            return 1
        file_path = Path(sys.argv[2])
        if not file_path.is_absolute():
            file_path = raw_dir / file_path
        try:
            checksum = compute_file_checksum(file_path)
            print(f"SHA256({file_path.name}): {checksum}")
            return 0
        except Exception as e:
            print(f"Error computing checksum: {e}")
            return 1

    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
