import os
import pytest
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ensure_test_dir import ensure_test_directory
from config import get_path


def test_ensure_test_directory_creates_if_missing(tmp_path):
    """Test that ensure_test_directory creates the directory if it doesn't exist."""
    # Mock the get_path function to return a subdirectory of tmp_path
    mock_test_path = tmp_path / "data" / "test"
    
    with patch('ensure_test_dir.get_path', return_value=mock_test_path):
        result_path = ensure_test_directory()
    
    assert result_path.exists()
    assert result_path.is_dir()
    assert result_path == mock_test_path


def test_ensure_test_directory_verifies_existing(tmp_path):
    """Test that ensure_test_directory verifies an existing directory."""
    existing_path = tmp_path / "data" / "test"
    existing_path.mkdir(parents=True, exist_ok=True)
    
    with patch('ensure_test_dir.get_path', return_value=existing_path):
        result_path = ensure_test_directory()
    
    assert result_path.exists()
    assert result_path.is_dir()
    assert result_path == existing_path


def test_ensure_test_directory_uses_custom_path(tmp_path):
    """Test that ensure_test_directory accepts and uses a custom path."""
    custom_path = tmp_path / "custom" / "test"
    
    result_path = ensure_test_directory(path=custom_path)
    
    assert result_path.exists()
    assert result_path.is_dir()
    assert result_path == custom_path


def test_ensure_test_directory_creates_parent_if_needed(tmp_path):
    """Test that ensure_test_directory creates parent directories if needed."""
    # Start with a path where only the root exists
    deep_path = tmp_path / "deep" / "nested" / "data" / "test"
    
    with patch('ensure_test_dir.get_path', return_value=deep_path):
        result_path = ensure_test_directory()
    
    assert result_path.exists()
    assert result_path.is_dir()
    # Verify the full path was created
    assert (tmp_path / "deep" / "nested" / "data").exists()
