"""
Unit tests for directory management utilities.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# We need to mock the config functions to avoid actual file system dependencies during tests
# but we are testing the logic of ensure_directory and create_base_directory_structure

@pytest.fixture
def mock_project_root(tmp_path):
    """Provide a temporary directory as the project root."""
    with patch('utils.directories.get_project_root', return_value=tmp_path):
        yield tmp_path

@pytest.fixture
def mock_data_path(tmp_path):
    """Provide a temporary directory as the data path."""
    with patch('utils.directories.get_data_path', return_value=tmp_path / "data"):
        yield tmp_path / "data"

@pytest.fixture
def mock_output_path(tmp_path):
    """Provide a temporary directory as the output path."""
    with patch('utils.directories.get_output_path', return_value=tmp_path / "output"):
        yield tmp_path / "output"

def test_ensure_directory_creates_missing_dir(mock_project_root):
    """Test that ensure_directory creates a directory if it doesn't exist."""
    from utils.directories import ensure_directory
    
    test_dir = mock_project_root / "new_test_dir"
    assert not test_dir.exists()
    
    ensure_directory(test_dir)
    
    assert test_dir.exists()
    assert test_dir.is_dir()

def test_ensure_directory_exists_noop(mock_project_root):
    """Test that ensure_directory does nothing if directory already exists."""
    from utils.directories import ensure_directory
    
    existing_dir = mock_project_root / "existing_dir"
    existing_dir.mkdir()
    
    ensure_directory(existing_dir)
    
    # Should still exist and be a directory
    assert existing_dir.exists()
    assert existing_dir.is_dir()

def test_create_base_directory_structure(mock_project_root, mock_data_path, mock_output_path):
    """Test that create_base_directory_structure creates all required directories."""
    from utils.directories import create_base_directory_structure
    
    create_base_directory_structure()
    
    # Check all required directories exist
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/eye-tracking",
        "data/valence",
        "output/plots",
        "output/results"
    ]
    
    for dir_path in required_dirs:
        full_path = mock_project_root / dir_path
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} is not a directory"
    
    # Check validation status file exists
    status_file = mock_project_root / "data" / "processed" / "validation_status.txt"
    assert status_file.exists(), "Validation status file was not created"

def test_verify_directory_structure_all_exist(mock_project_root, mock_data_path, mock_output_path):
    """Test verify_directory_structure returns True when all directories exist."""
    from utils.directories import create_base_directory_structure, verify_directory_structure
    
    create_base_directory_structure()
    
    result = verify_directory_structure()
    assert result is True

def test_verify_directory_structure_missing_dir(mock_project_root):
    """Test verify_directory_structure returns False when a directory is missing."""
    from utils.directories import verify_directory_structure
    
    # Don't create directories, just verify
    result = verify_directory_structure()
    assert result is False
