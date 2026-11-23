"""
Artifact hashing and versioning utilities for llmXive pipeline.
Ensures all output artifacts have content hashes and versioning discipline.
"""
import hashlib
import os
import json
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

# Configure logger
logger = logging.getLogger(__name__)


def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for hashing: {e}")


def compute_file_metadata(file_path: str) -> Dict[str, Any]:
    """
    Compute metadata for a file including hash, size, and modification time.

    Args:
        file_path: Path to the file.

    Returns:
        Dictionary with file metadata.
    """
    stat_info = os.stat(file_path)
    file_hash = compute_sha256(file_path)

    return {
        "path": file_path,
        "size_bytes": stat_info.st_size,
        "sha256": file_hash,
        "modified_timestamp": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
        "created_timestamp": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
    }


def hash_artifact(file_path: str, version: Optional[str] = None) -> Dict[str, Any]:
    """
    Hash an artifact and return versioned metadata.

    Args:
        file_path: Path to the artifact file.
        version: Optional version string (defaults to timestamp).

    Returns:
        Dictionary with artifact metadata including hash and version.
    """
    metadata = compute_file_metadata(file_path)
    metadata["version"] = version or datetime.now().isoformat()
    return metadata


def update_state_file(
    state_file_path: str,
    artifact_path: str,
    artifact_hash: str,
    artifact_version: Optional[str] = None,
) -> None:
    """
    Update the project state file with artifact hash and version.

    Args:
        state_file_path: Path to the state YAML/JSON file.
        artifact_path: Relative path of the artifact.
        artifact_hash: SHA-256 hash of the artifact.
        artifact_version: Version string for the artifact.
    """
    # Ensure state file directory exists
    state_dir = os.path.dirname(state_file_path)
    if state_dir and not os.path.exists(state_dir):
        os.makedirs(state_dir, exist_ok=True)

    # Load existing state or create new
    state_data = {"artifact_hashes": {}, "versions": {}}
    if os.path.exists(state_file_path):
        try:
            with open(state_file_path, "r") as f:
                state_data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load state file: {e}. Creating new state.")

    # Ensure artifact_hashes exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    # Ensure versions exists
    if "versions" not in state_data:
        state_data["versions"] = {}

    # Update hash
    state_data["artifact_hashes"][artifact_path] = artifact_hash

    # Update version
    if artifact_version:
        state_data["versions"][artifact_path] = artifact_version

    # Write back to file
    with open(state_file_path, "w") as f:
        json.dump(state_data, f, indent=2)

    logger.info(f"Updated state file: {artifact_path} -> {artifact_hash}")


def verify_artifact_integrity(
    file_path: str, expected_hash: str, state_key: Optional[str] = None
) -> bool:
    """
    Verify that an artifact's hash matches the expected hash.

    Args:
        file_path: Path to the artifact.
        expected_hash: Expected SHA-256 hash.
        state_key: Optional key in state file to log verification status.

    Returns:
        True if hash matches, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"Artifact not found for verification: {file_path}")
        return False

    actual_hash = compute_sha256(file_path)
    if actual_hash != expected_hash:
        logger.error(
            f"Hash mismatch for {file_path}: expected {expected_hash}, got {actual_hash}"
        )
        return False

    logger.info(f"Artifact integrity verified: {file_path} ({actual_hash})")
    return True


def scan_and_hash_artifacts(
    base_dir: str,
    patterns: list,
    state_file_path: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Scan a directory for artifacts matching patterns, hash them, and update state.

    Args:
        base_dir: Base directory to scan.
        patterns: List of file patterns (e.g., ['*.csv', '*.json']).
        state_file_path: Path to the state file to update.

    Returns:
        Dictionary of artifact paths to their metadata.
    """
    artifacts = {}
    for root, _, files in os.walk(base_dir):
        for file in files:
            if any(file.endswith(p) for p in patterns):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, base_dir)
                try:
                    metadata = hash_artifact(full_path)
                    metadata["relative_path"] = rel_path
                    artifacts[rel_path] = metadata
                    update_state_file(
                        state_file_path, rel_path, metadata["sha256"], metadata["version"]
                    )
                except Exception as e:
                    logger.error(f"Failed to hash {full_path}: {e}")

    return artifacts
