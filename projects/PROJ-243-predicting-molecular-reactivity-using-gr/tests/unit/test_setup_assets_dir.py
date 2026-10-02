"""
Unit tests for the setup_assets_dir script and directory creation logic.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, 'code')
from setup_assets_dir import create_assets_directory, main
from config import get_config

def test_create_assets_directory_exists():
    """Test that create_assets_directory creates the directory if it doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Mock config to use our temp directory
        mock_config = {
            "data_dir": tmpdir,
            "log_dir": os.path.join(tmpdir, "logs"),
            "artifacts_dir": os.path.join(tmpdir, "artifacts"),
            "code_dir": os.path.join(tmpdir, "code"),
            "tests_dir": os.path.join(tmpdir, "tests")
        }
        
        assets_path = os.path.join(tmpdir, "assets")
        assert not os.path.exists(assets_path)
        
        result_path = create_assets_directory(mock_config)
        
        assert os.path.exists(result_path)
        assert result_path == assets_path
        assert os.path.isdir(result_path)

def test_create_assets_directory_already_exists():
    """Test that create_assets_directory handles existing directory gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_config = {
            "data_dir": tmpdir,
            "log_dir": os.path.join(tmpdir, "logs"),
            "artifacts_dir": os.path.join(tmpdir, "artifacts"),
            "code_dir": os.path.join(tmpdir, "code"),
            "tests_dir": os.path.join(tmpdir, "tests")
        }
        
        assets_path = os.path.join(tmpdir, "assets")
        os.makedirs(assets_path, exist_ok=True)
        
        # Should not raise
        result_path = create_assets_directory(mock_config)
        
        assert result_path == assets_path
        assert os.path.isdir(result_path)

def test_main_success():
    """Test that main returns 0 on success."""
    # Mock get_config to return a valid config
    with patch('setup_assets_dir.get_config') as mock_get_config:
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_config.return_value = {
                "data_dir": tmpdir,
                "log_dir": os.path.join(tmpdir, "logs"),
                "artifacts_dir": os.path.join(tmpdir, "artifacts"),
                "code_dir": os.path.join(tmpdir, "code"),
                "tests_dir": os.path.join(tmpdir, "tests")
            }
            
            result = main()
            assert result == 0
            assert os.path.exists(os.path.join(tmpdir, "assets"))

def test_main_failure():
    """Test that main returns 1 on failure (e.g., permission denied)."""
    with patch('setup_assets_dir.create_assets_directory') as mock_create:
        mock_create.side_effect = PermissionError("Permission denied")
        
        result = main()
        assert result == 1