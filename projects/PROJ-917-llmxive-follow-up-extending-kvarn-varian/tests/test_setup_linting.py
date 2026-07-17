"""
Tests for the setup_linting module.
These tests verify that linting and formatting tools are properly configured.
"""
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import shutil

import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_linting import check_tool, create_ruff_config, create_black_config, verify_setup


class TestCheckTool:
    """Tests for the check_tool function."""

    def test_check_tool_returns_true_for_installed_tools(self):
        """Test that check_tool returns True for installed tools."""
        # pip should always be installed
        assert check_tool("pip") is True

    def test_check_tool_returns_false_for_nonexistent_tool(self):
        """Test that check_tool returns False for non-existent tools."""
        assert check_tool("this_tool_definitely_does_not_exist_12345") is False


class TestCreateRuffConfig:
    """Tests for the create_ruff_config function."""

    def test_creates_pyproject_toml_if_not_exists(self):
        """Test that create_ruff_config creates pyproject.toml if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Ensure pyproject.toml doesn't exist
                config_path = Path("pyproject.toml")
                assert not config_path.exists()
                
                # Create config
                create_ruff_config()
                
                # Verify file was created
                assert config_path.exists()
                
                # Verify it contains ruff configuration
                content = config_path.read_text()
                assert "[tool.ruff]" in content
            finally:
                os.chdir(original_dir)

    def test_appends_to_existing_pyproject_toml(self):
        """Test that create_ruff_config appends to existing pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create existing pyproject.toml
                config_path = Path("pyproject.toml")
                config_path.write_text("[project]\nname = \"test\"\n")
                
                # Create config
                create_ruff_config()
                
                # Verify file still exists and contains both sections
                content = config_path.read_text()
                assert "[project]" in content
                assert "[tool.ruff]" in content
            finally:
                os.chdir(original_dir)

    def test_does_not_duplicate_ruff_config(self):
        """Test that create_ruff_config doesn't duplicate existing ruff config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create pyproject.toml with existing ruff config
                config_path = Path("pyproject.toml")
                config_path.write_text("[tool.ruff]\nline-length = 88\n")
                
                # Create config
                create_ruff_config()
                
                # Verify ruff section appears only once
                content = config_path.read_text()
                assert content.count("[tool.ruff]") == 1
            finally:
                os.chdir(original_dir)


class TestCreateBlackConfig:
    """Tests for the create_black_config function."""

    def test_creates_no_separate_file(self):
        """Test that create_black_config doesn't create a separate file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Create config (should use pyproject.toml)
                create_black_config()
                
                # Black config should be in pyproject.toml, not separate file
                assert not Path("black.toml").exists()
            finally:
                os.chdir(original_dir)


class TestVerifySetup:
    """Tests for the verify_setup function."""

    def test_returns_false_when_no_config_file(self):
        """Test that verify_setup returns False when pyproject.toml doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)
                
                # Ensure pyproject.toml doesn't exist
                assert not Path("pyproject.toml").exists()
                
                # Verify setup should return False
                assert verify_setup() is False
            finally:
                os.chdir(original_dir)


class TestToolAvailability:
    """Tests that verify the actual tools are available (may be skipped in CI)."""

    @pytest.mark.skipif(
        not check_tool("pip"),
        reason="pip is not available"
    )
    def test_ruff_can_be_checked(self):
        """Test that ruff can be checked for availability."""
        # This test doesn't require ruff to be installed, just that the check works
        result = check_tool("ruff")
        # Result can be True or False depending on installation
        assert isinstance(result, bool)

    @pytest.mark.skipif(
        not check_tool("pip"),
        reason="pip is not available"
    )
    def test_black_can_be_checked(self):
        """Test that black can be checked for availability."""
        # This test doesn't require black to be installed, just that the check works
        result = check_tool("black")
        # Result can be True or False depending on installation
        assert isinstance(result, bool)