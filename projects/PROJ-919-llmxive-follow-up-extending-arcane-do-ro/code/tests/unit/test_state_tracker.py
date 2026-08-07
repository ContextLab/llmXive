"""
Unit tests for the experiment state tracking module.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.lib.state_tracker import (
    generate_run_id,
    hash_parameters,
    log_experiment_state,
    get_latest_run_state,
    get_run_state_by_id,
    update_run_status,
    _get_state_file_path,
    _ensure_state_directory
)

@pytest.fixture
def temp_state_dir():
    """Creates a temporary directory and patches the state file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # We need to patch the path resolution to use our temp dir
        # The module uses a hardcoded path 'data/artifacts/experiment_state.jsonl'
        # relative to cwd. We will mock the _get_state_file_path function.
        
        temp_path = Path(tmpdir) / "experiment_state.jsonl"
        
        def mock_get_path():
            return temp_path
        
        with patch('src.lib.state_tracker._get_state_file_path', mock_get_path):
            yield temp_path

@pytest.fixture
def mock_config():
    """Mock configuration if needed in future extensions."""
    return {}

def test_generate_run_id_format():
    """Test that generated run IDs are valid UUID4 strings."""
    run_id = generate_run_id()
    assert len(run_id) == 36  # Standard UUID string length
    assert run_id.count('-') == 4
    # Check version 4 (random)
    # UUID format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    assert run_id[14] == '4'
    assert run_id[19] in '89ab'

def test_hash_parameters_deterministic():
    """Test that hash is deterministic for same input."""
    params = {"lr": 0.01, "epochs": 10, "model": "llama"}
    h1 = hash_parameters(params)
    h2 = hash_parameters(params)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex length

def test_hash_parameters_order_independent():
    """Test that hash is independent of dictionary key order."""
    params1 = {"a": 1, "b": 2}
    params2 = {"b": 2, "a": 1}
    assert hash_parameters(params1) == hash_parameters(params2)

def test_hash_parameters_empty():
    """Test hash of empty dict."""
    h = hash_parameters({})
    assert len(h) == 64

def test_log_experiment_state_creates_file(temp_state_dir):
    """Test that logging creates the state file."""
    run_id = generate_run_id()
    params = {"test": "value"}
    
    log_experiment_state(run_id, params)
    
    assert temp_state_dir.exists()

def test_log_experiment_state_appends(temp_state_dir):
    """Test that logging appends to the file."""
    run_id_1 = generate_run_id()
    run_id_2 = generate_run_id()
    
    log_experiment_state(run_id_1, {"a": 1})
    log_experiment_state(run_id_2, {"b": 2})
    
    with open(temp_state_dir, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    # Verify content
    record_1 = json.loads(lines[0])
    record_2 = json.loads(lines[1])
    assert record_1['run_id'] == run_id_1
    assert record_2['run_id'] == run_id_2

def test_get_latest_run_state(temp_state_dir):
    """Test retrieving the latest state."""
    run_id = generate_run_id()
    log_experiment_state(run_id, {"key": "val"}, status="started")
    log_experiment_state(run_id, {"key": "val"}, status="finished")
    
    latest = get_latest_run_state()
    assert latest is not None
    assert latest['status'] == 'finished'
    assert latest['run_id'] == run_id

def test_get_run_state_by_id(temp_state_dir):
    """Test retrieving a specific run by ID."""
    run_id = generate_run_id()
    log_experiment_state(run_id, {"x": 1})
    
    found = get_run_state_by_id(run_id)
    assert found is not None
    assert found['run_id'] == run_id
    assert found['parameters']['x'] == 1

    not_found = get_run_state_by_id("non-existent-id")
    assert not_found is None

def test_update_run_status(temp_state_dir):
    """Test updating run status."""
    run_id = generate_run_id()
    log_experiment_state(run_id, {}, status="started")
    
    result = update_run_status(run_id, "completed", "All done")
    assert result is True
    
    # Verify the new record exists
    latest = get_latest_run_state()
    assert latest['status'] == 'completed'
    assert latest['message'] == 'All done'
    assert latest.get('previous_status') == 'started'

def test_update_run_status_not_found(temp_state_dir):
    """Test updating a non-existent run."""
    result = update_run_status("fake-id", "completed")
    assert result is False

def test_state_record_contains_required_fields(temp_state_dir):
    """Test that logged records contain all required fields."""
    run_id = generate_run_id()
    params = {"lr": 0.001}
    
    log_experiment_state(run_id, params, status="running")
    
    latest = get_latest_run_state()
    assert 'run_id' in latest
    assert 'timestamp' in latest
    assert 'parameters_hash' in latest
    assert 'parameters' in latest
    assert 'status' in latest

def test_empty_parameters_hash(temp_state_dir):
    """Test hashing with empty parameters."""
    run_id = generate_run_id()
    log_experiment_state(run_id, {})
    
    latest = get_latest_run_state()
    assert 'parameters_hash' in latest
    # Verify hash matches empty dict hash
    from src.lib.state_tracker import hash_parameters
    assert latest['parameters_hash'] == hash_parameters({})