"""
Content hashing module for Advancement-Evaluator Agent integration.

This module implements Constitution Principle V: Content Hashing for
reproducibility verification. It provides functions to compute content
hashes for artifacts and record them in the project state file.

Per Constitution Principle V, all artifacts must have their content hashes
recorded in the state file's artifact_hashes map, and the state file's
updated_at timestamp must be updated whenever artifact hashes change.

NOTE: This is a documentation-only task for Advancement-Evaluator Agent
integration. The external agent does not exist yet. This module provides
the infrastructure that the agent will use when it becomes available.

Constitution Principle V Requirements:
1. Content hash recorded in state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml
   under artifact_hashes map
2. updated_at timestamp updated in state file per Constitution Principle V explicit requirement
3. Hash algorithm: SHA-256 (cryptographically secure)
4. Hash computed from complete file contents (not metadata)
"""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Project state file path (per Constitution Principle V)
STATE_FILE_PATH = Path("state/projects/PROJ-552-quantifying-the-complexity-of-knot-diagr.yaml")

# Hash algorithm per Constitution Principle V
HASH_ALGORITHM = "sha256"


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 content hash for a file.

    Per Constitution Principle V, this computes the hash from the complete
    file contents to enable reproducibility verification.

    Args:
        file_path: Path to the file to hash

    Returns:
        Hexadecimal string of the SHA-256 hash (64 characters)

    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read

    Example:
        >>> hash_value = compute_file_hash("data/processed/knots_cleaned.csv")
        >>> print(hash_value)
        'aa5c3bb9a40eb704d737c329d4a6c06dbf916840f8269f69a5c5c2d7abd74c60'
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks for large files
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def compute_string_hash(content: str) -> str:
    """
    Compute SHA-256 content hash for a string.

    Per Constitution Principle V, this computes the hash from the complete
    string contents to enable reproducibility verification.

    Args:
        content: String content to hash

    Returns:
        Hexadecimal string of the SHA-256 hash (64 characters)
    """
    hasher = hashlib.sha256()
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


def load_state_file() -> Dict[str, Any]:
    """
    Load the project state file.

    Returns:
        Dictionary containing the state file contents

    Raises:
        FileNotFoundError: If the state file does not exist
    """
    if not STATE_FILE_PATH.exists():
        # Initialize empty state file if it doesn't exist
        return {
            "project_id": "PROJ-552-quantifying-the-complexity-of-knot-diagr",
            "artifact_hashes": {},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    with open(STATE_FILE_PATH, "r") as f:
        return yaml.safe_load(f)


def save_state_file(state: Dict[str, Any]) -> None:
    """
    Save the project state file.

    Per Constitution Principle V, this updates the updated_at timestamp
    whenever artifact hashes change.

    Args:
        state: Dictionary containing the state file contents
    """
    # Ensure parent directory exists
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Update timestamp per Constitution Principle V
    state["updated_at"] = datetime.now(timezone.utc).isoformat()

    with open(STATE_FILE_PATH, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)


def record_artifact_hash(
    artifact_path: Union[str, Path],
    artifact_name: Optional[str] = None
) -> str:
    """
    Compute and record an artifact's content hash in the state file.

    Per Constitution Principle V, this function:
    1. Computes the SHA-256 hash of the artifact content
    2. Records the hash in the state file's artifact_hashes map
    3. Updates the updated_at timestamp in the state file

    Args:
        artifact_path: Path to the artifact file
        artifact_name: Optional name for the artifact (defaults to filename)

    Returns:
        The computed hash value

    Raises:
        FileNotFoundError: If the artifact file does not exist
    """
    artifact_path = Path(artifact_path)
    if artifact_name is None:
        artifact_name = artifact_path.name

    # Compute hash
    hash_value = compute_file_hash(artifact_path)

    # Load state file
    state = load_state_file()

    # Record hash in artifact_hashes map (per Constitution Principle V)
    state["artifact_hashes"][artifact_name] = {
        "hash": hash_value,
        "path": str(artifact_path),
        "algorithm": HASH_ALGORITHM,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    # Save state file (updates updated_at timestamp per Constitution Principle V)
    save_state_file(state)

    return hash_value


def verify_artifact_hash(
    artifact_path: Union[str, Path],
    expected_hash: str
) -> bool:
    """
    Verify an artifact's content hash matches the expected value.

    Per Constitution Principle V, this enables reproducibility verification
    by checking that artifact content has not changed.

    Args:
        artifact_path: Path to the artifact file
        expected_hash: Expected SHA-256 hash value

    Returns:
        True if hash matches, False otherwise
    """
    actual_hash = compute_file_hash(artifact_path)
    return actual_hash == expected_hash


def get_artifact_hash(artifact_name: str) -> Optional[str]:
    """
    Retrieve the recorded hash for an artifact from the state file.

    Args:
        artifact_name: Name of the artifact (key in artifact_hashes map)

    Returns:
        Hash value if found, None otherwise
    """
    state = load_state_file()
    if artifact_name in state.get("artifact_hashes", {}):
        return state["artifact_hashes"][artifact_name].get("hash")
    return None


def list_recorded_artifacts() -> List[str]:
    """
    List all artifacts with recorded hashes in the state file.

    Returns:
        List of artifact names
    """
    state = load_state_file()
    return list(state.get("artifact_hashes", {}).keys())


def record_multiple_artifact_hashes(
    artifact_paths: List[Union[str, Path]],
    artifact_names: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Compute and record hashes for multiple artifacts.

    Per Constitution Principle V, this updates the updated_at timestamp
    once after all hashes are recorded (not once per artifact).

    Args:
        artifact_paths: List of paths to artifact files
        artifact_names: Optional list of names (defaults to filenames)

    Returns:
        Dictionary mapping artifact names to their hash values
    """
    results = {}

    # Load state file once
    state = load_state_file()

    for i, artifact_path in enumerate(artifact_paths):
        artifact_path = Path(artifact_path)
        if artifact_names is not None:
            artifact_name = artifact_names[i]
        else:
            artifact_name = artifact_path.name

        # Compute hash
        hash_value = compute_file_hash(artifact_path)
        results[artifact_name] = hash_value

        # Record hash
        state["artifact_hashes"][artifact_name] = {
            "hash": hash_value,
            "path": str(artifact_path),
            "algorithm": HASH_ALGORITHM,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

    # Save state file once (updates updated_at timestamp per Constitution Principle V)
    save_state_file(state)

    return results


def generate_hash_report() -> str:
    """
    Generate a human-readable report of all recorded artifact hashes.

    Returns:
        Formatted string report

    Per Constitution Principle V, this report enables audit verification
    of artifact integrity.
    """
    state = load_state_file()
    artifact_hashes = state.get("artifact_hashes", {})

    lines = [
        "=" * 80,
        "ARTIFACT HASH REPORT",
        f"Project: {state.get('project_id', 'Unknown')}",
        f"Last Updated: {state.get('updated_at', 'Unknown')}",
        f"Hash Algorithm: {HASH_ALGORITHM}",
        "=" * 80,
        "",
    ]

    if not artifact_hashes:
        lines.append("No artifacts recorded yet.")
    else:
        for name, info in artifact_hashes.items():
            lines.extend([
                f"Artifact: {name}",
                f"  Path: {info.get('path', 'Unknown')}",
                f"  Hash: {info.get('hash', 'Unknown')}",
                f"  Algorithm: {info.get('algorithm', 'Unknown')}",
                f"  Recorded: {info.get('recorded_at', 'Unknown')}",
                "",
            ])

    lines.append("=" * 80)
    return "\n".join(lines)


# ========================================================================
# Advancement-Evaluator Agent Integration Documentation
# ========================================================================
"""
The Advancement-Evaluator Agent integration follows this workflow:

1. BEFORE processing: Agent loads artifact hashes from state file
2. DURING processing: Agent computes new hashes for modified artifacts
3. AFTER processing: Agent records new hashes and updates updated_at

Integration Points:
- load_state_file(): Agent reads existing artifact hashes
- compute_file_hash(): Agent computes hashes for verification
- record_artifact_hash(): Agent records new/modified artifact hashes
- verify_artifact_hash(): Agent validates artifact integrity
- generate_hash_report(): Agent produces audit documentation

Constitution Principle V Compliance Checklist:
[x] Content hash recorded in state file artifact_hashes map
[x] updated_at timestamp updated when hashes change
[x] SHA-256 algorithm used (cryptographically secure)
[x] Hash computed from complete file contents
[x] Hash includes metadata (algorithm, recorded_at, path)

NOTE: External Advancement-Evaluator Agent does not exist yet.
This module provides the infrastructure for future integration.
"""


if __name__ == "__main__":
    # Example usage for documentation purposes
    print("Content Hashing Module for Advancement-Evaluator Agent Integration")
    print("=" * 70)
    print()
    print("This module implements Constitution Principle V requirements:")
    print("1. Content hash recorded in state file artifact_hashes map")
    print("2. updated_at timestamp updated in state file")
    print()
    print("Example usage:")
    print("  from reproducibility.hashing import record_artifact_hash")
    print("  hash_value = record_artifact_hash('data/processed/knots_cleaned.csv')")
    print("  print(f'Artifact hash: {hash_value}')")
    print()
    print(generate_hash_report())
