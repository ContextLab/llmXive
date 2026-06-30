"""
Checkpoint module for the Foundation Protocol.

Provides shared serialization, loading, and management of agent and protocol
state to ensure consistency between middleware and direct communication layers.

This module is imported by both `middleware.py` and `direct_comm.py` to ensure
logic equivalence in state handling.
"""
import json
import os
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .utils import get_hash


class CheckpointError(Exception):
    """Custom exception for checkpoint-related errors."""
    pass


def serialize_state(state: Dict[str, Any], include_metadata: bool = True) -> str:
    """
    Serialize a state dictionary to a JSON string.
    
    Args:
        state: The state dictionary to serialize.
        include_metadata: If True, adds timestamp and hash metadata to the output.
        
    Returns:
        A JSON string representation of the state.
        
    Raises:
        CheckpointError: If serialization fails.
    """
    try:
        if include_metadata:
            state["checkpoint_metadata"] = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "foundation_protocol_checkpoint"
            }
        
        return json.dumps(state, indent=2, default=str)
    except (TypeError, ValueError) as e:
        raise CheckpointError(f"Failed to serialize state: {e}")


def deserialize_state(json_str: str) -> Dict[str, Any]:
    """
    Deserialize a JSON string back to a state dictionary.
    
    Args:
        json_str: The JSON string to deserialize.
        
    Returns:
        The deserialized state dictionary.
        
    Raises:
        CheckpointError: If deserialization fails.
    """
    try:
        data = json.loads(json_str)
        # Remove metadata if present for clean state return
        if "checkpoint_metadata" in data:
            del data["checkpoint_metadata"]
        return data
    except json.JSONDecodeError as e:
        raise CheckpointError(f"Failed to deserialize state: {e}")


def save_checkpoint(
    state: Dict[str, Any],
    file_path: Union[str, Path],
    include_metadata: bool = True
) -> str:
    """
    Save a state dictionary to a file.
    
    Args:
        state: The state dictionary to save.
        file_path: Path to the output file.
        include_metadata: If True, adds timestamp and hash metadata.
        
    Returns:
        The SHA-256 hash of the saved file content.
        
    Raises:
        CheckpointError: If file writing fails.
    """
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        content = serialize_state(state, include_metadata)
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        return get_hash(str(path))
    except (IOError, OSError) as e:
        raise CheckpointError(f"Failed to save checkpoint to {file_path}: {e}")


def load_checkpoint(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a state dictionary from a file.
    
    Args:
        file_path: Path to the checkpoint file.
        
    Returns:
        The deserialized state dictionary.
        
    Raises:
        CheckpointError: If file reading or deserialization fails.
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise CheckpointError(f"Checkpoint file not found: {file_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return deserialize_state(content)
    except (IOError, OSError) as e:
        raise CheckpointError(f"Failed to load checkpoint from {file_path}: {e}")


def verify_checkpoint_integrity(file_path: Union[str, Path], expected_hash: str) -> bool:
    """
    Verify the integrity of a checkpoint file against an expected hash.
    
    Args:
        file_path: Path to the checkpoint file.
        expected_hash: The expected SHA-256 hash.
        
    Returns:
        True if the file hash matches the expected hash.
        
    Raises:
        CheckpointError: If the file does not exist.
    """
    actual_hash = get_hash(str(file_path))
    return actual_hash == expected_hash


def create_empty_checkpoint() -> Dict[str, Any]:
    """
    Create a new, empty checkpoint state.
    
    Returns:
        A dictionary representing an empty state.
    """
    return {
        "agent_states": {},
        "message_history": [],
        "protocol_config": {},
        "metrics_snapshot": {}
    }


def merge_checkpoints(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge an update checkpoint into a base checkpoint.
    
    Performs a shallow merge. For nested dictionaries, the update values
    overwrite base values.
    
    Args:
        base: The base state dictionary.
        update: The update state dictionary.
        
    Returns:
        A new merged dictionary.
    """
    merged = base.copy()
    merged.update(update)
    return merged
