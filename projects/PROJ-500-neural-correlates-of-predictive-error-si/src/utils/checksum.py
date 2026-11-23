"""
Checksum utilities for data hygiene (FR-009, Constitution III).

Provides functions to compute SHA-256 checksums for files and directories,
save/load manifest files, and verify data integrity.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional, List


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a single file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def compute_directory_checksums(
    directory_path: Path,
    extension_filter: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute SHA-256 checksums for all files in a directory (recursive).

    Args:
        directory_path: Path to the directory to scan.
        extension_filter: Optional list of extensions to include (e.g., ['.csv', '.json']).
                         If None, all files are included.

    Returns:
        Dictionary mapping relative file paths (string) to their SHA-256 hex digest.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")

    checksums = {}
    for root, _, files in os.walk(directory_path):
        for filename in files:
            file_path = Path(root) / filename

            # Apply extension filter if provided
            if extension_filter:
                if file_path.suffix not in extension_filter:
                    continue

            try:
                rel_path = file_path.relative_to(directory_path)
                checksums[str(rel_path)] = compute_file_sha256(file_path)
            except (PermissionError, OSError) as e:
                # Log warning or skip if inaccessible
                continue

    return checksums


def save_checksum_manifest(
    checksums: Dict[str, str],
    manifest_path: Path
) -> None:
    """
    Save a dictionary of checksums to a JSON manifest file.

    Args:
        checksums: Dictionary of relative paths to checksums.
        manifest_path: Path where the JSON manifest will be written.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)


def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the JSON manifest file.

    Returns:
        Dictionary of relative paths to checksums.

    Raises:
        FileNotFoundError: If the manifest does not exist.
        json.JSONDecodeError: If the manifest is not valid JSON.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_checksums(
    directory_path: Path,
    manifest_path: Path,
    extension_filter: Optional[List[str]] = None
) -> bool:
    """
    Verify that files in a directory match the checksums in a manifest.

    Args:
        directory_path: Root directory containing the files.
        manifest_path: Path to the JSON manifest file.
        extension_filter: Optional filter for file extensions (must match manifest generation).

    Returns:
        True if all checksums match, False otherwise.

    Raises:
        FileNotFoundError: If the manifest or any expected file is missing.
    """
    expected_checksums = load_checksum_manifest(manifest_path)
    current_checksums = compute_directory_checksums(directory_path, extension_filter)

    # Check for missing files in current directory compared to manifest
    missing_in_current = set(expected_checksums.keys()) - set(current_checksums.keys())
    if missing_in_current:
        # Log missing files but continue checking others if desired
        # For strict verification, we return False
        return False

    # Check for new files not in manifest (optional strictness)
    # Usually we only care that existing files haven't changed
    # but for hygiene, we might flag unexpected new files.
    # Here we stick to: existing files must match, missing files are a failure.

    for rel_path, expected_hash in expected_checksums.items():
        if rel_path in current_checksums:
            if current_checksums[rel_path] != expected_hash:
                return False
        else:
            return False

    return True


def generate_and_save_manifest(
    directory_path: Path,
    manifest_path: Path,
    extension_filter: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute checksums for a directory and save them to a manifest.

    Args:
        directory_path: Root directory to scan.
        manifest_path: Path to save the JSON manifest.
        extension_filter: Optional list of extensions to include.

    Returns:
        The computed dictionary of checksums.
    """
    checksums = compute_directory_checksums(directory_path, extension_filter)
    save_checksum_manifest(checksums, manifest_path)
    return checksums
