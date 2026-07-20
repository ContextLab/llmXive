"""
Tests for linting configuration setup.
"""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

# We need to ensure the module can be imported
# Since we are testing the logic, we might need to mock the config
# or run it in a temp directory.

def test_ensure_linting_config_creates_files(tmp_path):
    """
    Test that ensure_linting_config creates the necessary configuration files.
    """
    # Mock get_project_root to return our temp directory
    with patch("linting_config.get_project_root", return_value=str(tmp_path)):
        from linting_config import ensure_linting_config
        ensure_linting_config()

        # Check that files were created
        assert (tmp_path / "pyproject.toml").exists()
        assert (tmp_path / ".flake8").exists()
        
        # Verify content contains key settings
        pyproject_content = (tmp_path / "pyproject.toml").read_text()
        assert "[tool.black]" in pyproject_content
        assert "[tool.ruff]" in pyproject_content
        assert "line-length = 88" in pyproject_content

        flake8_content = (tmp_path / ".flake8").read_text()
        assert "[flake8]" in flake8_content
        assert "max-line-length = 88" in flake8_content

def test_ensure_linting_config_skips_existing(tmp_path):
    """
    Test that ensure_linting_config does not overwrite existing files.
    """
    # Create a dummy file first
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text("EXISTING_CONTENT")

    with patch("linting_config.get_project_root", return_value=str(tmp_path)):
        from linting_config import ensure_linting_config
        ensure_linting_config()

        # Verify content was NOT changed
        assert pyproject_path.read_text() == "EXISTING_CONTENT"