"""
Unit tests for the setup_data_directories script.

These tests verify that the required data directory structure is created correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the code directory to the path so we can import the module
# assuming this test runs from the project root or the code directory is accessible
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_data_directories import setup_data_directories


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


def test_creates_data_raw_directory(temp_project_root):
    """Test that data/raw/ is created."""
    setup_data_directories(temp_project_root)
    assert (temp_project_root / "data" / "raw").exists()
    assert (temp_project_root / "data" / "raw").is_dir()


def test_creates_data_processed_directory(temp_project_root):
    """Test that data/processed/ is created."""
    setup_data_directories(temp_project_root)
    assert (temp_project_root / "data" / "processed").exists()
    assert (temp_project_root / "data" / "processed").is_dir()


def test_creates_data_models_directory(temp_project_root):
    """Test that data/models/ is created."""
    setup_data_directories(temp_project_root)
    assert (temp_project_root / "data" / "models").exists()
    assert (temp_project_root / "data" / "models").is_dir()


def test_creates_gitkeep_files(temp_project_root):
    """Test that .gitkeep files are created in the data subdirectories."""
    setup_data_directories(temp_project_root)
    
    assert (temp_project_root / "data" / "raw" / ".gitkeep").exists()
    assert (temp_project_root / "data" / "processed" / ".gitkeep").exists()
    assert (temp_project_root / "data" / "models" / ".gitkeep").exists()


def test_no_error_if_directories_exist(temp_project_root):
    """Test that the function doesn't raise an error if directories already exist."""
    # Pre-create the directories
    (temp_project_root / "data" / "raw").mkdir(parents=True)
    (temp_project_root / "data" / "processed").mkdir(parents=True)
    (temp_project_root / "data" / "models").mkdir(parents=True)
    
    # This should run without raising an exception
    setup_data_directories(temp_project_root)
    
    # Verify they still exist
    assert (temp_project_root / "data" / "raw").exists()
    assert (temp_project_root / "data" / "processed").exists()
    assert (temp_project_root / "data" / "models").exists()