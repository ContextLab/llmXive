"""
Artifact Hashing Utility.

Provides SHA-256 checksumming for project artifacts to ensure data integrity
and reproducibility.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

# Project root is assumed to be the parent of 'code/'
# We calculate it dynamically to remain robust.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def calculate_sha256(file_path: Union[str, Path]) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "rb") as f:
        # Read in chunks to handle large files without memory issues
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def hash_directory(
    directory_path: Union[str, Path],
    extensions: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Calculate SHA-256 hashes for all files in a directory.

    Args:
        directory_path: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.parquet']).
        exclude_dirs: Optional list of directory names to skip (e.g., ['.git', '__pycache__']).

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    dir_path = Path(directory_path)
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    if exclude_dirs is None:
        exclude_dirs = []

    hashes = {}

    for root, dirs, files in os.walk(dir_path):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if extensions:
                if not any(file.endswith(ext) for ext in extensions):
                    continue

            file_path = Path(root) / file
            rel_path = file_path.relative_to(dir_path)

            try:
                file_hash = calculate_sha256(file_path)
                hashes[str(rel_path)] = file_hash
            except (FileNotFoundError, IOError) as e:
                # Log warning or skip if desired, but for now we raise
                raise e

    return hashes


def verify_artifacts(
    manifest_path: Union[str, Path],
    root_dir: Optional[Union[str, Path]] = None
) -> bool:
    """
    Verify file hashes against a manifest JSON file.

    The manifest should be a JSON object where keys are relative file paths
    and values are expected SHA-256 hashes.

    Args:
        manifest_path: Path to the JSON manifest file.
        root_dir: Base directory for resolving relative paths. Defaults to project root.

    Returns:
        True if all hashes match, False otherwise.

    Raises:
        FileNotFoundError: If manifest or a referenced file is missing.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    manifest_file = Path(manifest_path)
    if not manifest_file.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_file}")

    if root_dir is None:
        root_dir = _PROJECT_ROOT
    else:
        root_dir = Path(root_dir)

    with open(manifest_file, "r", encoding="utf-8") as f:
        expected_hashes = json.load(f)

    all_valid = True

    for rel_path, expected_hash in expected_hashes.items():
        full_path = root_dir / rel_path
        if not full_path.is_file():
            print(f"Missing file: {rel_path}")
            all_valid = False
            continue

        try:
            actual_hash = calculate_sha256(full_path)
            if actual_hash != expected_hash:
                print(f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                print(f"Verified: {rel_path}")
        except Exception as e:
            print(f"Error verifying {rel_path}: {e}")
            all_valid = False

    return all_valid


def create_manifest(
    directory_path: Union[str, Path],
    output_path: Union[str, Path],
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Create a JSON manifest of file hashes for a directory.

    Args:
        directory_path: Source directory to hash.
        output_path: Path where the JSON manifest will be written.
        extensions: Optional list of file extensions to include.

    Returns:
        The generated hash dictionary.
    """
    hashes = hash_directory(directory_path, extensions=extensions)

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)

    return hashes
