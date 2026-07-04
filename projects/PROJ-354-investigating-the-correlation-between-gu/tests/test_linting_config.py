"""
Tests for the linting configuration and helper functions.
"""

import subprocess
import sys
from unittest.mock import patch, MagicMock

import pytest

# Import the module to test
import code.linting_config as linting_config


class TestLintingConfigConstants:
    """Test that configuration constants are correctly defined."""

    def test_black_line_length(self):
        assert linting_config.BLACK_LINE_LENGTH == 88

    def test_black_target_version(self):
        assert linting_config.BLACK_TARGET_VERSION == "py310"

    def test_ruff_target_version(self):
        assert linting_config.RUFF_TARGET_VERSION == "3.10"

    def test_exclude_patterns(self):
        assert isinstance(linting_config.EXCLUDE_PATTERNS, list)
        assert ".git" in linting_config.EXCLUDE_PATTERNS
        assert "data" in linting_config.EXCLUDE_PATTERNS
        assert "results" in linting_config.EXCLUDE_PATTERNS


class TestGetConfigFunctions:
    """Test the configuration dictionary generators."""

    def test_get_black_config(self):
        config = linting_config.get_black_config()
        assert config["line-length"] == 88
        assert "py310" in config["target-version"]
        assert "data" in config["exclude"]

    def test_get_ruff_config(self):
        config = linting_config.get_ruff_config()
        assert config["target-version"] == "py310"
        assert "E" in config["lint"]["select"]
        assert "F" in config["lint"]["select"]
        assert "E501" in config["lint"]["ignore"]


class TestValidateEnvironment:
    """Test the environment validation function."""

    @patch("code.linting_config.subprocess.run")
    def test_validate_environment_success(self, mock_run):
        # Mock successful execution for both tools
        mock_run.return_value = MagicMock(returncode=0)

        with patch("code.linting_config.print") as mock_print:
            result = linting_config.validate_environment()
            assert result is True
            mock_print.assert_not_called()  # No error messages expected

    @patch("code.linting_config.subprocess.run")
    def test_validate_environment_failure(self, mock_run):
        # Mock failure for one tool
        def side_effect(*args, **kwargs):
            if "ruff" in str(args):
                raise subprocess.CalledProcessError(1, "ruff")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        with patch("code.linting_config.print") as mock_print:
            result = linting_config.validate_environment()
            assert result is False
            mock_print.assert_called()  # Should print missing tools message


class TestRunFormatter:
    """Test the Black formatter runner."""

    @patch("code.linting_config.subprocess.run")
    def test_run_formatter_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="All done!", stderr=""
        )

        with patch("code.linting_config.print") as mock_print:
            result = linting_config.run_formatter("code")
            assert result is True
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "black" in args

    @patch("code.linting_config.subprocess.run")
    def test_run_formatter_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "black")

        result = linting_config.run_formatter("code")
        assert result is False


class TestRunLinter:
    """Test the Ruff linter runner."""

    @patch("code.linting_config.subprocess.run")
    def test_run_linter_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="All checks passed!", stderr=""
        )

        with patch("code.linting_config.print") as mock_print:
            result = linting_config.run_linter("code")
            assert result is True
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "ruff" in args

    @patch("code.linting_config.subprocess.run")
    def test_run_linter_failure(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(1, "ruff")

        result = linting_config.run_linter("code")
        assert result is False
