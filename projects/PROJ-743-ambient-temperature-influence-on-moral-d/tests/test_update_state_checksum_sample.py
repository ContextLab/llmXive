import pytest
import yaml
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to test the logic without actually running the full pipeline
# We will mock the file system operations and the state file updates

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure."""
    # Create directories
    data_raw = tmp_path / "data" / "raw"
    data_raw.mkdir(parents=True)
    state_projects = tmp_path / "state" / "projects"
    state_projects.mkdir(parents=True)
    
    # Create a dummy sample file
    sample_file = data_raw / "era5_sample.h5"
    sample_file.write_bytes(b"dummy_hdf5_content_for_testing")
    
    # Create a dummy state file
    state_file = state_projects / "PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
    state_file.write_text("artifact_hashes: {}\nupdated_at: null\n")
    
    return tmp_path, sample_file, state_file

def test_compute_sha256(temp_project_root):
    """Test the SHA-256 computation function."""
    from compute_checksum import compute_sha256
    _, sample_file, _ = temp_project_root
    
    checksum = compute_sha256(sample_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)

def test_update_state_file(temp_project_root):
    """Test updating the state YAML file."""
    from compute_checksum import ensure_state_file_exists, update_state_file
    import logging
    
    _, _, state_file = temp_project_root
    logger = logging.getLogger(__name__)
    
    # Ensure file exists (it should already, but test the function)
    ensure_state_file_exists(state_file)
    
    # Update the specific key
    update_state_file(state_file, "artifact_hashes.era5_sample", "test_checksum_123", logger)
    
    # Verify content
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)
    
    assert data["artifact_hashes"]["era5_sample"] == "test_checksum_123"
    assert "updated_at" in data

def test_main_logic(temp_project_root, capsys):
    """Test the main execution logic of update_state_checksum_sample."""
    # We need to simulate the environment of update_state_checksum_sample
    # Since it imports from update_state_checksum, we can test the flow
    
    from update_state_checksum import compute_sha256, ensure_state_file_exists, update_state_file
    from setup_logging import setup_logging, get_data_quality_logger
    import logging
    
    project_root, sample_file, state_file = temp_project_root
    
    # Setup logging
    setup_logging()
    logger = get_data_quality_logger()
    
    # Compute checksum
    checksum = compute_sha256(sample_file)
    
    # Ensure and update
    ensure_state_file_exists(state_file)
    update_state_file(state_file, "artifact_hashes.era5_sample", checksum, logger)
    
    # Verify file was updated
    with open(state_file, "r") as f:
        data = yaml.safe_load(f)
    
    assert data["artifact_hashes"]["era5_sample"] == checksum
    assert "updated_at" in data
    
    # Check stdout
    captured = capsys.readouterr()
    assert "Success" in captured.out