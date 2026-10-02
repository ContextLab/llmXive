import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Import the function to test
from code.setup_processed_dir import ensure_processed_directory, setup_script_logging

@pytest.fixture
def temp_config_dir():
    """Create a temporary directory for testing config and paths."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_ensure_processed_directory_creates_new(temp_config_dir):
    """Test that the function creates the directory if it doesn't exist."""
    # Create a mock config pointing to a subdirectory in temp_config_dir
    mock_config = {
        'paths': {
            'processed': os.path.join(temp_config_dir, 'data', 'processed')
        }
    }
    
    # The directory should not exist yet
    target_dir = mock_config['paths']['processed']
    assert not os.path.exists(target_dir)
    
    # Call the function
    result_path = ensure_processed_directory(mock_config)
    
    # Verify the directory was created
    assert os.path.exists(target_dir)
    assert os.path.isdir(target_dir)
    assert result_path == os.path.abspath(target_dir)

def test_ensure_processed_directory_existing(temp_config_dir):
    """Test that the function handles existing directories gracefully."""
    target_dir = os.path.join(temp_config_dir, 'data', 'processed')
    os.makedirs(target_dir, exist_ok=True)
    
    mock_config = {
        'paths': {
            'processed': target_dir
        }
    }
    
    # Call the function
    result_path = ensure_processed_directory(mock_config)
    
    # Verify the directory still exists and path is correct
    assert os.path.exists(target_dir)
    assert result_path == os.path.abspath(target_dir)

def test_ensure_processed_directory_creates_parents(temp_config_dir):
    """Test that the function creates parent directories if missing."""
    target_dir = os.path.join(temp_config_dir, 'deep', 'nested', 'data', 'processed')
    
    mock_config = {
        'paths': {
            'processed': target_dir
        }
    }
    
    # Call the function
    result_path = ensure_processed_directory(mock_config)
    
    # Verify the full path exists
    assert os.path.exists(target_dir)
    assert os.path.isdir(target_dir)
    assert result_path == os.path.abspath(target_dir)

def test_ensure_processed_directory_raises_on_failure(temp_config_dir):
    """Test that the function raises RuntimeError if creation fails."""
    # Try to create a directory where we don't have permission (e.g., root)
    # This is hard to simulate reliably without root, so we mock os.makedirs to fail
    mock_config = {
        'paths': {
            'processed': os.path.join(temp_config_dir, 'test')
        }
    }
    
    with patch('code.setup_processed_dir.os.makedirs', side_effect=PermissionError("Mock permission error")):
        with pytest.raises(RuntimeError, match="Failed to create directory"):
            ensure_processed_directory(mock_config)
