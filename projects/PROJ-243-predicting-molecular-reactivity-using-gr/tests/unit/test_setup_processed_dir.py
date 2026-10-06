import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Mock sys.modules for imports if necessary, though standard libs should work
import sys

@pytest.fixture
def mock_config():
    """Provides a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield {
            'project_root': tmpdir,
            'data_root': os.path.join(tmpdir, 'data'),
            'directories': ['data/processed', 'data/raw', 'artifacts']
        }

def test_ensure_processed_directory_creates_folder(mock_config):
    """Test that ensure_processed_directory creates the data/processed folder."""
    from setup_processed_dir import ensure_processed_directory
    
    # Ensure the parent data folder exists first (simulating ensure_directories behavior)
    data_root = mock_config['data_root']
    os.makedirs(data_root, exist_ok=True)
    
    processed_path = ensure_processed_directory(mock_config)
    
    expected_path = os.path.join(data_root, 'processed')
    assert os.path.isdir(processed_path)
    assert processed_path == expected_path
    assert os.access(processed_path, os.W_OK)

def test_ensure_processed_directory_idempotent(mock_config):
    """Test that calling the function multiple times doesn't raise errors."""
    from setup_processed_dir import ensure_processed_directory
    
    data_root = mock_config['data_root']
    os.makedirs(data_root, exist_ok=True)
    
    # First call
    path1 = ensure_processed_directory(mock_config)
    # Second call
    path2 = ensure_processed_directory(mock_config)
    
    assert path1 == path2
    assert os.path.isdir(path1)

def test_ensure_processed_directory_fails_on_unwritable_path(mock_config):
    """Test that the function raises RuntimeError if directory is not writable."""
    from setup_processed_dir import ensure_processed_directory
    
    # Create a read-only directory scenario (simplified for unit test)
    # We mock os.makedirs to raise an error to simulate failure
    with patch('setup_processed_dir.os.makedirs', side_effect=OSError("Permission denied")):
        with pytest.raises(RuntimeError, match="Failed to create processed directory"):
            ensure_processed_directory(mock_config)
