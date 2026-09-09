import os
import tempfile
from pathlib import Path
import pytest
import yaml
import hashlib

# Add code to path if running standalone
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.checksum_registry import (
    load_state, 
    save_state, 
    register_raw_data_checksum, 
    get_raw_data_checksums,
    STATE_FILE,
    STATE_DIR
)

@pytest.fixture
def temp_state_file(tmp_path):
    """Create a temporary state file for testing."""
    temp_dir = tmp_path / "state" / "projects"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / "PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml"
    
    # Mock the module constants
    import utils.checksum_registry as reg
    original_file = reg.STATE_FILE
    original_dir = reg.STATE_DIR
    
    reg.STATE_FILE = temp_file
    reg.STATE_DIR = temp_dir
    
    yield temp_file
    
    # Restore
    reg.STATE_FILE = original_file
    reg.STATE_DIR = original_dir

def test_load_state_empty(temp_state_file):
    """Test loading an empty state."""
    state = load_state()
    assert "project_id" in state
    assert "artifact_hashes" in state
    assert "raw_data" in state["artifact_hashes"]

def test_register_checksum(temp_state_file):
    """Test registering a checksum for a file."""
    # Create a temporary data file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".parquet") as f:
        f.write(b"test data content")
        temp_data_path = f.name

    try:
        # Calculate expected checksum
        expected_checksum = hashlib.sha256(b"test data content").hexdigest()
        
        # Register
        result_checksum = register_raw_data_checksum("test_source", temp_data_path)
        
        # Verify result
        assert result_checksum == expected_checksum
        
        # Verify state file
        state = load_state()
        assert "test_source" in state["artifact_hashes"]["raw_data"]
        assert state["artifact_hashes"]["raw_data"]["test_source"]["checksum"] == expected_checksum
        assert state["artifact_hashes"]["raw_data"]["test_source"]["file_path"] == temp_data_path
    finally:
        os.unlink(temp_data_path)

def test_register_missing_file(temp_state_file):
    """Test that registering a missing file raises an error."""
    with pytest.raises(FileNotFoundError):
        register_raw_data_checksum("missing_source", "/nonexistent/path/file.parquet")

def test_get_checksums(temp_state_file):
    """Test retrieving checksums."""
    # Register a dummy
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(b"dummy")
        temp_path = f.name
    
    try:
        register_raw_data_checksum("dummy_source", temp_path)
        checksums = get_raw_data_checksums()
        assert "dummy_source" in checksums
    finally:
        os.unlink(temp_path)
