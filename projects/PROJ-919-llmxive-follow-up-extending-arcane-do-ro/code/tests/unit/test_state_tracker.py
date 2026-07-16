"""
Unit tests for experiment state tracking functionality.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# We need to mock the config to use a temp directory for tests
# so we don't pollute the real data directory
@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary directory structure for state files."""
    state_dir = tmp_path / "data" / "derived" / "states"
    state_dir.mkdir(parents=True)
    return state_dir

@pytest.fixture
def mock_config(temp_state_dir):
    """Patch the config module to use our temp directory."""
    with patch('src.lib.state_tracker.get_project_root', return_value=temp_state_dir.parent.parent):
        with patch('src.lib.state_tracker.STATE_DIR', temp_state_dir):
            with patch('src.lib.state_tracker.STATE_FILE', temp_state_dir / "experiment_state.jsonl"):
                # Re-import to pick up the patched paths
                # Note: In real tests, we might use importlib.reload or a more sophisticated mocking strategy
                # For this simple case, we assume the module is imported fresh or the paths are set correctly
                yield

def test_generate_run_id_format():
    """Test that run IDs follow the expected format."""
    from src.lib.state_tracker import _generate_run_id
    
    run_id = _generate_run_id()
    parts = run_id.split('_')
    
    # Should have at least 3 parts: date_time_microseconds_entropy
    assert len(parts) >= 3
    # First part should be date (YYYYMMDD)
    assert len(parts[0]) == 8
    # Second part should be time (HHMMSS)
    assert len(parts[1]) == 6
    # Third part should be hex entropy (8 chars)
    assert len(parts[2]) == 8
    # Verify entropy is hex
    int(parts[2], 16)

def test_hash_parameters_deterministic():
    """Test that parameter hashing is deterministic."""
    from src.lib.state_tracker import _hash_parameters
    
    params = {"lr": 0.01, "epochs": 10, "model": "test"}
    hash1 = _hash_parameters(params)
    hash2 = _hash_parameters(params)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

def test_hash_parameters_order_independent():
    """Test that parameter order doesn't affect the hash."""
    from src.lib.state_tracker import _hash_parameters
    
    params1 = {"a": 1, "b": 2}
    params2 = {"b": 2, "a": 1}
    
    assert _hash_parameters(params1) == _hash_parameters(params2)

def test_log_experiment_state_creates_file(temp_state_dir, mock_config):
    """Test that logging creates the state file."""
    from src.lib.state_tracker import log_experiment_state
    
    # Ensure file doesn't exist
    state_file = temp_state_dir / "experiment_state.jsonl"
    if state_file.exists():
        state_file.unlink()
    
    result = log_experiment_state(
        run_id="test_run_123",
        parameters={"lr": 0.01},
        status="initialized"
    )
    
    assert state_file.exists()
    assert result["run_id"] == "test_run_123"
    assert result["status"] == "initialized"
    assert "parameter_hash" in result
    assert "timestamp" in result

def test_log_experiment_state_appends(temp_state_dir, mock_config):
    """Test that logging appends to existing file."""
    from src.lib.state_tracker import log_experiment_state
    
    state_file = temp_state_dir / "experiment_state.jsonl"
    
    # Write first entry
    log_experiment_state(run_id="run_1", parameters={"a": 1})
    # Write second entry
    log_experiment_state(run_id="run_2", parameters={"b": 2})
    
    with open(state_file, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    # Verify order
    first = json.loads(lines[0])
    second = json.loads(lines[1])
    assert first["run_id"] == "run_1"
    assert second["run_id"] == "run_2"

def test_get_latest_run_state(temp_state_dir, mock_config):
    """Test retrieving the latest state."""
    from src.lib.state_tracker import log_experiment_state, get_latest_run_state
    
    log_experiment_state(run_id="run_1", parameters={"a": 1})
    log_experiment_state(run_id="run_2", parameters={"b": 2})
    
    latest = get_latest_run_state()
    
    assert latest is not None
    assert latest["run_id"] == "run_2"

def test_get_run_state_by_id(temp_state_dir, mock_config):
    """Test retrieving a specific run by ID."""
    from src.lib.state_tracker import log_experiment_state, get_run_state
    
    log_experiment_state(run_id="run_1", parameters={"a": 1})
    log_experiment_state(run_id="run_2", parameters={"b": 2})
    
    found = get_run_state("run_1")
    not_found = get_run_state("run_999")
    
    assert found is not None
    assert found["run_id"] == "run_1"
    assert not_found is None

def test_update_run_status(temp_state_dir, mock_config):
    """Test updating run status."""
    from src.lib.state_tracker import log_experiment_state, update_run_status, get_run_state
    
    log_experiment_state(run_id="run_1", status="initialized")
    
    # Update status
    success = update_run_status("run_1", "completed", "Finished successfully")
    
    assert success is True
    
    # Check that a new record exists with updated status
    # Note: The function appends a new record, so we need to find the latest one for this run
    # or check the file contents
    with open(temp_state_dir / "experiment_state.jsonl", 'r') as f:
        lines = f.readlines()
    
    # Should have 2 entries now
    assert len(lines) == 2
    
    # The last entry should be the update
    last_entry = json.loads(lines[-1])
    assert last_entry["status"] == "completed"
    assert last_entry["message"] == "Finished successfully"

def test_update_run_status_not_found(temp_state_dir, mock_config):
    """Test updating a non-existent run returns False."""
    from src.lib.state_tracker import update_run_status
    
    success = update_run_status("non_existent_run", "completed")
    assert success is False

def test_state_record_contains_required_fields(temp_state_dir, mock_config):
    """Test that state records contain all required fields."""
    from src.lib.state_tracker import log_experiment_state
    
    result = log_experiment_state(
        run_id="test_run",
        parameters={"param": "value"},
        status="test",
        message="test message"
    )
    
    required_fields = ["run_id", "timestamp", "parameter_hash", "parameters", "status", "message"]
    for field in required_fields:
        assert field in result

def test_empty_parameters_hash(temp_state_dir, mock_config):
    """Test hashing with empty parameters."""
    from src.lib.state_tracker import log_experiment_state
    
    result = log_experiment_state(run_id="test", parameters={})
    assert "parameter_hash" in result
    assert len(result["parameter_hash"]) == 64
