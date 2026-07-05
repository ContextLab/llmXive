"""
Unit tests for lint configuration and helper functions.
"""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
import subprocess
import sys

# Import the module to test
from code.lint_config import (
    RUFF_CONFIG,
    BLACK_CONFIG,
    write_ruff_toml,
    write_black_toml,
    install_tools,
    run_lint_check,
    run_format_check,
)


class TestRuffConfig:
    """Tests for ruff configuration constants."""

    def test_ruff_config_has_required_keys(self):
        """Test that RUFF_CONFIG has all required keys."""
        required_keys = ["target-version", "line-length", "select", "ignore", "exclude"]
        for key in required_keys:
            assert key in RUFF_CONFIG, f"Missing required key: {key}"

    def test_ruff_target_version(self):
        """Test that target version is set to py311."""
        assert RUFF_CONFIG["target-version"] == "py311"

    def test_ruff_line_length(self):
        """Test that line length is set to 88."""
        assert RUFF_CONFIG["line-length"] == 88

    def test_ruff_select_rules(self):
        """Test that select includes standard rules."""
        expected_rules = ["E", "W", "F", "I", "B", "C4", "UP"]
        for rule in expected_rules:
            assert rule in RUFF_CONFIG["select"], f"Missing rule: {rule}"


class TestBlackConfig:
    """Tests for black configuration constants."""

    def test_black_config_has_required_keys(self):
        """Test that BLACK_CONFIG has all required keys."""
        required_keys = ["line-length", "target-version", "exclude"]
        for key in required_keys:
            assert key in BLACK_CONFIG, f"Missing required key: {key}"

    def test_black_line_length(self):
        """Test that line length is set to 88."""
        assert BLACK_CONFIG["line-length"] == 88

    def test_black_target_version(self):
        """Test that target version includes py311."""
        assert "py311" in BLACK_CONFIG["target-version"]


class TestWriteRuffToml:
    """Tests for write_ruff_toml function."""

    def test_write_ruff_toml_creates_file(self):
        """Test that write_ruff_toml creates a new file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            temp_path = f.name
        
        try:
            # Remove file to test creation
            os.remove(temp_path)
            
            result = write_ruff_toml(temp_path)
            
            assert result is True
            assert os.path.exists(temp_path)
            
            # Check content
            with open(temp_path, "r") as f:
                content = f.read()
                assert "[tool.ruff]" in content
                assert 'target-version = "py311"' in content
                assert "line-length = 88" in content
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_write_ruff_toml_updates_existing(self):
        """Test that write_ruff_toml updates existing file correctly."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            f.write("[tool.black]\nline-length = 88\n")
            temp_path = f.name
        
        try:
            result = write_ruff_toml(temp_path)
            
            assert result is True
            
            with open(temp_path, "r") as f:
                content = f.read()
                assert "[tool.ruff]" in content
                assert "[tool.black]" in content
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestWriteBlackToml:
    """Tests for write_black_toml function."""

    def test_write_black_toml_creates_file(self):
        """Test that write_black_toml creates a new file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            temp_path = f.name
        
        try:
            # Remove file to test creation
            os.remove(temp_path)
            
            result = write_black_toml(temp_path)
            
            assert result is True
            assert os.path.exists(temp_path)
            
            # Check content
            with open(temp_path, "r") as f:
                content = f.read()
                assert "[tool.black]" in content
                assert "line-length = 88" in content
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_write_black_toml_updates_existing(self):
        """Test that write_black_toml updates existing file correctly."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".toml") as f:
            f.write("[tool.ruff]\ntarget-version = \"py311\"\n")
            temp_path = f.name
        
        try:
            result = write_black_toml(temp_path)
            
            assert result is True
            
            with open(temp_path, "r") as f:
                content = f.read()
                assert "[tool.black]" in content
                assert "[tool.ruff]" in content
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestInstallTools:
    """Tests for install_tools function."""

    @patch("code.lint_config.subprocess.run")
    def test_install_tools_success(self, mock_run):
        """Test successful installation of tools."""
        # Mock successful subprocess calls
        mock_run.return_value = MagicMock(returncode=0)
        
        result = install_tools()
        
        assert result is True

    @patch("code.lint_config.subprocess.run")
    def test_install_tools_failure(self, mock_run):
        """Test failure during tool installation."""
        # Mock failure
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        
        result = install_tools()
        
        assert result is False


class TestRunLintCheck:
    """Tests for run_lint_check function."""

    @patch("code.lint_config.subprocess.run")
    def test_run_lint_check_success(self, mock_run):
        """Test successful lint check with no issues."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_lint_check("code")
        
        assert result is True
        mock_run.assert_called_once()

    @patch("code.lint_config.subprocess.run")
    def test_run_lint_check_issues(self, mock_run):
        """Test lint check with issues found."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "E501 Line too long\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_lint_check("code")
        
        assert result is False


class TestRunFormatCheck:
    """Tests for run_format_check function."""

    @patch("code.lint_config.subprocess.run")
    def test_run_format_check_success(self, mock_run):
        """Test successful format check."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "All done!"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_format_check("code")
        
        assert result is True

    @patch("code.lint_config.subprocess.run")
    def test_run_format_check_issues(self, mock_run):
        """Test format check with issues found."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = "would reformat file.py\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        result = run_format_check("code")
        
        assert result is False