"""
Hashing utility for llmXive pipeline.

Provides functions to compute and verify checksums for data artifacts.
This module is a utility setup and does not execute analysis on its own.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from config import ensure_directories


def compute_file_hash(
    file_path: Union[str, Path], algorithm: str = "sha256"
) -> str:
    """
    Compute the hash of a file using the specified algorithm.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_directory_hashes(
    directory_path: Union[str, Path],
    extensions: Optional[List[str]] = None,
    algorithm: str = "sha256",
) -> Dict[str, str]:
    """
    Compute hashes for all files in a directory (recursive).

    Args:
        directory_path: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.json', '.csv']).
                   If None, all files are included.
        algorithm: Hash algorithm to use.

    Returns:
        Dictionary mapping relative file paths to their hex digests.
    """
    directory_path = Path(directory_path)
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory_path}")

    hashes = {}
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            if extensions is None or file_path.suffix in extensions:
                rel_path = file_path.relative_to(directory_path)
                hashes[str(rel_path)] = compute_file_hash(file_path, algorithm)

    return hashes


def verify_file_hash(
    file_path: Union[str, Path], expected_hash: str, algorithm: str = "sha256"
) -> bool:
    """
    Verify that a file's hash matches the expected value.

    Args:
        file_path: Path to the file.
        expected_hash: Expected hexadecimal hash digest.
        algorithm: Hash algorithm to use.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash


def save_hash_manifest(
    output_path: Union[str, Path],
    hashes: Dict[str, str],
    metadata: Optional[Dict] = None,
) -> None:
    """
    Save a dictionary of hashes to a JSON manifest file.

    Args:
        output_path: Path where the manifest will be written.
        hashes: Dictionary of file paths to hash values.
        metadata: Optional dictionary of metadata to include (e.g., algorithm, timestamp).
    """
    output_path = Path(output_path)
    ensure_directories(output_path)

    manifest = {
        "algorithm": "sha256",
        "hashes": hashes,
    }
    if metadata:
        manifest["metadata"] = metadata

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def load_hash_manifest(manifest_path: Union[str, Path]) -> Dict:
    """
    Load a hash manifest from a JSON file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Dictionary containing the manifest data.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    # Example usage for manual verification
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m code.hasher <file_or_dir> [output_manifest.json]")
        sys.exit(1)

    target = Path(sys.argv[1])
    output_manifest = sys.argv[2] if len(sys.argv) > 2 else None

    if target.is_file():
        h = compute_file_hash(target)
        print(f"{target.name}: {h}")
    elif target.is_dir():
        hashes = compute_directory_hashes(target)
        print(f"Found {len(hashes)} files in {target}")
        for rel_path, h in sorted(hashes.items()):
            print(f"  {rel_path}: {h}")

        if output_manifest:
            save_hash_manifest(output_manifest, hashes)
            print(f"Manifest saved to {output_manifest}")
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)
