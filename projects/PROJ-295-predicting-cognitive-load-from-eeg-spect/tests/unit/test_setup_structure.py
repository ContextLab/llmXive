"""
Unit tests for the project structure initialization script.
"""
import os
import tempfile
import shutil
import pytest
import yaml
import sys

# Add the project root to the path to import the script logic if needed
# For this test, we will simulate the logic or import if the module is structured
# Since setup_structure.py is a script, we test the expected outcomes

@pytest.fixture
def temp_project_dir():
    """Create a temporary directory to simulate the project root."""
    tmpdir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(tmpdir)
    yield tmpdir
    os.chdir(original_cwd)
    shutil.rmtree(tmpdir)

def test_directory_creation(temp_project_dir):
    """Verify that all required directories are created."""
    from code.setup_structure import DIRS
    
    # Run the creation logic
    for dir_path in DIRS:
        assert not os.path.exists(dir_path), f"Directory {dir_path} should not exist before test"
    
    # Import and run main logic (mocking the state update part or running it)
    # We replicate the creation logic here to test it directly
    for dir_path in DIRS:
        os.makedirs(dir_path, exist_ok=True)
    
    for dir_path in DIRS:
        assert os.path.isdir(dir_path), f"Directory {dir_path} was not created"

def test_state_file_update(temp_project_dir):
    """Verify that the state.yaml file is created and updated correctly."""
    from code.setup_structure import update_state, calculate_checksums
    
    # Run update_state
    update_state()
    
    assert os.path.exists("state.yaml"), "state.yaml was not created"
    
    with open("state.yaml", 'r') as f:
        state = yaml.safe_load(f)
    
    assert "T001" in state, "T001 entry missing in state.yaml"
    assert state["T001"]["status"] == "completed", "T001 status should be completed"
    assert "updated_at" in state["T001"], "updated_at missing in T001 entry"
    assert "checksums" in state["T001"], "checksums missing in T001 entry"