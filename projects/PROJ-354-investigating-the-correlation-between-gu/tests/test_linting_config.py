"""
Unit tests for the linting configuration module.
"""
import pytest
import sys
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

# Adjust path to import code modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.linting_config import (
    get_black_config,
    get_ruff_config,
    validate_environment,
    run_formatter,
    run_linter,
    main,
)


class TestConfigGeneration:
    """Tests for configuration retrieval functions."""

    def test_get_black_config_returns_valid_dict(self):
        config = get_black_config()
        assert isinstance(config, dict)
        assert "line_length" in config
        assert config["line_length"] == 88
        assert "target_version" in config
        assert config["target_version"] == "py310"

    def test_get_ruff_config_returns_valid_dict(self):
        config = get_ruff_config()
        assert isinstance(config, dict)
        assert "select" in config
        assert isinstance(config["select"], list)
        assert "E" in config["select"]
        assert "ignore" in config
        assert isinstance(config["ignore"], list)


class TestEnvironmentValidation:
    """Tests for environment validation."""

    @patch("code.linting_config.subprocess.run")
    def test_validate_environment_success(self, mock_run):
        # Mock successful subprocess calls for both ruff and black
        mock_run.return_value = MagicMock(
            stdout="ruff 0.1.0", stderr="", returncode=0
        )

        with patch("code.linting_config.subprocess.run", side_effect=[
            MagicMock(stdout="ruff 0.1.0", stderr="", returncode=0),
            MagicMock(stdout="black, 23.1.0", stderr="", returncode=0),
        ]):
            result = validate_environment()
            assert result is True

    @patch("code.linting_config.subprocess.run")
    def test_validate_environment_failure_missing_tool(self, mock_run):
        # Mock failure for ruff
        mock_run.side_effect = FileNotFoundError("ruff not found")

        result = validate_environment()
        assert result is False


class TestRunners:
    """Tests for formatter and linter runners."""

    @patch("code.linting_config.subprocess.run")
    def test_run_formatter_check_only(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        result = run_formatter(check_only=True)
        assert result is True
        # Verify --check flag was passed
        call_args = mock_run.call_args[0][0]
        assert "--check" in call_args

    @patch("code.linting_config.subprocess.run")
    def test_run_linter_fix_mode(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)

        result = run_linter(fix=True)
        assert result is True
        # Verify --fix flag was passed
        call_args = mock_run.call_args[0][0]
        assert "--fix" in call_args

    @patch("code.linting_config.subprocess.run")
    def test_run_linter_issues_found(self, mock_run):
        # Simulate ruff finding issues (non-zero exit code)
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["ruff"], output="E501 line too long"
        )

        result = run_linter()
        assert result is False
