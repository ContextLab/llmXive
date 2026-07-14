"""
Unit tests for the setup_data_dirs module.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Mock config and logger dependencies for testing
@pytest.fixture
def mock_config():
    return {
        'paths': {
            'project_root': tempfile.mkdtemp()
        }
    }

@pytest.fixture
def cleanup(mock_config):
    yield mock_config
    # Cleanup after test
    shutil.rmtree(mock_config['paths']['project_root'], ignore_errors=True)

def test_create_data_directories(cleanup):
    """Test that create_data_directories creates the required folders."""
    from code.setup_data_dirs import create_data_directories
    
    # Patch get_config to return our mock
    with patch('code.setup_data_dirs.get_config', return_value=cleanup):
        success = create_data_directories()
        
    assert success is True
    
    # Verify directories exist
    base_dir = Path(cleanup['paths']['project_root'])
    assert (base_dir / 'data' / 'raw').exists()
    assert (base_dir / 'data' / 'processed').exists()
    assert (base_dir / 'data' / 'results').exists()

def test_create_data_directories_existing(cleanup):
    """Test that the function handles existing directories gracefully."""
    from code.setup_data_dirs import create_data_directories
    
    # Pre-create the directories
    base_dir = Path(cleanup['paths']['project_root'])
    (base_dir / 'data' / 'raw').mkdir(parents=True)
    
    with patch('code.setup_data_dirs.get_config', return_value=cleanup):
        success = create_data_directories()
        
    assert success is True

def test_create_data_directories_permission_error(cleanup):
    """Test error handling when directory creation fails."""
    from code.setup_data_dirs import create_data_directories
    
    # Mock a scenario where we can't create a directory
    with patch('code.setup_data_dirs.get_config', return_value=cleanup):
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Mock permission error")):
            success = create_data_directories()
            
    assert success is False