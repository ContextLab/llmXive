"""
State Manager for llmXive Automated Science Pipeline.

Computes SHA-256 hashes for derived artifacts and updates the project state
file (state/pipeline_state.yaml) to track artifact integrity.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import yaml

# Project root relative to this file (code/utils/ -> root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_FILE = STATE_DIR / "pipeline_state.yaml"


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_state() -> Dict[str, Any]:
    """
    Load the current state file if it exists.

    Returns:
        Dictionary containing the current state, or an empty dict if not found.
    """
    if not STATE_FILE.exists():
        return {"artifacts": {}, "last_updated": None}

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {"artifacts": {}, "last_updated": None}
        except yaml.YAMLError:
            return {"artifacts": {}, "last_updated": None}


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the state file.

    Args:
        state: The state dictionary to save.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(
    relative_path: str,
    artifact_type: str = "derived",
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compute the hash for a derived artifact and update the state file.

    Args:
        relative_path: Path relative to the project root (e.g., 'data/processed/descriptors.csv').
        artifact_type: Type of artifact (e.g., 'raw', 'processed', 'model', 'figure').
        metadata: Optional additional metadata to store with the artifact entry.

    Returns:
        The computed SHA-256 hash.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    full_path = PROJECT_ROOT / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f"Artifact not found: {full_path}")

    file_hash = compute_sha256(full_path)
    state = load_state()

    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][relative_path] = {
        "hash": file_hash,
        "type": artifact_type,
        "size_bytes": full_path.stat().st_size,
        **(metadata or {})
    }

    save_state(state)
    return file_hash


def verify_artifact(relative_path: str) -> bool:
    """
    Verify the integrity of an artifact by comparing its current hash with the stored hash.

    Args:
        relative_path: Path relative to the project root.

    Returns:
        True if the hash matches, False otherwise.
    """
    full_path = PROJECT_ROOT / relative_path
    if not full_path.exists():
        return False

    state = load_state()
    stored_entry = state.get("artifacts", {}).get(relative_path)

    if not stored_entry or "hash" not in stored_entry:
        return False

    current_hash = compute_sha256(full_path)
    return current_hash == stored_entry["hash"]


def update_state_for_multiple_artifacts(
    artifact_paths: List[str],
    artifact_type: str = "derived",
    metadata_map: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Update state for multiple artifacts at once.

    Args:
        artifact_paths: List of relative paths to update.
        artifact_type: Default type for all artifacts.
        metadata_map: Optional map of path -> specific metadata.

    Returns:
        Dictionary mapping paths to their computed hashes.
    """
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}

    results = {}
    for path in artifact_paths:
        full_path = PROJECT_ROOT / path
        if not full_path.exists():
            # Skip missing files but continue processing others
            continue

        file_hash = compute_sha256(full_path)
        meta = (metadata_map or {}).get(path, {})
        state["artifacts"][path] = {
            "hash": file_hash,
            "type": artifact_type,
            "size_bytes": full_path.stat().st_size,
            **meta
        }
        results[path] = file_hash

    save_state(state)
    return results
