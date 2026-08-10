import os
from pathlib import Path
import pytest
import yaml
import json
from src.utils.directory_manager import (
    setup_project_directories,
    initialize_checksums,
    REQUIRED_DIRS
)
from src.utils.config import get_path

@pytest.fixture
def temp_test_dir(tmp_path):
    """
    Creates a temporary directory to simulate the project root for testing.
    Note: In a real integration test, we might run against the actual project root,
    but for unit testing the logic, we verify the function returns the correct structure.
    """
    return tmp_path

def test_setup_directories_creates_all_required(temp_test_dir, monkeypatch):
    """
    Verifies that setup_project_directories creates the expected directory structure.
    """
    # Monkeypatch get_path to return our temp directory
    def mock_get_path(suffix):
        if suffix == "":
            return str(temp_test_dir)
        return str(temp_test_dir / suffix)
    
    monkeypatch.setattr("src.utils.directory_manager.get_path", mock_get_path)
    monkeypatch.setattr("src.utils.config.get_path", mock_get_path)

    # Run the setup
    created_paths = setup_project_directories()

    # Verify all expected directories exist
    for dir_name in REQUIRED_DIRS:
        expected_path = temp_test_dir / dir_name
        assert expected_path.exists(), f"Directory {dir_name} was not created"
        assert expected_path.is_dir(), f"{dir_name} is not a directory"

    # Verify the returned list matches created paths
    assert len(created_paths) == len(REQUIRED_DIRS)

def test_initialize_checksums_creates_state_file(temp_test_dir, monkeypatch):
    """
    Verifies that initialize_checksums writes the structure_manifest.json.
    """
    def mock_get_path(suffix):
        if suffix == "":
            return str(temp_test_dir)
        return str(temp_test_dir / suffix)
    
    monkeypatch.setattr("src.utils.directory_manager.get_path", mock_get_path)
    monkeypatch.setattr("src.utils.config.get_path", mock_get_path)

    # Create dummy paths
    dummy_paths = [str(temp_test_dir / "src"), str(temp_test_dir / "data")]

    # Run initialization
    manifest = initialize_checksums(dummy_paths)

    # Verify manifest file exists
    manifest_path = temp_test_dir / "state" / "structure_manifest.json"
    assert manifest_path.exists(), "structure_manifest.json was not created"

    # Verify content
    with open(manifest_path, "r") as f:
        content = json.load(f)
    
    assert "created_at" in content
    assert "directories" in content
    assert "status" in content
    assert content["status"] == "complete"