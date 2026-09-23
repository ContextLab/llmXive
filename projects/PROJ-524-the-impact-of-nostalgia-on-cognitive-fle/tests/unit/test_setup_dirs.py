"""
Unit tests for the directory creation logic (Task T001).
Verifies that the setup_dirs module creates the required directories.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the function to test
from code.setup_dirs import create_required_directories
from code.config import get_config

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    tmp_dir = tempfile.mkdtemp()
    yield tmp_dir
    shutil.rmtree(tmp_dir)

def test_create_required_directories(temp_project_root):
    """Test that all required directories are created."""
    # Mock the config to use our temp directory
    mock_config = {
        'project_root': temp_project_root
    }
    
    with patch('code.setup_dirs.get_config', return_value=mock_config):
        created_dirs = create_required_directories()
    
    # Verify the correct number of directories were created
    expected_dirs = [
        'data/raw', 'data/processed', 'data/results', 'data/stimuli',
        'contracts', 'code', 'tests', 'paper'
    ]
    
    assert len(created_dirs) == len(expected_dirs)
    
    # Verify each expected directory exists
    for expected_dir in expected_dirs:
        full_path = Path(temp_project_root) / expected_dir
        assert full_path.exists(), f"Directory {full_path} was not created"
        assert full_path.is_dir(), f"{full_path} is not a directory"

def test_create_required_directories_idempotent(temp_project_root):
    """Test that running the function twice does not cause errors."""
    mock_config = {
        'project_root': temp_project_root
    }
    
    with patch('code.setup_dirs.get_config', return_value=mock_config):
        # Run twice
        create_required_directories()
        create_required_directories()
    
    # Verify directories still exist
    expected_dirs = [
        'data/raw', 'data/processed', 'data/results', 'data/stimuli',
        'contracts', 'code', 'tests', 'paper'
    ]
    
    for expected_dir in expected_dirs:
        full_path = Path(temp_project_root) / expected_dir
        assert full_path.exists()

def test_create_nested_directories(temp_project_root):
    """Test that nested directories (e.g., data/raw) are created correctly."""
    mock_config = {
        'project_root': temp_project_root
    }
    
    with patch('code.setup_dirs.get_config', return_value=mock_config):
        create_required_directories()
    
    # Verify nested structure
    assert (Path(temp_project_root) / 'data' / 'raw').exists()
    assert (Path(temp_project_root) / 'data' / 'processed').exists()
    assert (Path(temp_project_root) / 'data' / 'results').exists()
    assert (Path(temp_project_root) / 'data' / 'stimuli').exists()
