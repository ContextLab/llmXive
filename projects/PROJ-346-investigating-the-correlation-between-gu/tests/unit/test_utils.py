"""
Unit tests for code/utils.py functions.
These tests verify the helper functions defined in the utils module.
"""
import pytest
import os
from pathlib import Path

# Import the functions from utils.py
# Note: utils.py is in the code/ directory, which is added to path by conftest.py
from utils import (
    get_project_root_path,
    get_data_path,
    get_data_raw_path,
    get_data_processed_path,
    get_data_qc_path,
    ensure_directory,
    sanitize_url,
    sanitize_file_path
)

def test_get_project_root_path():
    """Test that get_project_root_path returns a valid Path object."""
    root = get_project_root_path()
    assert isinstance(root, Path)
    assert root.exists()

def test_get_data_paths():
    """Test that data path helpers return valid subdirectories."""
    root = get_project_root_path()
    data_path = get_data_path()
    raw_path = get_data_raw_path()
    processed_path = get_data_processed_path()
    qc_path = get_data_qc_path()

    assert raw_path.is_relative_to(data_path)
    assert processed_path.is_relative_to(data_path)
    assert qc_path.is_relative_to(data_path)

def test_ensure_directory_creates():
    """Test that ensure_directory creates a non-existent directory."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "new_dir"
        assert not test_dir.exists()
        ensure_directory(test_dir)
        assert test_dir.exists()
        assert test_dir.is_dir()

def test_sanitize_url():
    """Test URL sanitization removes dangerous characters."""
    safe_url = "https://example.com/data"
    unsafe_url = "https://example.com/data?param=value;rm -rf /"
    
    assert sanitize_url(safe_url) == safe_url
    # The sanitized unsafe URL should not contain the semicolon or command
    sanitized = sanitize_url(unsafe_url)
    assert ";" not in sanitized
    assert "rm" not in sanitized

def test_sanitize_file_path():
    """Test file path sanitization."""
    safe_path = "data/raw/file.csv"
    unsafe_path = "data/raw/../../../etc/passwd"
    
    sanitized = sanitize_file_path(unsafe_path)
    # Should not contain parent directory traversal
    assert ".." not in sanitized
    assert "etc" not in sanitized
    assert "passwd" not in sanitized