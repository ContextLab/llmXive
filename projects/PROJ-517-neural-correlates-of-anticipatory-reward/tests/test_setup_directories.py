import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import logging

# Import the function to test
# We assume setup_directories is in the code/ directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from setup_directories import create_directory, main

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for testing."""
    return tmp_path

def test_create_directory_new(temp_dir, caplog):
    """Test creating a new directory."""
    new_dir = temp_dir / "new_test_dir"
    with caplog.at_level(logging.INFO):
        result = create_directory(str(new_dir), logging.getLogger())
    
    assert result is True
    assert new_dir.exists()
    assert new_dir.is_dir()

def test_create_directory_exists(temp_dir, caplog):
    """Test creating a directory that already exists."""
    existing_dir = temp_dir / "existing_dir"
    existing_dir.mkdir()
    
    with caplog.at_level(logging.INFO):
        result = create_directory(str(existing_dir), logging.getLogger())
    
    assert result is True
    assert existing_dir.exists()

def test_create_directory_failure(temp_dir, caplog):
    """Test handling of directory creation failure (e.g., permission denied)."""
    # This is hard to simulate cleanly without root/specific permissions,
    # so we mock the Path.mkdir to raise an exception.
    with patch("setup_directories.Path.mkdir", side_effect=OSError("Permission denied")):
        bad_dir = temp_dir / "bad_dir"
        with caplog.at_level(logging.ERROR):
            result = create_directory(str(bad_dir), logging.getLogger())
        
        assert result is False
        assert not bad_dir.exists()

def test_main_creates_all_directories(temp_dir, caplog):
    """Test that main() creates all expected directories."""
    # Change to temp_dir to simulate project root
    original_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        
        # Mock logging setup to use temp_dir logger or just capture
        with patch("setup_directories.setup_logging", return_value=logging.getLogger()):
            with caplog.at_level(logging.INFO):
                exit_code = main()
        
        assert exit_code == 0
        
        expected_dirs = [
            "code",
            "tests",
            "data/raw",
            "data/processed",
            "data/figures"
        ]
        
        for dir_name in expected_dirs:
            assert (temp_dir / dir_name).exists()
            assert (temp_dir / dir_name).is_dir()
    finally:
        os.chdir(original_cwd)