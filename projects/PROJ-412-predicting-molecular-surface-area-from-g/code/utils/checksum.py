"""
Dataset checksumming utility for verifying data integrity and reproducibility.

This module provides functions to calculate, save, load, and verify checksums
for individual files and directories containing dataset artifacts.
"""

import hashlib
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from .config import get_project_root, get_data_dir
from .logging import get_logger

logger = get_logger(__name__)

CHECKSUM_ALGORITHM = "sha256"
MANIFEST_FILENAME = "checksum_manifest.json"


def calculate_file_checksum(file_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Calculate the checksum of a single file.

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

    hasher = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def calculate_directory_checksum(dir_path: Path, algorithm: str = CHECKSUM_ALGORITHM) -> str:
    """
    Calculate a combined checksum for all files in a directory.

    The checksum is computed by hashing the sorted concatenation of:
    (relative_path, file_checksum) for all files in the directory.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.

    Returns:
        Hexadecimal string of the directory checksum.

    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    hasher = hashlib.new(algorithm)
    files = sorted(dir_path.rglob('*'))
    files = [f for f in files if f.is_file()]

    if not files:
        logger.warning(f"Directory is empty: {dir_path}")
        # Return hash of empty string for empty directory
        return hashlib.new(algorithm).hexdigest()

    for file_path in files:
        try:
            file_hash = calculate_file_checksum(file_path, algorithm)
            rel_path = file_path.relative_to(dir_path)
            # Combine path and hash in a deterministic way
            combined = f"{rel_path.as_posix()}:{file_hash}"
            hasher.update(combined.encode('utf-8'))
        except FileNotFoundError:
            logger.warning(f"Skipping missing file during directory checksum: {file_path}")
            continue

    return hasher.hexdigest()


def save_checksum_manifest(
    manifest_path: Path,
    file_checksums: Dict[str, str],
    directory_checksums: Dict[str, str],
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save checksums to a JSON manifest file.

    Args:
        manifest_path: Path to save the manifest.
        file_checksums: Dict mapping relative file paths to their checksums.
        directory_checksums: Dict mapping relative directory paths to their checksums.
        metadata: Optional metadata to include (e.g., timestamp, algorithm).
    """
    manifest = {
        "algorithm": CHECKSUM_ALGORITHM,
        "file_checksums": file_checksums,
        "directory_checksums": directory_checksums,
        "metadata": metadata or {}
    }
    if metadata:
        manifest["metadata"].update({"created_at": metadata.get("created_at", "")})

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Checksum manifest saved to {manifest_path}")


def load_checksum_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load checksums from a JSON manifest file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary containing the manifest data.

    Raises:
        FileNotFoundError: If the manifest does not exist.
        json.JSONDecodeError: If the manifest is not valid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def verify_file_checksum(file_path: Path, expected_checksum: str, algorithm: str = CHECKSUM_ALGORITHM) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False

    try:
        actual_checksum = calculate_file_checksum(file_path, algorithm)
        is_valid = actual_checksum == expected_checksum
        if not is_valid:
            logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
        else:
            logger.debug(f"Checksum verified for {file_path}")
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying checksum for {file_path}: {e}")
        return False


def verify_directory_checksum(dir_path: Path, expected_checksum: str, algorithm: str = CHECKSUM_ALGORITHM) -> bool:
    """
    Verify a directory's checksum against an expected value.

    Args:
        dir_path: Path to the directory.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    if not dir_path.is_dir():
        logger.error(f"Path is not a directory for verification: {dir_path}")
        return False

    try:
        actual_checksum = calculate_directory_checksum(dir_path, algorithm)
        is_valid = actual_checksum == expected_checksum
        if not is_valid:
            logger.error(f"Directory checksum mismatch for {dir_path}: expected {expected_checksum}, got {actual_checksum}")
        else:
            logger.debug(f"Directory checksum verified for {dir_path}")
        return is_valid
    except Exception as e:
        logger.error(f"Error verifying directory checksum for {dir_path}: {e}")
        return False


def verify_manifest_checksums(manifest_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify all checksums recorded in a manifest against the actual files.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Tuple of (all_valid, list_of_failed_files)
    """
    try:
        manifest = load_checksum_manifest(manifest_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load manifest: {e}")
        return False, [f"Manifest load error: {e}"]

    project_root = get_project_root()
    algorithm = manifest.get("algorithm", CHECKSUM_ALGORITHM)
    file_checksums = manifest.get("file_checksums", {})
    directory_checksums = manifest.get("directory_checksums", {})

    failures = []

    # Verify files
    for rel_path, expected in file_checksums.items():
        full_path = project_root / rel_path
        if not verify_file_checksum(full_path, expected, algorithm):
            failures.append(f"File mismatch: {rel_path}")

    # Verify directories
    for rel_path, expected in directory_checksums.items():
        full_path = project_root / rel_path
        if not verify_directory_checksum(full_path, expected, algorithm):
            failures.append(f"Directory mismatch: {rel_path}")

    all_valid = len(failures) == 0
    if all_valid:
        logger.info("All checksums in manifest verified successfully.")
    else:
        logger.error(f"Verification failed for {len(failures)} items.")

    return all_valid, failures


def main():
    """
    Command-line interface for checksum operations.
    Usage examples:
      python -m code.utils.checksum --action calculate_file --path data/processed/graphs_with_features.parquet
      python -m code.utils.checksum --action verify_manifest --path data/schemas/checksum_manifest.json
    """
    import argparse

    parser = argparse.ArgumentParser(description="Dataset Checksum Utility")
    parser.add_argument("--action", choices=["calculate_file", "calculate_dir", "verify_file", "verify_dir", "verify_manifest", "save_manifest"], required=True)
    parser.add_argument("--path", type=str, required=True, help="Path to file or directory")
    parser.add_argument("--expected", type=str, help="Expected checksum for verification actions")
    parser.add_argument("--output", type=str, help="Output path for manifest (for save_manifest action)")

    args = parser.parse_args()
    project_root = get_project_root()
    target_path = Path(args.path)

    if not target_path.is_absolute():
        target_path = project_root / target_path

    if args.action == "calculate_file":
        if not target_path.is_file():
            logger.error(f"Path is not a file: {target_path}")
            return 1
        checksum = calculate_file_checksum(target_path)
        print(f"Checksum for {target_path}: {checksum}")

    elif args.action == "calculate_dir":
        if not target_path.is_dir():
            logger.error(f"Path is not a directory: {target_path}")
            return 1
        checksum = calculate_directory_checksum(target_path)
        print(f"Directory checksum for {target_path}: {checksum}")

    elif args.action == "verify_file":
        if not args.expected:
            logger.error("Expected checksum required for verify_file action")
            return 1
        if not target_path.is_file():
            logger.error(f"Path is not a file: {target_path}")
            return 1
        valid = verify_file_checksum(target_path, args.expected)
        print(f"Verification result: {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1

    elif args.action == "verify_dir":
        if not args.expected:
            logger.error("Expected checksum required for verify_dir action")
            return 1
        if not target_path.is_dir():
            logger.error(f"Path is not a directory: {target_path}")
            return 1
        valid = verify_directory_checksum(target_path, args.expected)
        print(f"Verification result: {'PASS' if valid else 'FAIL'}")
        return 0 if valid else 1

    elif args.action == "verify_manifest":
        if not target_path.is_file():
            logger.error(f"Manifest path is not a file: {target_path}")
            return 1
        all_valid, failures = verify_manifest_checksums(target_path)
        if failures:
            for f in failures:
                print(f"  - {f}")
        return 0 if all_valid else 1

    elif args.action == "save_manifest":
        if not args.output:
            logger.error("Output path required for save_manifest action")
            return 1
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = project_root / output_path

        # Calculate checksums for the target path
        file_checksums = {}
        directory_checksums = {}

        if target_path.is_file():
            rel_path = target_path.relative_to(project_root)
            file_checksums[rel_path.as_posix()] = calculate_file_checksum(target_path)
        elif target_path.is_dir():
            rel_path = target_path.relative_to(project_root)
            directory_checksums[rel_path.as_posix()] = calculate_directory_checksum(target_path)
            # Also include all files in the directory
            for f in target_path.rglob('*'):
                if f.is_file():
                    rel_f = f.relative_to(project_root)
                    file_checksums[rel_f.as_posix()] = calculate_file_checksum(f)
        else:
            logger.error(f"Target path is not a file or directory: {target_path}")
            return 1

        save_checksum_manifest(output_path, file_checksums, directory_checksums)
        print(f"Manifest saved to {output_path}")

    return 0


if __name__ == "__main__":
    exit(main())