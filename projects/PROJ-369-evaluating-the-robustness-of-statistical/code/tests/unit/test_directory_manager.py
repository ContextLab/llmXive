import os
import json
import tempfile
from pathlib import Path
import pytest

# Patch get_path to use a temporary directory for testing
import src.utils.config as config_module

@pytest.fixture
def temp_test_dir():
    """Create a temporary directory to simulate project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_get_path = config_module.get_path
        
        def mock_get_path(rel_path):
            return tmpdir
        
        config_module.get_path = mock_get_path
        yield tmpdir
        config_module.get_path = original_get_path

def test_setup_directories_creates_all_required(temp_test_dir):
    """Verify that all required directories are created."""
    from src.utils.directory_manager import setup_project_directories
    
    created = setup_project_directories()
    
    # Check that all expected directories are in the created list
    expected_dirs = [
        "src", "src/data", "src/synthesis", "src/analysis", "src/viz", "src/utils",
        "tests/unit", "tests/integration", "tests/contract",
        "data/raw", "data/processed", "data/results",
        "specs", "state"
    ]
    
    for expected in expected_dirs:
        assert expected in created, f"Directory {expected} was not created."
        
    # Verify actual existence on disk
    for expected in expected_dirs:
        full_path = Path(temp_test_dir) / expected
        assert full_path.exists(), f"Directory {full_path} does not exist on disk."
        assert full_path.is_dir(), f"{full_path} is not a directory."

def test_initialize_checksums_creates_state_file(temp_test_dir):
    """Verify that structure_manifest.json is created and valid."""
    from src.utils.directory_manager import setup_project_directories, initialize_checksums
    
    # First create directories
    created = setup_directories()
    
    # Then initialize checksums
    manifest = initialize_checksums(created)
    
    # Check manifest content
    assert "timestamp" in manifest
    assert "project_root" in manifest
    assert "created_directories" in manifest
    assert "verification_status" in manifest
    assert manifest["verification_status"] == "completed"
    
    # Check file existence
    manifest_path = Path(temp_test_dir) / "state" / "structure_manifest.json"
    assert manifest_path.exists(), "structure_manifest.json was not created."
    
    # Verify JSON validity and content
    with open(manifest_path, "r") as f:
        loaded_manifest = json.load(f)
        
    assert loaded_manifest == manifest

def test_full_workflow(temp_test_dir):
    """Test the complete workflow of directory setup and manifest creation."""
    from src.utils.directory_manager import setup_project_directories, initialize_checksums
    
    # Setup
    created = setup_project_directories()
    manifest = initialize_checksums(created)
    
    # Assertions
    assert len(created) > 0
    assert manifest["verification_status"] == "completed"
    
    # Verify all directories exist
    for dir_name in created:
        assert (Path(temp_test_dir) / dir_name).exists()
        
    # Verify manifest exists
    assert (Path(temp_test_dir) / "state" / "structure_manifest.json").exists()
