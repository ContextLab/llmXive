"""
Tests for the fallback manager logic.

These tests verify that:
1. The fallback logic is triggered when primary datasets fail
2. The state file is updated with the correct fallback dataset information
3. A clear error is raised after triggering the fallback
"""
import os
import sys
import tempfile
import yaml
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from data.fallback_manager import (
    trigger_fallback, 
    load_state, 
    update_state, 
    FALLBACK_DATASET,
    PROJECT_ROOT,
    STATE_DIR
)

@pytest.fixture
def temp_state_file():
    """Create a temporary state file for testing."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        # Override the STATE_DIR and STATE_FILE for testing
        original_state_dir = STATE_DIR
        original_state_file = os.path.join(STATE_DIR, 'PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml')
        
        # Set up temporary state file
        test_state_dir = os.path.join(tmpdir, 'state', 'projects')
        os.makedirs(test_state_dir, exist_ok=True)
        test_state_file = os.path.join(test_state_dir, 'PROJ-041-evaluating-the-use-of-graph-neural-netwo.yaml')
        
        # Create initial state file
        initial_state = {
            "project_id": "PROJ-041-evaluating-the-use-of-graph-neural-netwo",
            "artifact_hashes": {},
            "updated_at": None,
            "dataset_source": None
        }
        with open(test_state_file, 'w') as f:
            yaml.dump(initial_state, f)
        
        # Patch the module-level variables
        import data.fallback_manager as fallback_module
        fallback_module.STATE_DIR = test_state_dir
        fallback_module.STATE_FILE = test_state_file
        
        yield test_state_file
        
        # Restore original values
        fallback_module.STATE_DIR = original_state_dir
        fallback_module.STATE_FILE = original_state_file

def test_trigger_fallback_updates_state(temp_state_file):
    """Test that trigger_fallback updates the state file correctly."""
    # This will raise an error, so we catch it
    with pytest.raises(RuntimeError) as exc_info:
        trigger_fallback("Test failure reason")
    
    # Verify the error message contains expected information
    assert "NF-BoT-IoT-v3" in str(exc_info.value)
    assert "Fallback triggered" in str(exc_info.value)
    
    # Load the state file and verify it was updated
    state = load_state()
    assert state["dataset_source"] is not None
    assert state["dataset_source"]["name"] == FALLBACK_DATASET["name"]
    assert state["dataset_source"]["version"] == FALLBACK_DATASET["version"]
    assert state["dataset_source"]["url"] == FALLBACK_DATASET["url"]
    assert "fallback_reason" in state["dataset_source"]
    assert state["dataset_source"]["fallback_reason"] == "Test failure reason"
    assert "timestamp" in state["dataset_source"]

def test_trigger_fallback_raises_error(temp_state_file):
    """Test that trigger_fallback raises a RuntimeError."""
    with pytest.raises(RuntimeError) as exc_info:
        trigger_fallback("Test failure reason")
    
    # Verify the error message contains expected information
    assert "Primary dataset unavailable" in str(exc_info.value)
    assert "NF-BoT-IoT-v3" in str(exc_info.value)

def test_fallback_dataset_info():
    """Test that the fallback dataset information is correctly defined."""
    assert FALLBACK_DATASET["name"] == "NF-BoT-IoT-v3"
    assert "version" in FALLBACK_DATASET
    assert "url" in FALLBACK_DATASET
    assert "checksum" in FALLBACK_DATASET
    assert "description" in FALLBACK_DATASET

def test_state_file_creation(temp_state_file):
    """Test that the state file is created if it doesn't exist."""
    # Remove the state file
    os.remove(temp_state_file)
    
    # Trigger fallback (which will create the state file)
    with pytest.raises(RuntimeError):
        trigger_fallback("Test creation")
    
    # Verify the state file was created
    assert os.path.exists(temp_state_file)
    
    # Load and verify the state
    state = load_state()
    assert "project_id" in state
    assert "artifact_hashes" in state
    assert "updated_at" in state
    assert "dataset_source" in state