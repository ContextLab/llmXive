import os
import sys
import tempfile
import pytest
from pathlib import Path

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from setup_directories import create_directories, verify_structure
import logging

@pytest.fixture
def temp_project_path():
    """Creates a temporary directory to act as the project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "projects" / "PROJ-422-predicting-molecular-permeability-coeffi"
        yield project_root

def test_create_directories_creates_all_folders(temp_project_path):
    """Test that create_directories creates all required subdirectories."""
    logger = logging.getLogger("test")
    
    result = create_directories(str(temp_project_path), logger)
    
    assert result is True
    
    required_dirs = [
        "code/data", "code/models", "code/analysis",
        "data/raw", "data/processed", "data/interim",
        "results", "tests/unit", "tests/integration"
    ]
    
    for dir_name in required_dirs:
        full_path = temp_project_path / dir_name
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"Path {full_path} is not a directory"
        # Check for .gitkeep evidence
        assert (full_path / ".gitkeep").exists(), f".gitkeep missing in {full_path}"

def test_verify_structure_returns_true_after_creation(temp_project_path):
    """Test that verify_structure returns True after directories are created."""
    logger = logging.getLogger("test")
    
    create_directories(str(temp_project_path), logger)
    is_valid = verify_structure(str(temp_project_path), logger)
    
    assert is_valid is True

def test_verify_structure_returns_false_if_missing(temp_project_path):
    """Test that verify_structure returns False if a directory is missing."""
    logger = logging.getLogger("test")
    
    # Create only one directory
    (temp_project_path / "code").mkdir(parents=True)
    
    is_valid = verify_structure(str(temp_project_path), logger)
    
    assert is_valid is False