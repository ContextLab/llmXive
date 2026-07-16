"""
Unit tests for code/config.py.
Tests path resolution and environment override logic.
"""
import os
import pytest
from pathlib import Path

from config import get_path_env_override

class TestConfig:
    """Tests for configuration utilities."""

    def test_get_path_env_override_not_set(self, monkeypatch):
        """Test behavior when environment variable is not set."""
        monkeypatch.delenv("PROJECT_DATA_ROOT", raising=False)

        result = get_path_env_override("PROJECT_DATA_ROOT", "default/path")
        assert result == Path("default/path")

    def test_get_path_env_override_set(self, monkeypatch, temp_dir):
        """Test behavior when environment variable is set."""
        test_path = temp_dir / "custom/data"
        monkeypatch.setenv("PROJECT_DATA_ROOT", str(test_path))

        result = get_path_env_override("PROJECT_DATA_ROOT", "default/path")
        assert result == test_path

    def test_get_path_env_override_type_conversion(self, monkeypatch, temp_dir):
        """Test that string path is converted to Path object."""
        test_path_str = str(temp_dir / "string/path")
        monkeypatch.setenv("PROJECT_PATH_VAR", test_path_str)

        result = get_path_env_override("PROJECT_PATH_VAR", "default")
        assert isinstance(result, Path)
        assert str(result) == test_path_str
