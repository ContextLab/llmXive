"""
Data integrity infrastructure for verifying downloaded dataset shards.

This module provides utilities to compute SHA-256 checksums of files and
verify them against a manifest of known-good hashes.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Default manifest path relative to project root
DEFAULT_MANIFEST_PATH = "data/raw/checksums.txt"


def compute_sha256(file_path: str, chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.
        chunk_size: Size of chunks to read at a time (default 8KB).

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def parse_manifest(manifest_path: str) -> Dict[str, str]:
    """
    Parse a checksum manifest file.

    Expected format: one line per entry as `hash  relative_path`
    (two spaces or tab separated, consistent with `sha256sum` output).

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary mapping relative file paths to their expected SHA-256 hashes.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        ValueError: If a line in the manifest cannot be parsed.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    checksums = {}
    with open(path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) < 2:
                raise ValueError(
                    f"Invalid manifest format at line {line_num}: expected 'hash  path', got '{line}'"
                )

            # Handle standard sha256sum format: hash  filename
            # The hash is the first token, the path is the rest (joined in case of spaces)
            expected_hash = parts[0]
            # Join remaining parts with space to handle filenames with spaces
            file_path = " ".join(parts[1:])

            checksums[file_path] = expected_hash

    return checksums


def verify_file(file_path: str, expected_hash: str) -> bool:
    """
    Verify a single file against an expected hash.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA-256 hash (hex string).

    Returns:
        True if the file's hash matches the expected hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()


def verify_manifest(
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    base_dir: Optional[str] = None
) -> List[Tuple[str, bool, str]]:
    """
    Verify all files listed in a manifest against their expected hashes.

    Args:
        manifest_path: Path to the manifest file.
        base_dir: Base directory for resolving relative paths in manifest.
                  If None, uses the directory containing the manifest.

    Returns:
        List of tuples: (file_path, is_valid, message)
        - file_path: Relative path as listed in manifest
        - is_valid: True if hash matches, False otherwise
        - message: Detailed status message

    Raises:
        FileNotFoundError: If the manifest file does not exist.
    """
    if base_dir is None:
        base_dir = str(Path(manifest_path).parent)

    checksums = parse_manifest(manifest_path)
    results = []

    for rel_path, expected_hash in checksums.items():
        full_path = os.path.join(base_dir, rel_path)

        if not os.path.exists(full_path):
            results.append((rel_path, False, f"File not found: {full_path}"))
            continue

        try:
            actual_hash = compute_sha256(full_path)
            if actual_hash.lower() == expected_hash.lower():
                results.append((rel_path, True, "OK"))
            else:
                results.append(
                    (
                        rel_path,
                        False,
                        f"Hash mismatch. Expected: {expected_hash}, Got: {actual_hash}"
                    )
                )
        except Exception as e:
            results.append((rel_path, False, f"Error reading file: {str(e)}"))

    return results


def create_manifest(
    directory: str,
    output_path: str,
    recursive: bool = True,
    include_hidden: bool = False
) -> None:
    """
    Create a checksum manifest for all files in a directory.

    Args:
        directory: Directory to scan for files.
        output_path: Path where the manifest file will be written.
        recursive: If True, scan subdirectories recursively.
        include_hidden: If True, include hidden files (starting with '.').
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    files = []
    if recursive:
        for root, _, filenames in os.walk(dir_path):
            for filename in filenames:
                if not include_hidden and filename.startswith('.'):
                    continue
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, directory)
                files.append((rel_path, full_path))
    else:
        for item in dir_path.iterdir():
            if item.is_file():
                if not include_hidden and item.name.startswith('.'):
                    continue
                rel_path = item.name
                files.append((rel_path, str(item)))

    # Sort for deterministic output
    files.sort(key=lambda x: x[0])

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# SHA-256 checksums for {directory}\n")
        f.write(f"# Generated on: {__import__('datetime').datetime.now().isoformat()}\n")
        f.write("# Format: hash  relative_path\n\n")

        for rel_path, full_path in files:
            try:
                checksum = compute_sha256(full_path)
                f.write(f"{checksum}  {rel_path}\n")
            except Exception as e:
                f.write(f"# ERROR computing hash for {rel_path}: {e}\n")


def verify_dataset_shards(
    dataset_name: str,
    manifest_path: str = DEFAULT_MANIFEST_PATH,
    data_dir: str = "data/raw"
) -> bool:
    """
    Verify all shards for a specific dataset against the manifest.

    Args:
        dataset_name: Name of the dataset (e.g., 'WISE', 'RISE').
                      Used to filter manifest entries (files containing this name).
        manifest_path: Path to the manifest file.
        data_dir: Base directory where dataset files are stored.

    Returns:
        True if all shards for the dataset pass verification.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
    """
    results = verify_manifest(manifest_path, data_dir)
    
    # Filter results for the specific dataset
    dataset_results = [
        r for r in results 
        if dataset_name.lower() in r[0].lower()
    ]

    if not dataset_results:
        raise FileNotFoundError(
            f"No files found in manifest for dataset: {dataset_name}"
        )

    all_valid = all(r[1] for r in dataset_results)

    for rel_path, is_valid, message in dataset_results:
        status = "✓" if is_valid else "✗"
        print(f"{status} {rel_path}: {message}")

    return all_valid
