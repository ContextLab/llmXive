"""
Unit tests for linting configuration and tool verification.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from code.linting_config import (
    verify_tools_installed,
    run_ruff_check,
    run_black_check,
    RUFF_CONFIG,
    BLACK_CONFIG,
)


class TestLintingConfig:
    """Tests for linting configuration constants and functions."""

    def test_ruff_config_structure(self):
        """Verify RUFF_CONFIG has required keys."""
        assert "select" in RUFF_CONFIG
        assert "ignore" in RUFF_CONFIG
        assert "line-length" in RUFF_CONFIG
        assert "target-version" in RUFF_CONFIG
        assert RUFF_CONFIG["line-length"] == 88
        assert RUFF_CONFIG["target-version"] == "py39"

    def test_black_config_structure(self):
        """Verify BLACK_CONFIG has required keys."""
        assert "line-length" in BLACK_CONFIG
        assert "target-version" in BLACK_CONFIG
        assert BLACK_CONFIG["line-length"] == 88
        assert BLACK_CONFIG["target-version"] == ["py39"]

    @patch("code.linting_config.subprocess.run")
    def test_verify_tools_installed_success(self, mock_run):
        """Test verify_tools_installed when tools are present."""
        mock_run.return_value = MagicMock(returncode=0)
        
        # Should not raise
        verify_tools_installed()
        
        # Verify subprocess was called for both tools
        assert mock_run.call_count == 2

    @patch("code.linting_config.subprocess.run")
    def test_verify_tools_installed_ruff_missing(self, mock_run):
        """Test verify_tools_installed when ruff is missing."""
        # First call (ruff) fails
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, "ruff"),
            MagicMock(returncode=0),  # black (won't be reached)
        ]
        
        with pytest.raises(RuntimeError) as exc_info:
            verify_tools_installed()
        
        assert "ruff is not installed" in str(exc_info.value)

    @patch("code.linting_config.subprocess.run")
    def test_verify_tools_installed_black_missing(self, mock_run):
        """Test verify_tools_installed when black is missing."""
        # First call succeeds, second fails
        mock_run.side_effect = [
            MagicMock(returncode=0),  # ruff
            subprocess.CalledProcessError(1, "black"),
        ]
        
        with pytest.raises(RuntimeError) as exc_info:
            verify_tools_installed()
        
        assert "black is not installed" in str(exc_info.value)

    @patch("code.linting_config.subprocess.run")
    def test_run_ruff_check(self, mock_run):
        """Test ruff check command construction."""
        mock_result = MagicMock(returncode=0)
        mock_run.return_value = mock_result
        
        result = run_ruff_check()
        
        # Verify subprocess was called
        mock_run.assert_called_once()
        assert result == mock_result

    @patch("code.linting_config.subprocess.run")
    def test_run_black_check(self, mock_run):
        """Test black check command construction."""
        mock_result = MagicMock(returncode=0)
        mock_run.return_value = mock_result
        
        result = run_black_check()
        
        # Verify subprocess was called
        mock_run.assert_called_once()
        assert result == mock_result

class TestConfigFiles:
    """Tests for configuration file generation."""

    def test_ruff_toml_exists(self):
        """Verify .ruff.toml exists in project root."""
        ruff_path = Path.cwd() / ".ruff.toml"
        assert ruff_path.exists(), ".ruff.toml should exist"

    def test_pyproject_toml_black_section(self):
        """Verify pyproject.toml contains black configuration."""
        pyproject_path = Path.cwd() / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml should exist"
        
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        assert "[tool.black]" in content, "pyproject.toml should contain [tool.black]"
        assert "line-length = 88" in content, "Black line-length should be 88"

    def test_ruff_toml_content(self):
        """Verify .ruff.toml contains expected configuration."""
        ruff_path = Path.cwd() / ".ruff.toml"
        
        with open(ruff_path, "r") as f:
            content = f.read()
        
        assert "target-version" in content
        assert "line-length = 88" in content
        assert "select" in content
        assert "ignore" in content
