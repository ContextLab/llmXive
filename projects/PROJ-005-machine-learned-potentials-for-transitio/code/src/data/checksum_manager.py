"""
Checksum verification logic for downloaded artifacts in data/raw/.
Supports SHA-256 checksum computation and verification against a manifest.
"""
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from src.utils.logging import get_logger

# Configure logger
logger = get_logger(__name__)

CHECKSUM_MANIFEST_NAME = "checksums.json"
DEFAULT_ALGORITHM = "sha256"


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the project structure is:
    code/
    data/
    ...
    and this file is at code/src/data/checksum_manager.py
    """
    current_file = Path(__file__).resolve()
    # Traverse up from code/src/data to project root
    project_root = current_file.parents[3]
    return project_root


def compute_file_checksum(file_path: Path, algorithm: str = DEFAULT_ALGORITHM) -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to compute checksum for.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum computation: {file_path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Algorithm '{algorithm}' not available. Available: {hashlib.algorithms_available}")

    hash_func = hashlib.new(algorithm)

    logger.info(f"Computing {algorithm} checksum for: {file_path}")
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)
        checksum = hash_func.hexdigest()
        logger.info(f"Checksum computed successfully: {checksum}")
        return checksum
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise


def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load the checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the checksums.json file.

    Returns:
        Dictionary mapping relative file paths to their expected checksums.
    """
    if not manifest_path.exists():
        logger.warning(f"Checksum manifest not found at {manifest_path}. Returning empty manifest.")
        return {}

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        logger.info(f"Loaded checksum manifest with {len(manifest)} entries.")
        return manifest
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum manifest: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading checksum manifest: {e}")
        raise


def save_checksum_manifest(checksums: Dict[str, str], manifest_path: Path) -> None:
    """
    Save the checksums to a JSON manifest file.

    Args:
        checksums: Dictionary mapping relative file paths to checksums.
        manifest_path: Path to save the checksums.json file.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        logger.info(f"Checksum manifest saved to {manifest_path}")
    except Exception as e:
        logger.error(f"Error saving checksum manifest: {e}")
        raise


def verify_checksum(file_path: Path, expected_checksum: str, algorithm: str = DEFAULT_ALGORITHM) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum string.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False

    actual_checksum = compute_file_checksum(file_path, algorithm)
    if actual_checksum.lower() == expected_checksum.lower():
        logger.info(f"Checksum verification PASSED for {file_path.name}")
        return True
    else:
        logger.error(
            f"Checksum verification FAILED for {file_path.name}. "
            f"Expected: {expected_checksum}, Got: {actual_checksum}"
        )
        return False


def verify_all_files(manifest_path: Optional[Path] = None, data_raw_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Verify all files listed in the checksum manifest against their stored checksums.

    Args:
        manifest_path: Optional path to the manifest. If None, uses default location.
        data_raw_path: Optional path to data/raw. If None, uses default location.

    Returns:
        Tuple of (all_passed: bool, failed_files: List[str])
    """
    project_root = get_project_root()
    if data_raw_path is None:
        data_raw_path = project_root / "data" / "raw"
    if manifest_path is None:
        manifest_path = data_raw_path / CHECKSUM_MANIFEST_NAME

    if not data_raw_path.exists():
        logger.warning(f"Data raw directory does not exist: {data_raw_path}. Nothing to verify.")
        return True, []

    if not manifest_path.exists():
        logger.warning(f"Checksum manifest does not exist: {manifest_path}. Nothing to verify.")
        return True, []

    manifest = load_checksum_manifest(manifest_path)
    all_passed = True
    failed_files = []

    for relative_path, expected_checksum in manifest.items():
        file_path = data_raw_path / relative_path
        if not file_path.exists():
            logger.error(f"File listed in manifest but not found: {file_path}")
            all_passed = False
            failed_files.append(relative_path)
            continue

        if not verify_checksum(file_path, expected_checksum):
            all_passed = False
            failed_files.append(relative_path)

    return all_passed, failed_files


def update_checksum_for_file(file_path: Path, manifest_path: Optional[Path] = None) -> str:
    """
    Compute checksum for a file and update the manifest.

    Args:
        file_path: Path to the file to checksum.
        manifest_path: Optional path to the manifest.

    Returns:
        The computed checksum.
    """
    project_root = get_project_root()
    if manifest_path is None:
        manifest_path = project_root / "data" / "raw" / CHECKSUM_MANIFEST_NAME

    if not file_path.exists():
        raise FileNotFoundError(f"Cannot update checksum for non-existent file: {file_path}")

    relative_path = str(file_path.relative_to(project_root / "data" / "raw"))
    checksum = compute_file_checksum(file_path)

    manifest = load_checksum_manifest(manifest_path)
    manifest[relative_path] = checksum
    save_checksum_manifest(manifest, manifest_path)

    logger.info(f"Updated checksum for {relative_path} in manifest.")
    return checksum


def main() -> int:
    """
    CLI entry point for checksum management.
    Usage:
      python code/src/data/checksum_manager.py verify
      python code/src/data/checksum_manager.py update <file_path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Checksum verification for data/raw artifacts.")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify all files in data/raw against manifest")

    # Update command
    update_parser = subparsers.add_parser("update", help="Compute checksum and update manifest for a specific file")
    update_parser.add_argument("file_path", type=str, help="Path to the file to checksum (relative to project root)")

    args = parser.parse_args()

    if args.command == "verify":
        all_passed, failed = verify_all_files()
        if all_passed:
            print("All checksums verified successfully.")
            return 0
        else:
            print(f"Verification failed for {len(failed)} file(s):")
            for f in failed:
                print(f"  - {f}")
            return 1

    elif args.command == "update":
        try:
            file_path = Path(args.file_path)
            if not file_path.is_absolute():
                # Assume relative to project root if not absolute
                project_root = get_project_root()
                file_path = project_root / file_path

            if not file_path.exists():
                print(f"Error: File not found: {file_path}")
                return 1

            # Ensure file is under data/raw
            data_raw = get_project_root() / "data" / "raw"
            try:
                file_path.relative_to(data_raw)
            except ValueError:
                print(f"Error: File must be under data/raw: {file_path}")
                return 1

            checksum = update_checksum_for_file(file_path)
            print(f"Updated checksum for {file_path}: {checksum}")
            return 0

        except Exception as e:
            print(f"Error updating checksum: {e}")
            return 1

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
