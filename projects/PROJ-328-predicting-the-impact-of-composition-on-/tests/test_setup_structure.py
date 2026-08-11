import os
import pytest
from pathlib import Path
import tempfile
import shutil

from setup_project_structure import setup_directories

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_setup_directories_creates_all_folders(temp_project_root):
    """Verify that setup_directories creates all required directories."""
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code/ingestion",
        "code/features",
        "code/models",
        "code/evaluation",
        "code/visualization",
        "tests",
        "models"
    ]

    setup_directories(temp_project_root)

    for dir_path in required_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists(), f"Directory {dir_path} was not created."
        assert full_path.is_dir(), f"{dir_path} exists but is not a directory."

def test_setup_directories_idempotent(temp_project_root):
    """Verify that running setup_directories twice does not cause errors."""
    required_dirs = ["data/raw", "code/models"]
    
    # First run
    setup_directories(temp_project_root)
    
    # Second run
    setup_directories(temp_project_root)
    
    for dir_path in required_dirs:
        full_path = temp_project_root / dir_path
        assert full_path.exists()
