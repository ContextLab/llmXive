"""
Unit tests for the configuration module.
"""
import pytest
import sys
from pathlib import Path
from config import ensure_directories

class TestConfig:
    """Tests for configuration functions."""

    def test_ensure_directories_creates_missing(self, tmp_path):
        """Test that ensure_directories creates missing directories."""
        test_data_dir = tmp_path / "data" / "processed"
        
        # Directory should not exist yet
        assert not test_data_dir.exists()
        
        # Call the function
        result = ensure_directories(test_data_dir)
        
        # Directory should now exist
        assert test_data_dir.exists()
        assert result is True

    def test_ensure_directories_exists(self, tmp_path):
        """Test that ensure_directories returns True if dir exists."""
        existing_dir = tmp_path / "already_exists"
        existing_dir.mkdir(parents=True)
        
        result = ensure_directories(existing_dir)
        
        assert result is True
        assert existing_dir.exists()

    def test_ensure_directories_multiple_levels(self, tmp_path):
        """Test creating deeply nested directories."""
        deep_dir = tmp_path / "a" / "b" / "c" / "d"
        
        assert not deep_dir.exists()
        
        result = ensure_directories(deep_dir)
        
        assert result is True
        assert deep_dir.exists()
        assert deep_dir.is_dir()
