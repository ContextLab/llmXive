"""
Checksum utility for dataset verification and reproducibility.

This module provides functions to calculate SHA-256 checksums for files and directories,
save/load checksum manifests, and verify data integrity. It is used to ensure
reproducibility and detect data corruption during the pipeline execution.
"""

import hashlib
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from .logging import get_logger

# Constants
CHUNK_SIZE = 1024 * 1024  # 1MB chunks for reading files
MANIFEST_FILENAME = "checksum_manifest.json"

logger = get_logger(__name__)


def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the SHA-256 checksum of a single file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string representation of the hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except IOError as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise


def calculate_directory_checksum(
    dir_path: Path, algorithm: str = "sha256", exclude_patterns: Optional[List[str]] = None
) -> Tuple[str, Dict[str, str]]:
    """
    Calculate checksums for all files in a directory recursively.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use (default: sha256).
        exclude_patterns: List of glob patterns to exclude (e.g., ['*.log', '__pycache__']).

    Returns:
        Tuple of (combined checksum, dict of file_path -> checksum).
        The combined checksum is the SHA-256 of the sorted concatenation of all file checksums.

    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    file_checksums = {}
    exclude_patterns = exclude_patterns or []

    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(dir_path):
        # Filter directories
        dirs[:] = [d for d in dirs if not any(Path(d).match(p) for p in exclude_patterns)]

        for file in files:
            file_path = Path(root) / file
            # Check exclusion patterns
            if any(file_path.match(p) for p in exclude_patterns):
                continue
            all_files.append(file_path)

    # Sort for reproducibility
    all_files.sort()

    # Calculate individual checksums
    combined_hash_input = ""
    for file_path in all_files:
        try:
            checksum = calculate_file_checksum(file_path, algorithm)
            relative_path = str(file_path.relative_to(dir_path))
            file_checksums[relative_path] = checksum
            combined_hash_input += f"{relative_path}:{checksum}\n"
        except (FileNotFoundError, IOError) as e:
            logger.warning(f"Skipping file {file_path} due to error: {e}")

    # Calculate combined checksum
    combined_hash = hashlib.new(algorithm)
    combined_hash.update(combined_hash_input.encode("utf-8"))

    return combined_hash.hexdigest(), file_checksums


def save_checksum_manifest(
    manifest_path: Path,
    file_checksums: Dict[str, str],
    directory_checksum: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Save checksums to a JSON manifest file.

    Args:
        manifest_path: Path to save the manifest.
        file_checksums: Dictionary of file paths to checksums.
        directory_checksum: Optional combined directory checksum.
        metadata: Optional metadata to include (e.g., timestamp, algorithm).
    """
    manifest_data = {
        "file_checksums": file_checksums,
        "directory_checksum": directory_checksum,
        "metadata": metadata or {},
    }

    # Ensure parent directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True)

    logger.info(f"Saved checksum manifest to {manifest_path}")


def load_checksum_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load a checksum manifest from a JSON file.

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

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_file_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm to use.

    Returns:
        True if the checksum matches, False otherwise.
    """
    try:
        actual_checksum = calculate_file_checksum(file_path, algorithm)
        match = actual_checksum == expected_checksum
        if not match:
            logger.error(
                f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}"
            )
        return match
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Failed to verify checksum for {file_path}: {e}")
        return False


def verify_directory_checksum(
    dir_path: Path,
    expected_checksum: str,
    file_checksums: Dict[str, str],
    algorithm: str = "sha256",
) -> Tuple[bool, List[str]]:
    """
    Verify all files in a directory against expected checksums.

    Args:
        dir_path: Path to the directory.
        expected_checksum: Expected combined directory checksum.
        file_checksums: Dictionary of expected file checksums.
        algorithm: Hash algorithm to use.

    Returns:
        Tuple of (overall success, list of failed files).
    """
    failed_files = []

    # Verify individual files
    for relative_path, expected in file_checksums.items():
        file_path = dir_path / relative_path
        if not file_path.exists():
            logger.error(f"File missing during verification: {file_path}")
            failed_files.append(relative_path)
            continue

        if not verify_file_checksum(file_path, expected, algorithm):
            failed_files.append(relative_path)

    # Verify combined checksum
    actual_combined, _ = calculate_directory_checksum(dir_path, algorithm)
    if actual_combined != expected_checksum:
        logger.error(
            f"Directory checksum mismatch: expected {expected_checksum}, got {actual_combined}"
        )
        return False, failed_files

    if failed_files:
        return False, failed_files

    logger.info(f"Directory checksum verification successful: {dir_path}")
    return True, []


def verify_manifest_checksums(manifest_path: Path, base_dir: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Verify all checksums in a manifest against actual files.

    Args:
        manifest_path: Path to the checksum manifest.
        base_dir: Base directory for relative paths (defaults to manifest's parent).

    Returns:
        Tuple of (overall success, list of failed files).
    """
    if base_dir is None:
        base_dir = manifest_path.parent

    try:
        manifest = load_checksum_manifest(manifest_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Failed to load manifest: {e}")
        return False, []

    file_checksums = manifest.get("file_checksums", {})
    expected_dir_checksum = manifest.get("directory_checksum")

    # Verify individual files
    success, failed_files = verify_directory_checksum(
        base_dir,
        expected_dir_checksum or "",
        file_checksums,
    )

    return success, failed_files


def main() -> None:
    """
    Command-line interface for checksum operations.

    Usage:
        python -m code.utils.checksum --command <command> [options]

    Commands:
        calculate-file <path>          Calculate checksum for a file
        calculate-dir <path>           Calculate checksums for a directory
        save-manifest <path> <files>   Save checksums to a manifest
        verify-manifest <path>         Verify all files in a manifest
    """
    import argparse

    parser = argparse.ArgumentParser(description="Checksum utility for dataset verification")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Calculate file checksum
    file_parser = subparsers.add_parser("calculate-file", help="Calculate checksum for a file")
    file_parser.add_argument("path", type=Path, help="Path to the file")
    file_parser.add_argument("--algorithm", default="sha256", help="Hash algorithm (default: sha256)")

    # Calculate directory checksum
    dir_parser = subparsers.add_parser("calculate-dir", help="Calculate checksums for a directory")
    dir_parser.add_argument("path", type=Path, help="Path to the directory")
    dir_parser.add_argument("--algorithm", default="sha256", help="Hash algorithm (default: sha256)")
    dir_parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Patterns to exclude (e.g., '*.log __pycache__')",
    )

    # Save manifest
    save_parser = subparsers.add_parser("save-manifest", help="Save checksums to a manifest")
    save_parser.add_argument("output", type=Path, help="Output manifest path")
    save_parser.add_argument("path", type=Path, help="Path to file or directory")
    save_parser.add_argument("--metadata", type=str, default="{}", help="JSON metadata string")

    # Verify manifest
    verify_parser = subparsers.add_parser("verify-manifest", help="Verify checksums in a manifest")
    verify_parser.add_argument("manifest", type=Path, help="Path to the manifest")
    verify_parser.add_argument("--base-dir", type=Path, help="Base directory for relative paths")

    args = parser.parse_args()

    if args.command == "calculate-file":
        checksum = calculate_file_checksum(args.path, args.algorithm)
        print(f"{checksum}  {args.path}")

    elif args.command == "calculate-dir":
        combined, file_checksums = calculate_directory_checksum(
            args.path, args.algorithm, args.exclude
        )
        print(f"Directory checksum: {combined}")
        print("File checksums:")
        for path, checksum in sorted(file_checksums.items()):
            print(f"  {checksum}  {path}")

    elif args.command == "save-manifest":
        metadata = json.loads(args.metadata)
        if args.path.is_file():
            checksum = calculate_file_checksum(args.path)
            file_checksums = {str(args.path.name): checksum}
            combined = None
        else:
            combined, file_checksums = calculate_directory_checksum(args.path)

        save_checksum_manifest(args.output, file_checksums, combined, metadata)
        print(f"Manifest saved to {args.output}")

    elif args.command == "verify-manifest":
        success, failed = verify_manifest_checksums(args.manifest, args.base_dir)
        if success:
            print("All checksums verified successfully.")
        else:
            print(f"Verification failed for {len(failed)} files:")
            for f in failed:
                print(f"  - {f}")
        exit(0 if success else 1)

    else:
        parser.print_help()
        exit(1)


if __name__ == "__main__":
    main()