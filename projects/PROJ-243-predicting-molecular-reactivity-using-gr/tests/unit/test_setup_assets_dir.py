import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

# We need to import the module functions. 
# Since the project structure implies code/setup_assets_dir.py is the script,
# we will test the logic by importing or mocking the config.

def test_create_assets_directory_creates_folder(tmp_path):
    """Test that the function creates the data/assets directory."""
    # Mock config to use our temp directory
    mock_config = {
        "paths": {
            "data": str(tmp_path)
        }
    }

    # Import the function to test
    from setup_assets_dir import create_assets_directory

    result_path = create_assets_directory(mock_config)
    
    expected_path = str(tmp_path / "assets")
    
    assert os.path.exists(expected_path)
    assert result_path == expected_path
    assert os.path.isdir(expected_path)

def test_create_assets_directory_exists(tmp_path):
    """Test that the function handles existing directory gracefully."""
    assets_path = str(tmp_path / "assets")
    os.makedirs(assets_path)
    
    mock_config = {
        "paths": {
            "data": str(tmp_path)
        }
    }

    from setup_assets_dir import create_assets_directory

    result_path = create_assets_directory(mock_config)
    
    assert result_path == assets_path
    assert os.path.isdir(result_path)

def test_create_assets_directory_creates_parent_if_missing(tmp_path):
    """Test that parent data directory is created if missing."""
    # Ensure 'data' subfolder does not exist yet in tmp_path
    data_sub = tmp_path / "data"
    # We simulate that ensure_directories handles the parent, 
    # but our test logic here focuses on the assets creation.
    
    mock_config = {
        "paths": {
            "data": str(data_sub)
        }
    }

    from setup_assets_dir import create_assets_directory

    result_path = create_assets_directory(mock_config)
    
    expected_assets = str(data_sub / "assets")
    assert os.path.exists(expected_assets)
    assert result_path == expected_assets
