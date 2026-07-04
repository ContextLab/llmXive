"""
Data integrity utilities for checksumming and validation.
Supports SHA-256 checksums for files and directories.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

def compute_file_checksum(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a single file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()

def compute_directory_checksum(
    dir_path: Union[str, Path],
    algorithm: str = "sha256",
    exclude_patterns: Optional[List[str]] = None
) -> str:
    """
    Compute a deterministic checksum for a directory based on its contents.
    Files are processed in sorted order to ensure determinism.

    Args:
        dir_path: Path to the directory.
        algorithm: Hash algorithm to use.
        exclude_patterns: List of glob patterns to exclude (e.g., ['*.log', '__pycache__/*']).

    Returns:
        Hexadecimal digest string representing the directory state.

    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    path = Path(dir_path)
    if not path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    hasher = hashlib.new(algorithm)
    exclude_set = set(exclude_patterns or [])

    # Sort files to ensure deterministic order
    all_files = sorted(path.rglob("*"))
    files_to_hash = []

    for file_path in all_files:
        if file_path.is_file():
            rel_path = str(file_path.relative_to(path))
            # Simple glob matching for exclusion
            if not any(rel_path == pattern or rel_path.endswith(pattern) or rel_path.startswith(pattern.replace("*", "")) for pattern in exclude_set):
                files_to_hash.append((rel_path, file_path))

    # Hash the list of files first to include filenames in the checksum
    list_hash = hashlib.new(algorithm)
    for rel_path, _ in files_to_hash:
        list_hash.update(rel_path.encode("utf-8"))
    hasher.update(list_hash.digest())

    # Hash contents
    for rel_path, file_path in files_to_hash:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

    return hasher.hexdigest()

def generate_manifest(
    base_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    algorithm: str = "sha256"
) -> Dict[str, str]:
    """
    Generate a JSON manifest of checksums for all files in a directory.

    Args:
        base_path: Root directory to scan.
        output_path: Optional path to write the manifest JSON.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    base = Path(base_path)
    manifest = {}

    for file_path in sorted(base.rglob("*")):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(base))
            try:
                checksum = compute_file_checksum(file_path, algorithm)
                manifest[rel_path] = checksum
            except (FileNotFoundError, ValueError) as e:
                manifest[rel_path] = f"ERROR: {e}"

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

    return manifest

def verify_manifest(
    base_path: Union[str, Path],
    manifest_path: Union[str, Path],
    algorithm: str = "sha256"
) -> Dict[str, bool]:
    """
    Verify files against a manifest.

    Args:
        base_path: Root directory where files are located.
        manifest_path: Path to the JSON manifest file.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping file paths to verification status (True if valid).
    """
    base = Path(base_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    results = {}
    for rel_path, expected_checksum in manifest.items():
        file_path = base / rel_path
        if not file_path.exists():
            results[rel_path] = False
            continue

        try:
            actual_checksum = compute_file_checksum(file_path, algorithm)
            results[rel_path] = actual_checksum == expected_checksum
        except Exception:
            results[rel_path] = False

    return results

def verify_single_file(
    file_path: Union[str, Path],
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a single file against an expected checksum.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal digest.
        algorithm: Hash algorithm to use.

    Returns:
        True if checksum matches, False otherwise.
    """
    actual = compute_file_checksum(file_path, algorithm)
    return actual.lower() == expected_checksum.lower()