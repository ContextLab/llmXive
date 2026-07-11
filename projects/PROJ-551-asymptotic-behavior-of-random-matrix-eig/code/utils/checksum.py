"""
Data hygiene utilities for checksums per Constitution Principle III.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Union

from .config import get_project_paths


def compute_file_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Compute SHA-256 (or other hashlib-supported) checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm name (default: 'sha256').

    Returns:
        Hexadecimal digest string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}") from e

    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def compute_directory_checksums(
    root_dir: Union[str, Path],
    extensions: List[str] = None,
    algorithm: str = 'sha256'
) -> Dict[str, str]:
    """
    Compute checksums for all files in a directory tree.

    Args:
        root_dir: Root directory to traverse.
        extensions: Optional list of file extensions to include (e.g. ['.csv', '.npy']).
                   If None, all files are included.
        algorithm: Hash algorithm name.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    root_dir = Path(root_dir)
    if not root_dir.is_dir():
        raise NotADirectoryError(f"Root path is not a directory: {root_dir}")

    checksums = {}

    for file_path in root_dir.rglob('*'):
        if file_path.is_file():
            if extensions is None or file_path.suffix in extensions:
                rel_path = file_path.relative_to(root_dir)
                try:
                    checksums[str(rel_path)] = compute_file_checksum(file_path, algorithm)
                except FileNotFoundError:
                    # Skip files that might be deleted during traversal
                    continue

    return checksums


def save_checksum_manifest(
    checksums: Dict[str, str],
    output_path: Union[str, Path],
    metadata: Dict[str, str] = None
) -> None:
    """
    Save a checksum manifest to a JSON file.

    Args:
        checksums: Dictionary of relative paths to checksums.
        output_path: Path to the output JSON file.
        metadata: Optional metadata dictionary (e.g. timestamp, algorithm used).
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = {
        "algorithm": "sha256",
        "metadata": metadata or {},
        "checksums": checksums
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)


def load_checksum_manifest(manifest_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load a checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary of relative paths to checksums.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data.get("checksums", {})


def verify_checksums(
    root_dir: Union[str, Path],
    manifest_path: Union[str, Path]
) -> Dict[str, bool]:
    """
    Verify files against a saved checksum manifest.

    Args:
        root_dir: Root directory where files are located.
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary mapping relative paths to verification status (True=valid, False=invalid).
    """
    root_dir = Path(root_dir)
    manifest = load_checksum_manifest(manifest_path)
    results = {}

    for rel_path, expected_checksum in manifest.items():
        file_path = root_dir / rel_path
        if not file_path.exists():
            results[rel_path] = False
            continue

        try:
            actual_checksum = compute_file_checksum(file_path)
            results[rel_path] = (actual_checksum == expected_checksum)
        except Exception:
            results[rel_path] = False

    return results