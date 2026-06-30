"""
Tests for the checkpoint module.

Ensures serialization, loading, and integrity verification work correctly
and that the module can be imported by other components without circular
dependencies.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest

from foundation_protocol.checkpoint import (
    serialize_state,
    deserialize_state,
    save_checkpoint,
    load_checkpoint,
    verify_checkpoint_integrity,
    create_empty_checkpoint,
    merge_checkpoints,
    CheckpointError
)


@pytest.fixture
def sample_state():
    return {
        "agent_id": "test_agent_1",
        "current_episode": 42,
        "message_count": 150,
        "last_action": {"type": "move", "target": "A"},
        "nested_data": {
            "history": [1, 2, 3],
            "config": {"timeout": 500}
        }
    }


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_serialize_deserialize_roundtrip(sample_state):
    """Test that state survives serialization and deserialization."""
    json_str = serialize_state(sample_state, include_metadata=False)
    restored = deserialize_state(json_str)
    
    assert restored == sample_state


def test_serialize_includes_metadata(sample_state):
    """Test that serialization includes metadata when requested."""
    json_str = serialize_state(sample_state, include_metadata=True)
    data = json.loads(json_str)
    
    assert "checkpoint_metadata" in data
    assert "timestamp" in data["checkpoint_metadata"]
    assert data["checkpoint_metadata"]["source"] == "foundation_protocol_checkpoint"


def test_deserialize_removes_metadata(sample_state):
    """Test that deserialization removes metadata from the output."""
    json_str = serialize_state(sample_state, include_metadata=True)
    restored = deserialize_state(json_str)
    
    assert "checkpoint_metadata" not in restored
    assert restored["agent_id"] == sample_state["agent_id"]


def test_save_and_load_checkpoint(sample_state, temp_dir):
    """Test saving to and loading from a file."""
    file_path = temp_dir / "test_checkpoint.json"
    
    hash_val = save_checkpoint(sample_state, file_path)
    assert hash_val is not None
    assert len(hash_val) == 64  # SHA-256 hex length
    
    loaded_state = load_checkpoint(file_path)
    assert loaded_state == sample_state


def test_load_nonexistent_checkpoint(temp_dir):
    """Test that loading a nonexistent file raises an error."""
    file_path = temp_dir / "nonexistent.json"
    
    with pytest.raises(CheckpointError):
        load_checkpoint(file_path)


def test_verify_integrity_success(sample_state, temp_dir):
    """Test successful integrity verification."""
    file_path = temp_dir / "verify_test.json"
    hash_val = save_checkpoint(sample_state, file_path)
    
    assert verify_checkpoint_integrity(file_path, hash_val) is True


def test_verify_integrity_failure(sample_state, temp_dir):
    """Test failed integrity verification with wrong hash."""
    file_path = temp_dir / "verify_fail_test.json"
    save_checkpoint(sample_state, file_path)
    
    wrong_hash = "0" * 64
    assert verify_checkpoint_integrity(file_path, wrong_hash) is False


def test_create_empty_checkpoint():
    """Test creating an empty checkpoint."""
    empty = create_empty_checkpoint()
    
    assert "agent_states" in empty
    assert "message_history" in empty
    assert "protocol_config" in empty
    assert "metrics_snapshot" in empty
    assert empty["agent_states"] == {}
    assert empty["message_history"] == []


def test_merge_checkpoints():
    """Test merging two checkpoints."""
    base = {
        "a": 1,
        "b": {"x": 10, "y": 20},
        "c": [1, 2]
    }
    update = {
        "b": {"y": 99, "z": 30},
        "d": 4
    }
    
    merged = merge_checkpoints(base, update)
    
    assert merged["a"] == 1
    assert merged["b"] == {"y": 99, "z": 30}  # Shallow merge: 'b' fully replaced
    assert merged["d"] == 4
    assert merged["c"] == [1, 2]


def test_save_checkpoint_creates_directories(temp_dir):
    """Test that save_checkpoint creates parent directories."""
    nested_path = temp_dir / "deep" / "nested" / "dir" / "checkpoint.json"
    
    sample = {"test": "data"}
    save_checkpoint(sample, nested_path)
    
    assert nested_path.exists()


def test_serialize_with_datetime():
    """Test serialization of objects with datetime (using default=str)."""
    from datetime import datetime
    state = {
        "time": datetime(2024, 1, 1, 12, 0, 0),
        "value": 123
    }
    
    json_str = serialize_state(state, include_metadata=False)
    restored = deserialize_state(json_str)
    
    # Datetime is converted to string
    assert isinstance(restored["time"], str)
    assert "2024-01-01" in restored["time"]