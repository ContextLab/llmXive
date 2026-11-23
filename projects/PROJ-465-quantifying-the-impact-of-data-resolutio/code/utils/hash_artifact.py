"""
Artifact hashing module for versioning and integrity verification.

This module provides utilities to compute SHA-256 hashes of files and
strings, enabling the verification of data integrity and the tracking
of artifact versions in the research pipeline.
"""
import hashlib
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA-256 hash of a file's contents.

    Reads the file in binary mode and computes the hash in chunks to
    handle large files efficiently without loading the entire file into memory.

    Args:
        file_path: Path to the file to be hashed.

    Returns:
        A hexadecimal string representing the SHA-256 hash of the file.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def compute_string_hash(data: str) -> str:
    """
    Compute the SHA-256 hash of a string.

    Args:
        data: The string to be hashed.

    Returns:
        A hexadecimal string representing the SHA-256 hash of the input string.
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def hash_artifact_manifest(manifest: Dict[str, Any]) -> str:
    """
    Compute a hash of a manifest dictionary.

    Serializes the manifest to a canonical JSON string (sorted keys) and
    computes its hash. This ensures that the same dictionary content always
    produces the same hash, regardless of key order.

    Args:
        manifest: A dictionary representing the artifact metadata.

    Returns:
        A hexadecimal string representing the SHA-256 hash of the manifest.
    """
    canonical_json = json.dumps(manifest, sort_keys=True)
    return compute_string_hash(canonical_json)


def save_hash_manifest(manifest: Dict[str, Any], output_path: Union[str, Path]) -> None:
    """
    Save a hash manifest to a JSON file.

    Args:
        manifest: The dictionary containing artifact hashes and metadata.
        output_path: The path where the manifest JSON file will be saved.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def load_hash_manifest(input_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a hash manifest from a JSON file.

    Args:
        input_path: The path to the manifest JSON file.

    Returns:
        The dictionary containing the manifest data.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def verify_artifact_integrity(
    artifact_path: Union[str, Path],
    expected_hash: str,
    manifest_path: Optional[Union[str, Path]] = None
) -> bool:
    """
    Verify the integrity of an artifact against an expected hash.

    Args:
        artifact_path: Path to the artifact file to verify.
        expected_hash: The expected SHA-256 hash of the artifact.
        manifest_path: Optional path to a manifest file. If provided,
                       the function will check if the artifact hash matches
                       the one stored in the manifest for the artifact's filename.
                       If both `expected_hash` and `manifest_path` are provided,
                       `expected_hash` takes precedence.

    Returns:
        True if the computed hash matches the expected hash, False otherwise.
    """
    computed_hash = compute_file_hash(artifact_path)
    return computed_hash == expected_hash
