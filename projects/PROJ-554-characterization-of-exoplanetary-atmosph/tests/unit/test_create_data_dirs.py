import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from create_data_dirs import create_directories
from utils import setup_logging
import logging

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary directory to act as the project root."""
    return tmp_path

def test_create_directories_creates_missing_dirs(temp_project_root):
    """Test that create_directories creates data/raw and data/processed if they don't exist."""
    # Change to temp directory to simulate project root
    original_cwd = os.getcwd()
    os.chdir(str(temp_project_root))
    
    try:
        # Ensure directories don't exist
        assert not (temp_project_root / "data" / "raw").exists()
        assert not (temp_project_root / "data" / "processed").exists()
        
        # Mock logging to capture output without cluttering test run
        with patch('create_data_dirs.setup_logging') as mock_setup:
            mock_logger = MagicMock()
            mock_setup.return_value = mock_logger
            
            # Run the function
            result = create_directories()
            
            # Verify directories were created
            assert (temp_project_root / "data" / "raw").exists()
            assert (temp_project_root / "data" / "processed").exists()
            assert result is True
            
            # Verify logging calls (optional check)
            assert mock_logger.info.called
    finally:
        os.chdir(original_cwd)

def test_create_directories_handles_existing_dirs(temp_project_root):
    """Test that create_directories handles already existing directories gracefully."""
    original_cwd = os.getcwd()
    os.chdir(str(temp_project_root))
    
    try:
        # Pre-create directories
        (temp_project_root / "data" / "raw").mkdir(parents=True)
        (temp_project_root / "data" / "processed").mkdir(parents=True)
        
        assert (temp_project_root / "data" / "raw").exists()
        assert (temp_project_root / "data" / "processed").exists()
        
        with patch('create_data_dirs.setup_logging') as mock_setup:
            mock_logger = MagicMock()
            mock_setup.return_value = mock_logger
            
            result = create_directories()
            
            # Should still return True
            assert result is True
            
            # Verify directories still exist
            assert (temp_project_root / "data" / "raw").exists()
            assert (temp_project_root / "data" / "processed").exists()
    finally:
        os.chdir(original_cwd)

def test_create_directories_fails_on_permission_error(temp_project_root):
    """Test that create_directories returns False when permission is denied."""
    original_cwd = os.getcwd()
    os.chdir(str(temp_project_root))
    
    try:
        # Create a read-only file where a directory should be
        data_dir = temp_project_root / "data"
        data_dir.mkdir(parents=True)
        
        # Create a file named 'raw' to conflict with directory creation
        raw_path = data_dir / "raw"
        raw_path.touch()
        raw_path.chmod(0o444) # Read-only
        
        with patch('create_data_dirs.setup_logging') as mock_setup:
            mock_logger = MagicMock()
            mock_setup.return_value = mock_logger
            
            result = create_directories()
            
            # Should return False because it can't create the directory
            assert result is False
            
            # Verify error was logged
            assert mock_logger.error.called
    finally:
        os.chdir(original_cwd)
        # Cleanup permissions for temp dir removal
        raw_path = temp_project_root / "data" / "raw"
        if raw_path.exists():
            raw_path.chmod(0o644)
            raw_path.unlink()