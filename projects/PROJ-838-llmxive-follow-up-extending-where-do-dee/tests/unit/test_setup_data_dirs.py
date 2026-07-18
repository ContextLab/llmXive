"""
Unit tests for data directory initialization (T008).
Verifies that data/raw and data/processed directories are created with .gitkeep files.
"""
import os
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Mock the config module to use temporary directories during testing
@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project root for testing."""
    # Create a temporary directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Return the temporary path
    return tmp_path

def test_directories_exist(temp_project_root):
    """Test that data/raw and data/processed directories are created."""
    # Import the function to test
    from setup_data_dirs import main
    
    # Change to temp directory to avoid affecting real project structure
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Mock ensure_directories to create dirs in temp location
        with patch('setup_data_dirs.ensure_directories') as mock_ensure:
            mock_ensure.side_effect = lambda path: (Path(temp_project_root) / path).mkdir(parents=True, exist_ok=True)
            
            # Run the setup function
            main()
        
        # Verify directories were created
        assert (temp_project_root / "data" / "raw").exists(), "data/raw directory not created"
        assert (temp_project_root / "data" / "processed").exists(), "data/processed directory not created"
        assert (temp_project_root / "data" / "processed" / "graphs").exists(), "data/processed/graphs directory not created"
        assert (temp_project_root / "data" / "processed" / "figures").exists(), "data/processed/figures directory not created"
        
    finally:
        os.chdir(original_cwd)

def test_gitkeep_files_exist(temp_project_root):
    """Test that .gitkeep files are created in each data directory."""
    from setup_data_dirs import main
    
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Mock ensure_directories
        with patch('setup_data_dirs.ensure_directories') as mock_ensure:
            mock_ensure.side_effect = lambda path: (Path(temp_project_root) / path).mkdir(parents=True, exist_ok=True)
            
            # Run the setup function
            main()
        
        # Verify .gitkeep files exist
        gitkeep_files = [
            "data/raw/.gitkeep",
            "data/processed/.gitkeep",
            "data/processed/graphs/.gitkeep",
            "data/processed/figures/.gitkeep"
        ]
        
        for gitkeep in gitkeep_files:
            full_path = temp_project_root / gitkeep
            assert full_path.exists(), f"{gitkeep} not created"
            assert full_path.is_file(), f"{gitkeep} is not a file"
            
    finally:
        os.chdir(original_cwd)

def test_gitkeep_files_empty(temp_project_root):
    """Test that .gitkeep files are empty (0 bytes)."""
    from setup_data_dirs import main
    
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_project_root)
        
        # Mock ensure_directories
        with patch('setup_data_dirs.ensure_directories') as mock_ensure:
            mock_ensure.side_effect = lambda path: (Path(temp_project_root) / path).mkdir(parents=True, exist_ok=True)
            
            # Run the setup function
            main()
        
        # Verify .gitkeep files are empty
        gitkeep_files = [
            "data/raw/.gitkeep",
            "data/processed/.gitkeep",
            "data/processed/graphs/.gitkeep",
            "data/processed/figures/.gitkeep"
        ]
        
        for gitkeep in gitkeep_files:
            full_path = temp_project_root / gitkeep
            assert full_path.stat().st_size == 0, f"{gitkeep} is not empty"
            
    finally:
        os.chdir(original_cwd)