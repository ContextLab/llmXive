"""
Unit tests for the metadata manager (T005).
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Patch the global path for testing
@pytest.fixture
def mock_metadata_path(tmp_path):
    """Fixture to provide a temporary metadata file path."""
    test_file = tmp_path / "test_metadata.json"
    with patch('code.utils.metadata_manager.METADATA_FILE_PATH', str(test_file)):
        yield str(test_file)

def test_ensure_metadata_file_exists_creates_file(mock_metadata_path):
    """Test that ensure_metadata_file_exists creates a new file if missing."""
    from code.utils.metadata_manager import ensure_metadata_file_exists, load_simulation_metadata

    assert not os.path.exists(mock_metadata_path)
    result_path = ensure_metadata_file_exists()
    
    assert os.path.exists(result_path)
    data = load_simulation_metadata()
    assert "schema_version" in data
    assert "runs" in data
    assert data["runs"] == []

def test_register_run_adds_entry(mock_metadata_path):
    """Test that register_run adds a new run entry."""
    from code.utils.metadata_manager import register_run, load_simulation_metadata

      # Ensure file exists first
    ensure_file = lambda: __import__('code.utils.metadata_manager', fromlist=['ensure_metadata_file_exists']).ensure_metadata_file_exists()
    ensure_file()

    run_params = {"test": "value", "n": 100}
    run_id = register_run(run_params)

    data = load_simulation_metadata()
    assert len(data["runs"]) == 1
    assert data["runs"][0]["run_id"] == run_id
    assert data["runs"][0]["params"] == run_params
    assert data["runs"][0]["status"] == "started"

def test_update_run_status(mock_metadata_path):
    """Test updating run status."""
    from code.utils.metadata_manager import register_run, update_run_status, load_simulation_metadata

    # Ensure file exists
    ensure_file = lambda: __import__('code.utils.metadata_manager', fromlist=['ensure_metadata_file_exists']).ensure_metadata_file_exists()
    ensure_file()

    run_id = register_run({"key": "val"})
    update_run_status(run_id, "completed", outputs=["data.csv"])

    data = load_simulation_metadata()
    run = next(r for r in data["runs"] if r["run_id"] == run_id)
    assert run["status"] == "completed"
    assert run["outputs"] == ["data.csv"]
    assert "completed_at" in run

def test_compute_file_checksum(mock_metadata_path):
    """Test checksum computation."""
    from code.utils.metadata_manager import compute_file_checksum

    # Create a dummy file
    test_file = os.path.join(os.path.dirname(mock_metadata_path), "dummy.txt")
    with open(test_file, 'w') as f:
        f.write("test content")

    checksum = compute_file_checksum(test_file)
    assert len(checksum) == 64  # SHA256 hex length

    os.remove(test_file)

def test_register_dataset_checksum(mock_metadata_path):
    """Test registering a dataset checksum."""
    from code.utils.metadata_manager import register_dataset_checksum, load_simulation_metadata

    # Ensure file exists
    ensure_file = lambda: __import__('code.utils.metadata_manager', fromlist=['ensure_metadata_file_exists']).ensure_metadata_file_exists()
    ensure_file()

    # Create a dummy dataset file
    dataset_file = os.path.join(os.path.dirname(mock_metadata_path), "dataset.csv")
    with open(dataset_file, 'w') as f:
        f.write("col1,col2\n1,2")

    register_dataset_checksum("test_dataset", dataset_file)

    data = load_simulation_metadata()
    assert len(data["datasets"]) == 1
    assert data["datasets"][0]["name"] == "test_dataset"
    assert data["datasets"][0]["checksum"] is not None
    
    os.remove(dataset_file)

def test_schema_structure(mock_metadata_path):
    """Verify the JSON schema structure matches requirements."""
    from code.utils.metadata_manager import ensure_metadata_file_exists, load_simulation_metadata

    ensure_metadata_file_exists()
    data = load_simulation_metadata()

    # Required top-level keys
    assert "schema_version" in data
    assert "created_at" in data
    assert "runs" in data
    assert "datasets" in data
    assert "config" in data

    # Run entry structure
    run_params = {"test": 1}
    from code.utils.metadata_manager import register_run
    run_id = register_run(run_params)
    
    data = load_simulation_metadata()
    run = data["runs"][0]
    assert "run_id" in run
    assert "timestamp" in run
    assert "params" in run
    assert "status" in run
    assert "outputs" in run
