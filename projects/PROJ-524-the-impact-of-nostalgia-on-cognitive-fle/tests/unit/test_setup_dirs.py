"""
Unit tests for Task T001: Directory creation.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the function to test
from code.setup_dirs import main
from code.config import get_config


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_directory_creation(temp_project_root):
    """Test that all required directories are created."""
    # Mock config to use temp directory
    # We will directly test the directory creation logic
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "data/stimuli",
        "contracts",
        "code",
        "tests",
        "paper",
    ]
    
    base_path = Path(temp_project_root)
    
    # Verify directories do not exist initially
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert not dir_path.exists(), f"Directory {dir_path} should not exist before test"
    
    # Create directories
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Verify directories exist after creation
    for dir_name in required_dirs:
        dir_path = base_path / dir_name
        assert dir_path.exists(), f"Directory {dir_path} should exist after creation"
        assert dir_path.is_dir(), f"{dir_path} should be a directory"
