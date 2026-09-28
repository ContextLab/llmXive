import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.setup_data_structure import setup_directories, get_project_root

@pytest.fixture
def temp_root():
    """Create a temporary directory to simulate a project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_required_directories_exist(temp_root, monkeypatch):
    """Test that setup_directories creates the required structure."""
    # Monkeypatch get_project_root to return our temp directory
    def mock_get_project_root():
        return temp_root
    
    monkeypatch.setattr("src.setup_data_structure.get_project_root", mock_get_project_root)
    
    # Run the setup
    success = setup_directories()
    
    assert success is True, "setup_directories should return True"
    
    required_dirs = [
        "src",
        "src/ingestion",
        "src/preprocessing",
        "src/analysis",
        "src/utils",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit",
        "data/raw",
        "data/processed",
        "data/processed/results",
        "docs",
        "state",
    ]
    
    for dir_name in required_dirs:
        dir_path = temp_root / dir_name
        assert dir_path.is_dir(), f"Directory {dir_path} should exist after setup"

def test_test_directories_exist(temp_root, monkeypatch):
    """Test that specific test subdirectories are created."""
    def mock_get_project_root():
        return temp_root
    
    monkeypatch.setattr("src.setup_directories.get_project_root", mock_get_project_root)
    
    setup_directories()
    
    test_subdirs = [
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]
    
    for subdir in test_subdirs:
        path = temp_root / subdir
        assert path.is_dir(), f"Test subdirectory {path} should exist"