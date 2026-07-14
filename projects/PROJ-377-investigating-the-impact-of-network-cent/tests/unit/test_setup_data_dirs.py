import os
import shutil
import pytest
from pathlib import Path
import sys

# Add code to path if necessary, assuming this runs from project root or code/
sys.path.insert(0, 'code')
from setup_data_dirs import setup_data_directories

@pytest.fixture
def temp_data_dir(tmp_path):
    """Fixture to create a temporary data directory structure for testing."""
    # Change to temp directory to avoid polluting real project structure during tests
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(original_cwd)

def test_setup_data_directories_creates_folders(temp_data_dir):
    """Test that setup_data_directories creates the required subdirectories."""
    setup_data_directories()
    
    base_path = Path("data")
    
    assert base_path.exists(), "Base 'data' directory should exist"
    
    required_dirs = ["raw", "processed", "artifacts"]
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory {dir_path} should exist"
        assert dir_path.is_dir(), f"{dir_path} should be a directory"

def test_setup_data_directories_idempotent(temp_data_dir):
    """Test that running the setup twice does not raise errors."""
    setup_data_directories()
    setup_data_directories() # Should not raise error
    
    base_path = Path("data")
    assert (base_path / "raw").exists()
    assert (base_path / "processed").exists()
    assert (base_path / "artifacts").exists()
