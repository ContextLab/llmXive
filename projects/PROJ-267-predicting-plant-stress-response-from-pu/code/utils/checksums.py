"""
Checksum verification utilities for SHA-256 validation of raw downloads.

This module provides functionality to compute and verify SHA-256 checksums
for data files to ensure integrity of downloaded datasets.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from .logging_config import get_logger, log_warning
from .config import DATA_RAW_PATH, CHECKSUMS_FILE

logger = get_logger(__name__)


def compute_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file path is invalid.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str) -> Tuple[bool, str]:
    """
    Verify a file's SHA-256 checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 hash string.

    Returns:
        Tuple of (is_valid, message) where is_valid is True if checksums match.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        msg = f"File not found for verification: {file_path}"
        log_warning(msg)
        return False, msg

    actual_checksum = compute_sha256(file_path)
    is_valid = actual_checksum.lower() == expected_checksum.lower()

    if is_valid:
        msg = f"Checksum verified for {file_path.name}: {actual_checksum[:16]}..."
        logger.info(msg)
    else:
        msg = (
            f"Checksum MISMATCH for {file_path.name}!\n"
            f"  Expected: {expected_checksum}\n"
            f"  Actual:   {actual_checksum}"
        )
        log_warning(msg)

    return is_valid, msg


def save_checksums(checksums: Dict[str, str], output_path: Optional[str] = None) -> str:
    """
    Save a dictionary of file checksums to a JSON file.

    Args:
        checksums: Dictionary mapping file paths to their SHA-256 hashes.
        output_path: Optional path to save the checksums file. Defaults to config CHECKSUMS_FILE.

    Returns:
        Path where checksums were saved.
    """
    if output_path is None:
        output_path = CHECKSUMS_FILE

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Checksums saved to {output_path}")
    return str(output_path)


def load_checksums(input_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        input_path: Optional path to load checksums from. Defaults to config CHECKSUMS_FILE.

    Returns:
        Dictionary mapping file paths to their SHA-256 hashes.

    Raises:
        FileNotFoundError: If the checksums file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if input_path is None:
        input_path = CHECKSUMS_FILE

    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Checksums file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_all_downloads(raw_data_dir: Optional[str] = None) -> List[Tuple[str, bool, str]]:
    """
    Verify checksums for all files in the raw data directory against saved checksums.

    Args:
        raw_data_dir: Optional path to raw data directory. Defaults to config DATA_RAW_PATH.

    Returns:
        List of tuples (file_path, is_valid, message) for each verified file.
    """
    if raw_data_dir is None:
        raw_data_dir = DATA_RAW_PATH

    raw_data_path = Path(raw_data_dir)
    if not raw_data_path.exists():
        msg = f"Raw data directory does not exist: {raw_data_path}"
        log_warning(msg)
        return [(msg, False, msg)]

    try:
        saved_checksums = load_checksums()
    except FileNotFoundError as e:
        msg = f"No checksums file found to verify against: {e}"
        log_warning(msg)
        return [(msg, False, msg)]
    except json.JSONDecodeError as e:
        msg = f"Invalid checksums file format: {e}"
        log_warning(msg)
        return [(msg, False, msg)]

    results = []
    files_to_check = list(raw_data_path.glob("*"))
    files_to_check = [f for f in files_to_check if f.is_file()]

    if not files_to_check:
        msg = "No files found in raw data directory to verify."
        logger.info(msg)
        return [(msg, True, msg)]

    for file_path in files_to_check:
        rel_path = str(file_path.relative_to(raw_data_path))
        if rel_path in saved_checksums:
            is_valid, message = verify_checksum(str(file_path), saved_checksums[rel_path])
            results.append((rel_path, is_valid, message))
        else:
            msg = f"No checksum record for {rel_path}, skipping verification."
            log_warning(msg)
            results.append((rel_path, False, msg))

    return results


def generate_checksums_for_directory(directory_path: str, output_path: Optional[str] = None) -> Dict[str, str]:
    """
    Generate SHA-256 checksums for all files in a directory.

    Args:
        directory_path: Path to the directory to scan.
        output_path: Optional path to save the generated checksums file.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    dir_path = Path(directory_path)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {dir_path}")

    checksums = {}
    files = [f for f in dir_path.glob("*") if f.is_file()]

    logger.info(f"Generating checksums for {len(files)} files in {dir_path}")

    for file_path in files:
        rel_path = str(file_path.relative_to(dir_path))
        try:
            checksum = compute_sha256(file_path)
            checksums[rel_path] = checksum
            logger.debug(f"Computed checksum for {rel_path}: {checksum[:16]}...")
        except Exception as e:
            msg = f"Failed to compute checksum for {file_path}: {e}"
            log_warning(msg)

    if output_path:
        save_checksums(checksums, output_path)

    return checksums


def main():
    """
    CLI entry point for checksum verification utility.
    Usage: python -m utils.checksums [command] [args]

    Commands:
      verify <file_path> <expected_checksum>  - Verify a single file
      verify-all                              - Verify all files in raw data directory
      generate <dir_path>                     - Generate checksums for a directory
      save <file_path> <checksum>             - Save a single checksum record
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m utils.checksums <command> [args]")
        print("Commands: verify, verify-all, generate, save")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "verify":
        if len(sys.argv) != 4:
            print("Usage: verify <file_path> <expected_checksum>")
            sys.exit(1)
        file_path = sys.argv[2]
        expected = sys.argv[3]
        is_valid, message = verify_checksum(file_path, expected)
        print(message)
        sys.exit(0 if is_valid else 1)

    elif command == "verify-all":
        results = verify_all_downloads()
        all_valid = True
        for rel_path, is_valid, message in results:
            status = "✓" if is_valid else "✗"
            print(f"{status} {rel_path}: {message}")
            if not is_valid:
                all_valid = False
        sys.exit(0 if all_valid else 1)

    elif command == "generate":
        if len(sys.argv) < 3:
            print("Usage: generate <directory_path> [output_file]")
            sys.exit(1)
        dir_path = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) > 3 else None
        checksums = generate_checksums_for_directory(dir_path, output_file)
        print(f"Generated {len(checksums)} checksums")
        if output_file:
            print(f"Saved to {output_file}")

    elif command == "save":
        if len(sys.argv) != 4:
            print("Usage: save <file_path> <checksum>")
            sys.exit(1)
        file_path = sys.argv[2]
        checksum = sys.argv[3]
        try:
            saved_path = save_checksums({file_path: checksum})
            print(f"Checksum saved to {saved_path}")
        except Exception as e:
            print(f"Error saving checksum: {e}")
            sys.exit(1)

    else:
        print(f"Unknown command: {command}")
        print("Commands: verify, verify-all, generate, save")
        sys.exit(1)


if __name__ == "__main__":
    main()
