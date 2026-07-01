"""
Checkpointing utilities for state saving/loading to enable pipeline resumption.
Implements Constitution Principle V: Deterministic updates via state hashing.
"""
import json
import os
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional, List

# Default checkpoint directory relative to project root
CHECKPOINT_DIR = Path("results/checkpoints")


def ensure_checkpoint_dir() -> Path:
    """Ensure the checkpoint directory exists, creating it if necessary."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR


def compute_state_hash(state: Dict[str, Any]) -> str:
    """
    Compute a deterministic SHA-256 hash of the state dictionary.
    Used to detect changes in state for versioning and integrity checks.
    """
    # Sort keys to ensure deterministic serialization
    serialized = json.dumps(state, sort_keys=True).encode('utf-8')
    return hashlib.sha256(serialized).hexdigest()


def save_checkpoint(checkpoint_id: str, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> Path:
    """
    Save a checkpoint to disk.

    Args:
        checkpoint_id: Unique identifier for the checkpoint (e.g., 'download_001', 'filter_042')
        state: The state dictionary to save
        metadata: Optional metadata dict (e.g., timestamp, script version)

    Returns:
        Path to the saved checkpoint file
    """
    ensure_checkpoint_dir()
    checkpoint_path = CHECKPOINT_DIR / f"{checkpoint_id}.json"

    # Compute hash of the state for integrity tracking
    state_hash = compute_state_hash(state)

    checkpoint_data = {
        "checkpoint_id": checkpoint_id,
        "state": state,
        "state_hash": state_hash,
        "metadata": metadata or {}
    }

    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint_data, f, indent=2, sort_keys=True)

    return checkpoint_path


def load_checkpoint(checkpoint_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a checkpoint from disk.

    Args:
        checkpoint_id: The identifier of the checkpoint to load

    Returns:
        The state dictionary if found, None otherwise
    """
    checkpoint_path = CHECKPOINT_DIR / f"{checkpoint_id}.json"

    if not checkpoint_path.exists():
        return None

    with open(checkpoint_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Verify integrity
    stored_hash = data.get("state_hash")
    current_hash = compute_state_hash(data["state"])

    if stored_hash != current_hash:
        raise ValueError(f"Checkpoint {checkpoint_id} hash mismatch! "
                         f"Stored: {stored_hash}, Computed: {current_hash}")

    return data["state"]


def delete_checkpoint(checkpoint_id: str) -> bool:
    """
    Delete a checkpoint from disk.

    Args:
        checkpoint_id: The identifier of the checkpoint to delete

    Returns:
        True if deleted, False if not found
    """
    checkpoint_path = CHECKPOINT_DIR / f"{checkpoint_id}.json"
    if checkpoint_path.exists():
        checkpoint_path.unlink()
        return True
    return False


def get_all_checkpoint_ids() -> List[str]:
    """
    List all available checkpoint IDs in the checkpoint directory.

    Returns:
        List of checkpoint IDs (filenames without .json extension)
    """
    if not CHECKPOINT_DIR.exists():
        return []

    return [
        f.stem for f in CHECKPOINT_DIR.iterdir()
        if f.is_file() and f.suffix == '.json'
    ]


def update_checkpoint(checkpoint_id: str, state_updates: Dict[str, Any], metadata_updates: Optional[Dict[str, Any]] = None) -> Path:
    """
    Load an existing checkpoint, update its state, and re-save it.
    If the checkpoint doesn't exist, creates a new one.

    Args:
        checkpoint_id: The identifier for the checkpoint
        state_updates: Dictionary of state values to update/merge
        metadata_updates: Optional dictionary of metadata to update/merge

    Returns:
        Path to the updated checkpoint file
    """
    # Load existing state or start fresh
    existing_state = load_checkpoint(checkpoint_id) or {}

    # Merge updates (state_updates takes precedence)
    merged_state = {**existing_state, **state_updates}

    # Load existing metadata or start fresh
    existing_metadata = None
    checkpoint_path = CHECKPOINT_DIR / f"{checkpoint_id}.json"
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            existing_metadata = json.load(f).get("metadata", {})

    merged_metadata = {}
    if existing_metadata:
        merged_metadata.update(existing_metadata)
    if metadata_updates:
        merged_metadata.update(metadata_updates)

    # Save the updated checkpoint
    return save_checkpoint(checkpoint_id, merged_state, merged_metadata)
