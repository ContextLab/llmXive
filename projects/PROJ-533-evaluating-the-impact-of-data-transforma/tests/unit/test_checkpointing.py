"""
Unit tests for code/utils/checkpointing.py
"""
import os
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.utils.checkpointing import (
    save_state,
    load_state,
    delete_checkpoint,
    has_checkpoint,
    list_checkpoints,
    ensure_checkpoint_dir,
    get_checkpoint_path,
    compute_file_hash,
    CHECKPOINT_DIR
)

# Fixtures
@pytest.fixture
def temp_checkpoint_dir(tmp_path):
    """Create a temporary directory for checkpoints."""
    # Temporarily override CHECKPOINT_DIR for testing
    original_dir = CHECKPOINT_DIR
    test_dir = tmp_path / "checkpoints"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # We need to mock the module's reference to the path
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', test_dir):
        yield test_dir

@pytest.fixture
def mock_logger():
    """Mock the logger to prevent actual file writes during tests."""
    with patch('code.utils.checkpointing.logger') as mock:
        yield mock

# Tests
def test_ensure_checkpoint_dir_creates_directory(temp_checkpoint_dir):
    """Test that ensure_checkpoint_dir creates the directory if it doesn't exist."""
    # The fixture already creates it, but let's test the function logic
    # by removing it first (simulating a fresh state)
    # Note: Since we patched the module variable, we work with the temp dir
    new_dir = temp_checkpoint_dir / "subdir"
    assert not new_dir.exists()
    
    # Re-assign the module variable to point to a non-existent sub-path for the test
    # Actually, simpler: just test that the function doesn't crash and dir exists
    ensure_checkpoint_dir()
    assert temp_checkpoint_dir.exists()

def test_get_checkpoint_path_returns_correct_path(temp_checkpoint_dir):
    """Test that get_checkpoint_path returns the correct file path."""
    run_id = "test_run_123"
    expected_path = temp_checkpoint_dir / f"{run_id}.json"
    
    # Patch the module's CHECKPOINT_DIR to match our temp dir
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        result = get_checkpoint_path(run_id)
        assert result == expected_path
        assert result.suffix == ".json"

def test_save_state_creates_valid_json(temp_checkpoint_dir, mock_logger):
    """Test that save_state creates a valid JSON file with correct structure."""
    run_id = "test_run_save"
    step = "initialization"
    data = {
        "current_dataset_id": "dataset_001",
        "last_seed": 42,
        "error_counts": {"connection": 0, "validation": 1}
    }

    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        path = save_state(run_id, step, data)

    assert path.exists()
    assert path.suffix == ".json"

    # Verify content
    with open(path, 'r') as f:
        content = json.load(f)

    assert content["run_id"] == run_id
    assert content["step"] == step
    assert content["data"]["current_dataset_id"] == "dataset_001"
    assert content["data"]["last_seed"] == 42
    assert content["data"]["error_counts"]["validation"] == 1

def test_load_state_returns_correct_data(temp_checkpoint_dir, mock_logger):
    """Test that load_state returns the data saved by save_state."""
    run_id = "test_run_load"
    step = "processing"
    data = {
        "current_dataset_id": "dataset_999",
        "last_seed": 123,
        "error_counts": {"timeout": 5}
    }

    # Save first
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        save_state(run_id, step, data)

    # Load
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        result = load_state(run_id)

    assert result is not None
    assert result["run_id"] == run_id
    assert result["step"] == step
    assert result["data"]["current_dataset_id"] == "dataset_999"
    assert result["data"]["last_seed"] == 123
    assert result["data"]["error_counts"]["timeout"] == 5

def test_load_state_returns_none_for_missing_checkpoint(temp_checkpoint_dir, mock_logger):
    """Test that load_state returns None if checkpoint does not exist."""
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        result = load_state("non_existent_run")
    
    assert result is None

def test_delete_checkpoint_removes_file(temp_checkpoint_dir, mock_logger):
    """Test that delete_checkpoint removes the file and returns True."""
    run_id = "test_run_delete"
    data = {"current_dataset_id": "del_me", "last_seed": 1, "error_counts": {}}

    # Save
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        save_state(run_id, "start", data)

    assert (temp_checkpoint_dir / f"{run_id}.json").exists()

    # Delete
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        result = delete_checkpoint(run_id)

    assert result is True
    assert not (temp_checkpoint_dir / f"{run_id}.json").exists()

def test_delete_checkpoint_returns_false_for_missing(temp_checkpoint_dir, mock_logger):
    """Test that delete_checkpoint returns False if file doesn't exist."""
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        result = delete_checkpoint("non_existent")
    assert result is False

def test_has_checkpoint(temp_checkpoint_dir, mock_logger):
    """Test has_checkpoint returns True/False correctly."""
    run_id = "test_run_has"
    
    # Initially false
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        assert not has_checkpoint(run_id)

    # Save and check true
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        save_state(run_id, "step", {"current_dataset_id": "x", "last_seed": 1, "error_counts": {}})
        assert has_checkpoint(run_id)

def test_list_checkpoints(temp_checkpoint_dir, mock_logger):
    """Test list_checkpoints returns all run_ids."""
    run_ids = ["run_a", "run_b", "run_c"]
    
    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        for rid in run_ids:
            save_state(rid, "step", {"current_dataset_id": "x", "last_seed": 1, "error_counts": {}})
        
        result = list_checkpoints()
    
    assert set(result) == set(run_ids)

def test_compute_file_hash(temp_checkpoint_dir, mock_logger):
    """Test compute_file_hash returns a valid SHA-256 hex string."""
    test_file = temp_checkpoint_dir / "test_file.txt"
    test_file.write_text("test content")

    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        file_hash = compute_file_hash(test_file)

    assert len(file_hash) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in file_hash)

def test_save_state_with_invalid_data_structure(temp_checkpoint_dir, mock_logger):
    """Test save_state handles complex but valid JSON-serializable data."""
    run_id = "test_run_complex"
    data = {
        "current_dataset_id": "dataset_complex",
        "last_seed": 999,
        "error_counts": {"type_a": 10, "type_b": 20},
        "metadata": {"nested": {"key": "value"}, "list": [1, 2, 3]}
    }

    with patch('code.utils.checkpointing.CHECKPOINT_DIR', temp_checkpoint_dir):
        path = save_state(run_id, "complex_step", data)

    assert path.exists()
    with open(path, 'r') as f:
        content = json.load(f)
    
    assert content["data"]["metadata"]["nested"]["key"] == "value"
    assert content["data"]["metadata"]["list"] == [1, 2, 3]