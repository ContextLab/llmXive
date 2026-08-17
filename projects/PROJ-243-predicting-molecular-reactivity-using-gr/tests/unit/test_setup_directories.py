import os
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# We need to mock the config to use a temporary directory for testing
@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_config(temp_project_root):
    """Mock the get_config function to return our temp directory."""
    config_mock = MagicMock()
    config_mock.get.return_value = temp_project_root
    with patch('setup_directories.get_config', return_value=config_mock):
        with patch('setup_directories.ensure_directories'):
            yield

def test_create_directories(temp_project_root, mock_config):
    """Test that create_directories creates the required folder structure."""
    from setup_directories import create_directories
    import logging

    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    
    # Call the function
    create_directories(logger)
    
    # Define expected directories relative to temp_project_root
    expected_dirs = [
        "data/raw",
        "data/processed",
        "data/assets",
        "code",
        "artifacts",
        "tests",
        "artifacts/logs",
        "artifacts/weights",
        "figures"
    ]
    
    for dir_path in expected_dirs:
        full_path = os.path.join(temp_project_root, dir_path)
        assert os.path.exists(full_path), f"Directory {full_path} was not created."
        assert os.path.isdir(full_path), f"{full_path} exists but is not a directory."

def test_create_directories_idempotent(temp_project_root, mock_config):
    """Test that running create_directories twice does not cause errors."""
    from setup_directories import create_directories
    import logging

    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)
    
    # Run twice
    create_directories(logger)
    create_directories(logger)
    
    # Verify existence again
    expected_dirs = ["data/processed", "data/raw", "data/assets"]
    for dir_path in expected_dirs:
        full_path = os.path.join(temp_project_root, dir_path)
        assert os.path.exists(full_path)
