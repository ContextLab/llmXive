import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")

def compute_string_sha256(content: str) -> str:
    """
    Calculate the SHA256 checksum of a string.

    Args:
        content: String content to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def compute_file_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate a checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm name (default: 'sha256').

    Returns:
        Hexadecimal string of the checksum.
    """
    hasher = hashlib.new(algorithm)
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def verify_file_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify that a file's checksum matches the expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal checksum.
        algorithm: Hash algorithm name (default: 'sha256').

    Returns:
        True if checksums match, False otherwise.
    """
    try:
        actual_checksum = compute_file_checksum(file_path, algorithm)
        return actual_checksum.lower() == expected_checksum.lower()
    except (FileNotFoundError, IOError):
        return False

def generate_checksum_manifest(
    files: Union[list, str],
    manifest_path: Optional[str] = None,
    root_dir: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Generate a manifest of checksums for a list of files.

    This function is designed to be tolerant of different calling conventions:
    1. generate_checksum_manifest([file1, file2]) -> returns dict
    2. generate_checksum_manifest([file1], manifest_path="path") -> writes file, returns path
    3. generate_checksum_manifest([file1], root_dir="path") -> handles root_dir logic if needed

    Args:
        files: List of file paths or a single file path string.
        manifest_path: Optional path to write the manifest JSON. If provided,
                       the manifest is written to disk and the path is returned.
        root_dir: Optional root directory to prepend to file paths (for context).
                  If provided, it is used to resolve relative paths but does not
                  alter the checksum calculation logic itself.

    Returns:
        If manifest_path is provided: returns the manifest_path string.
        Otherwise: returns the manifest dictionary.
    """
    if isinstance(files, str):
        files = [files]

    manifest = {
        "version": "1.0",
        "algorithm": "sha256",
        "files": {}
    }

    for file_path in files:
        # Handle root_dir context if provided
        if root_dir:
            # If file_path is relative, make it absolute relative to root_dir
            # but we only store the original path or the resolved one?
            # Usually manifests store the path relative to the manifest or absolute.
            # We will store the path as provided, but ensure we can read it.
            full_path = Path(root_dir) / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            logger.warning(f"File not found for checksum: {full_path}")
            continue

        try:
            checksum = calculate_sha256(str(full_path))
            # Store with the original relative path if root_dir was used, else the input path
            display_path = file_path if root_dir else file_path
            manifest["files"][display_path] = {
                "checksum": checksum,
                "size_bytes": full_path.stat().st_size
            }
        except Exception as e:
            logger.error(f"Failed to checksum {full_path}: {e}")

    if manifest_path:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Checksum manifest written to {manifest_path}")
        return manifest_path

    return manifest

def load_checksum_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary containing the manifest data.
    """
    path = Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def verify_manifest(manifest_path: str) -> bool:
    """
    Verify all files listed in a checksum manifest.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        True if all files match their checksums, False otherwise.
    """
    try:
        manifest = load_checksum_manifest(manifest_path)
        files = manifest.get("files", {})
        all_valid = True

        for file_path, info in files.items():
            expected = info.get("checksum")
            if not expected:
                logger.warning(f"No checksum found for {file_path} in manifest")
                continue

            if not verify_file_checksum(file_path, expected):
                logger.error(f"Checksum mismatch for {file_path}")
                all_valid = False

        return all_valid
    except Exception as e:
        logger.error(f"Failed to verify manifest: {e}")
        return False