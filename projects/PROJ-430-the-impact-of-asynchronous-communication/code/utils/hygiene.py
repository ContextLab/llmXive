"""
Hygiene utilities for the llmXive automated science pipeline.

Implements Constitution Principle V: Data Integrity via Cryptographic Hashing.
Provides functions to compute SHA-256 hashes of files and update state manifests.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Default path for the state manifest
DEFAULT_MANIFEST_PATH = "data/validation/state_manifest.json"


def compute_sha256(file_path: str | Path) -> str:
    """
    Compute the SHA-256 hash of a file's contents.

    Reads the file in chunks to handle large files without excessive memory usage.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for hashing: {file_path}") from e


def load_manifest(manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> Dict[str, Any]:
    """
    Load the state manifest from disk.

    If the manifest does not exist, returns an empty dictionary.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        Dictionary containing the manifest state.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise IOError(f"Failed to load or parse manifest at {manifest_path}") from e


def save_manifest(manifest: Dict[str, Any], manifest_path: str | Path = DEFAULT_MANIFEST_PATH) -> None:
    """
    Save the state manifest to disk.

    Ensures the directory structure exists before writing.

    Args:
        manifest: Dictionary to save.
        manifest_path: Path to the manifest JSON file.
    """
    manifest_path = Path(manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)


def update_state_manifest(
    artifact_path: str | Path,
    manifest_path: str | Path = DEFAULT_MANIFEST_PATH,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Update the state manifest with the hash and metadata of a new artifact.

    This enforces Constitution Principle V by ensuring every processed data
    artifact is tracked with a cryptographic fingerprint.

    Args:
        artifact_path: Path to the artifact file being tracked.
        manifest_path: Path to the manifest file to update.
        metadata: Optional dictionary of additional metadata to store (e.g., processing timestamp, source).

    Returns:
        The computed SHA-256 hash of the artifact.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    artifact_path = Path(artifact_path)
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    # Compute hash
    file_hash = compute_sha256(artifact_path)

    # Load existing manifest
    manifest = load_manifest(manifest_path)

    # Prepare entry
    entry = {
        "path": str(artifact_path),
        "sha256": file_hash,
        "size_bytes": artifact_path.stat().st_size
    }

    # Merge metadata if provided
    if metadata:
        entry.update(metadata)

    # Update manifest (keyed by relative path for stability)
    rel_path = str(artifact_path)
    manifest[rel_path] = entry

    # Save updated manifest
    save_manifest(manifest, manifest_path)

    return file_hash