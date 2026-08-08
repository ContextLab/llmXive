"""
Unit tests for the data directory creation script.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

from code.utils.create_data_dirs import create_data_directories
from code.utils.logger import setup_logger

@pytest.fixture
def temp_config_dir(monkeypatch):
    """Create a temporary directory structure for testing."""
    temp_root = tempfile.mkdtemp()
    temp_data_dir = os.path.join(temp_root, "data")
    
    # Mock the config to use our temp directory
    def mock_get_config():
        return {"data_dir": temp_data_dir}
    
    monkeypatch.setattr("code.utils.create_data_dirs.get_config", mock_get_config)
    
    yield temp_data_dir
    
    # Cleanup
    if os.path.exists(temp_root):
        shutil.rmtree(temp_root)

def test_creates_required_directories(temp_config_dir):
    """Test that all required data directories are created."""
    logger = setup_logger("test_logger")
    
    # Directories should not exist initially (unless created by previous tests)
    required_dirs = ["raw", "processed", "results", "external"]
    
    # Run the function
    created_paths = create_data_directories(logger)
    
    # Verify paths were returned
    assert len(created_paths) == 4
    
    # Verify each directory exists
    for dir_name in required_dirs:
        expected_path = Path(temp_config_dir) / dir_name
        assert expected_path.exists(), f"Directory {expected_path} was not created"
        assert expected_path.is_dir(), f"{expected_path} is not a directory"

def test_handles_existing_directories(temp_config_dir):
    """Test that the function handles pre-existing directories gracefully."""
    logger = setup_logger("test_logger")
    
    # Create one directory manually
    pre_existing = Path(temp_config_dir) / "raw"
    pre_existing.mkdir(parents=True, exist_ok=True)
    
    # Run the function
    created_paths = create_data_directories(logger)
    
    # Should still return all paths
    assert len(created_paths) == 4
    
    # Pre-existing directory should still exist
    assert pre_existing.exists()
