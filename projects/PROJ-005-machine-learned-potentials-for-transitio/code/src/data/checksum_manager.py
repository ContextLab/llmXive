"""
Checksum Manager for Data Integrity Verification.

This module provides utilities to compute, store, and verify file checksums
(SHA-256) for artifacts in the data/raw/ directory. It ensures data integrity
by maintaining a manifest of expected checksums and verifying downloaded files
against them.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CHECKSUM_ALGORITHM = 'sha256'
MANIFEST_FILENAME = 'checksum_manifest.json'
RAW_DATA_DIR = 'data/raw'


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or code/ directory.
    """
    current_path = Path(__file__).resolve()
    # Traverse up to find the directory containing 'data' and 'specs'
    # Usually the project root is 2 levels up from code/src/data/
    project_root = current_path.parent.parent.parent.parent
    return project_root


def compute_file_checksum(file_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Compute the SHA-256 checksum of a file.

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

    hash_obj = hashlib.new(algorithm)

    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_obj.update(chunk)
    except IOError as e:
        logger.error(f"IO error while reading {file_path}: {e}")
        raise

    return hash_obj.hexdigest()


def load_checksum_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the checksum manifest from disk.

    Args:
        manifest_path: Optional path to the manifest file. If None, uses the default
                       location in the project root.

    Returns:
        Dictionary containing the manifest data. Empty dict if file doesn't exist.
    """
    if manifest_path is None:
        project_root = get_project_root()
        manifest_path = project_root / RAW_DATA_DIR / MANIFEST_FILENAME

    if not manifest_path.exists():
        logger.info(f"Checksum manifest not found at {manifest_path}. Initializing empty manifest.")
        return {
            "version": "1.0",
            "algorithm": CHECKSUM_ALGORITHM,
            "files": {}
        }

    try:
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded checksum manifest from {manifest_path}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse checksum manifest: {e}")
        raise
    except IOError as e:
        logger.error(f"IO error while reading manifest: {e}")
        raise


def save_checksum_manifest(manifest: Dict[str, Any], manifest_path: Optional[Path] = None) -> None:
    """
    Save the checksum manifest to disk.

    Args:
        manifest: Dictionary containing the manifest data.
        manifest_path: Optional path to save the manifest. Defaults to standard location.
    """
    if manifest_path is None:
        project_root = get_project_root()
        manifest_path = project_root / RAW_DATA_DIR / MANIFEST_FILENAME

    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Saved checksum manifest to {manifest_path}")
    except IOError as e:
        logger.error(f"Failed to save checksum manifest: {e}")
        raise


def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = CHECKSUM_ALGORITHM) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected hexadecimal checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        if actual_checksum.lower() == expected_checksum.lower():
            logger.info(f"Checksum verified for {file_path.name}")
            return True
        else:
            logger.error(f"Checksum mismatch for {file_path.name}. "
                         f"Expected: {expected_checksum}, Got: {actual_checksum}")
            return False
    except FileNotFoundError as e:
        logger.error(f"File not found during verification: {file_path}")
        raise


def verify_all_files(manifest: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
    """
    Verify all files listed in the manifest against their stored checksums.

    Args:
        manifest: Optional manifest dictionary. If None, loads from disk.

    Returns:
        Tuple of (all_verified: bool, failed_files: List[str])
    """
    if manifest is None:
        manifest = load_checksum_manifest()

    files_dict = manifest.get('files', {})
    failed_files = []
    all_verified = True

    project_root = get_project_root()
    raw_data_dir = project_root / RAW_DATA_DIR

    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return False, ["Raw data directory missing"]

    for relative_path, checksum_info in files_dict.items():
        file_path = raw_data_dir / relative_path
        expected_checksum = checksum_info.get('checksum')

        if not file_path.exists():
            logger.error(f"File missing from verification: {relative_path}")
            failed_files.append(relative_path)
            all_verified = False
            continue

        if expected_checksum is None:
            logger.warning(f"No checksum found for {relative_path} in manifest")
            continue

        if not verify_checksum(file_path, expected_checksum):
            failed_files.append(relative_path)
            all_verified = False

    return all_verified, failed_files


def update_checksum_for_file(file_path: Path, manifest: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Compute and update the checksum for a specific file in the manifest.

    Args:
        file_path: Path to the file (relative to data/raw or absolute).
        manifest: Optional manifest to update in memory.

    Returns:
        Updated manifest dictionary.
    """
    if manifest is None:
        manifest = load_checksum_manifest()

    # Resolve path relative to raw_data_dir if it's not absolute
    project_root = get_project_root()
    raw_data_dir = project_root / RAW_DATA_DIR

    if not file_path.is_absolute():
        # Assume it's relative to raw_data_dir
        full_path = raw_data_dir / file_path
        relative_path = str(file_path)
    else:
        full_path = Path(file_path)
        try:
            relative_path = str(full_path.relative_to(raw_data_dir))
        except ValueError:
            # If not relative to raw_data_dir, use the filename as key
            relative_path = full_path.name

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")

    checksum = compute_file_checksum(full_path)

    if 'files' not in manifest:
        manifest['files'] = {}

    manifest['files'][relative_path] = {
        'checksum': checksum,
        'algorithm': CHECKSUM_ALGORITHM,
        'last_updated': str(Path(full_path).stat().st_mtime)
    }

    logger.info(f"Updated checksum for {relative_path}: {checksum}")
    return manifest


def main() -> int:
    """
    CLI entry point for checksum management operations.

    Usage:
        python -m src.data.checksum_manager [command] [args]

    Commands:
        verify [filename]   - Verify a specific file or all files in manifest
        add [filename]      - Add/update checksum for a specific file
        init                - Initialize a new empty manifest
        list                - List all tracked files and their status
    """
    if len(sys.argv) < 2:
        print("Usage: python -m src.data.checksum_manager <command> [args]")
        print("Commands: verify, add, init, list")
        return 1

    command = sys.argv[1]
    project_root = get_project_root()
    raw_data_dir = project_root / RAW_DATA_DIR

    if command == "init":
        manifest = {
            "version": "1.0",
            "algorithm": CHECKSUM_ALGORITHM,
            "files": {}
        }
        save_checksum_manifest(manifest)
        print(f"Initialized checksum manifest at {raw_data_dir / MANIFEST_FILENAME}")
        return 0

    elif command == "add":
        if len(sys.argv) < 3:
            print("Error: Filename required for 'add' command")
            return 1
        filename = sys.argv[2]
        file_path = raw_data_dir / filename
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return 1

        manifest = load_checksum_manifest()
        manifest = update_checksum_for_file(file_path, manifest)
        save_checksum_manifest(manifest)
        return 0

    elif command == "verify":
        if len(sys.argv) >= 3:
            filename = sys.argv[2]
            file_path = raw_data_dir / filename
            if not file_path.exists():
                print(f"Error: File not found: {file_path}")
                return 1
            manifest = load_checksum_manifest()
            files_dict = manifest.get('files', {})
            if filename not in files_dict:
                print(f"Error: File not in manifest: {filename}")
                return 1
            expected = files_dict[filename].get('checksum')
            if expected:
                if verify_checksum(file_path, expected):
                    print(f"OK: {filename}")
                    return 0
                else:
                    print(f"FAIL: {filename}")
                    return 1
            else:
                print(f"Error: No checksum in manifest for {filename}")
                return 1
        else:
            all_ok, failed = verify_all_files()
            if all_ok:
                print("All files verified successfully.")
                return 0
            else:
                print(f"Verification failed for {len(failed)} file(s):")
                for f in failed:
                    print(f"  - {f}")
                return 1

    elif command == "list":
        manifest = load_checksum_manifest()
        files_dict = manifest.get('files', {})
        if not files_dict:
            print("No files tracked in manifest.")
            return 0
        print(f"Tracked files ({len(files_dict)}):")
        for rel_path, info in files_dict.items():
            checksum = info.get('checksum', 'N/A')
            print(f"  {rel_path}: {checksum[:16]}...")
        return 0

    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
