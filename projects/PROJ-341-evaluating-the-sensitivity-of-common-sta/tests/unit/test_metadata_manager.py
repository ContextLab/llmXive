"""
Unit tests for the metadata manager and checksum utilities.
"""
import os
import json
import tempfile
import pytest
from datetime import datetime
import uuid

# We need to temporarily override the METADATA_PATH for testing
# to avoid polluting the project's actual data directory during unit tests.
# However, since the module imports constants at the top, we need to be careful.
# For this test, we will mock the file operations or use a temporary directory
# and patch the path if necessary. 
# Given the constraints, we will test the logic by creating a temp file 
# and ensuring the functions handle it correctly.

# Note: The actual METADATA_PATH is 'data/simulation_metadata.json'.
# We will test the functions by creating a temporary file and passing it 
# to a modified version of the functions if possible, or by testing the 
# logic on the real file if we clean it up afterwards. 
# To be safe and isolated, we will patch the path in the module.

from code.utils import metadata_manager, checksum_utils

@pytest.fixture(autouse=True)
def setup_and_teardown():
    """
    Setup and teardown for each test.
    We will use a temporary file path to avoid conflicts.
    """
    # Create a temporary directory and file for testing
    temp_dir = tempfile.mkdtemp()
    temp_metadata_path = os.path.join(temp_dir, "test_metadata.json")
    
    # Patch the METADATA_PATH in both modules
    original_path = metadata_manager.METADATA_PATH
    metadata_manager.METADATA_PATH = temp_metadata_path
    checksum_utils.METADATA_PATH = temp_metadata_path
    
    yield temp_metadata_path
    
    # Restore original path
    metadata_manager.METADATA_PATH = original_path
    checksum_utils.METADATA_PATH = original_path
    
    # Cleanup
    if os.path.exists(temp_metadata_path):
        os.remove(temp_metadata_path)
    os.rmdir(temp_dir)

def test_ensure_metadata_file_exists(setup_and_teardown):
    """Test that ensure_metadata_file_exists creates the file with correct schema."""
    temp_path = setup_and_teardown
    # File should not exist yet
    assert not os.path.exists(temp_path)
    
    metadata_manager.ensure_metadata_file_exists()
    
    assert os.path.exists(temp_path)
    
    with open(temp_path, 'r') as f:
        data = json.load(f)
    
    assert "schema_version" in data
    assert "metadata" in data
    assert "simulation_runs" in data
    assert data["metadata"]["status"] == "initialized"
    assert "created_at" in data["metadata"]

def test_load_simulation_metadata_creates_if_missing(setup_and_teardown):
    """Test that load_simulation_metadata creates the file if it doesn't exist."""
    temp_path = setup_and_teardown
    assert not os.path.exists(temp_path)
    
    data = metadata_manager.load_simulation_metadata()
    
    assert os.path.exists(temp_path)
    assert "schema_version" in data

def test_register_run(setup_and_teardown):
    """Test registering a new run."""
    temp_path = setup_and_teardown
    metadata_manager.ensure_metadata_file_exists()
    
    config = {"sample_sizes": [5, 10], "alpha": 0.05}
    seed_config = {"base_seed": 42}
    
    run_id = metadata_manager.register_run(config, seed_config)
    
    assert run_id is not None
    try:
        uuid.UUID(run_id)
    except ValueError:
        pytest.fail("run_id is not a valid UUID")
    
    data = metadata_manager.load_simulation_metadata()
    assert len(data["simulation_runs"]) == 1
    assert data["simulation_runs"][0]["run_id"] == run_id
    assert data["simulation_runs"][0]["config"] == config
    assert data["simulation_runs"][0]["seed_config"] == seed_config
    assert data["simulation_runs"][0]["timestamp_completed"] is None

def test_update_run_status(setup_and_teardown):
    """Test updating run status."""
    temp_path = setup_and_teardown
    metadata_manager.ensure_metadata_file_exists()
    
    config = {"sample_sizes": [5]}
    seed_config = {"base_seed": 42}
    run_id = metadata_manager.register_run(config, seed_config)
    
    completion_time = "2023-10-27T12:00:00Z"
    metadata_manager.update_run_status(run_id, {"timestamp_completed": completion_time})
    
    data = metadata_manager.load_simulation_metadata()
    run = next(r for r in data["simulation_runs"] if r["run_id"] == run_id)
    assert run["timestamp_completed"] == completion_time
    assert data["metadata"]["status"] == "completed"

def test_register_dataset_checksum(setup_and_teardown):
    """Test registering a dataset checksum."""
    temp_path = setup_and_teardown
    metadata_manager.ensure_metadata_file_exists()
    
    # Create a dummy file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(b"test data")
    temp_file.close()
    
    try:
        checksum_utils.register_dataset_checksum("test_dataset", temp_file.name)
        
        data = metadata_manager.load_simulation_metadata()
        assert len(data["dataset_checksums"]) == 1
        
        entry = data["dataset_checksums"][0]
        assert entry["dataset_name"] == "test_dataset"
        assert entry["file_path"] == temp_file.name
        assert entry["checksum_algorithm"] == "sha256"
        assert entry["checksum_value"] == checksum_utils.compute_file_checksum(temp_file.name)
    finally:
        os.remove(temp_file.name)

def test_compute_file_checksum(setup_and_teardown):
    """Test checksum computation."""
    # Create a dummy file
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    content = b"Hello, World!"
    temp_file.write(content)
    temp_file.close()
    
    try:
        checksum = checksum_utils.compute_file_checksum(temp_file.name)
        assert len(checksum) == 64  # SHA256 hex length
        
        # Verify against known value
        import hashlib
        expected = hashlib.sha256(content).hexdigest()
        assert checksum == expected
    finally:
        os.remove(temp_file.name)

def test_verify_checksum(setup_and_teardown):
    """Test checksum verification."""
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    content = b"test content"
    temp_file.write(content)
    temp_file.close()
    
    try:
        checksum = checksum_utils.compute_file_checksum(temp_file.name)
        assert checksum_utils.verify_checksum(temp_file.name, checksum)
        assert not checksum_utils.verify_checksum(temp_file.name, "wrong_checksum")
    finally:
        os.remove(temp_file.name)
