"""
Unit tests for linting setup utilities.
"""
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from linting_setup import check_tool, install_tool


class TestLintingSetup:
    """Tests for linting setup functions."""

    def test_check_tool_returns_bool(self):
        """Test that check_tool returns a boolean."""
        result = check_tool("python")
        assert isinstance(result, bool)

    def test_check_tool_python_exists(self):
        """Test that python tool is detected."""
        result = check_tool("python")
        # Python should always be available
        assert result is True

    def test_check_tool_nonexistent(self):
        """Test that check_tool returns False for nonexistent tool."""
        result = check_tool("this_tool_definitely_does_not_exist_12345")
        assert result is False

    def test_install_tool_already_installed(self):
        """Test install_tool returns True for already installed tool."""
        # Python is always installed
        result = install_tool("python")
        assert result is True

    def test_install_tool_nonexistent(self):
        """Test install_tool returns False for nonexistent package."""
        # This should fail gracefully
        result = install_tool("this_package_definitely_does_not_exist_12345")
        assert result is False

    def test_project_root_in_path(self):
        """Test that project root is in sys.path after import."""
        assert str(project_root) in sys.path
