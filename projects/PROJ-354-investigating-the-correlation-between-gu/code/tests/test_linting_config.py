"""
Tests for the linting configuration and utility functions.
These tests verify that the configuration dictionaries are valid
and that the environment validation logic works.
"""
import pytest
import sys
import subprocess
from unittest.mock import patch, MagicMock

# Import the module under test
# Assuming the test file is in code/tests/, we need to adjust path if necessary
# But typically tests are run with pytest from root, adding src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.linting_config import (
    get_black_config,
    get_ruff_config,
    validate_environment,
    run_formatter,
    run_linter
)
from pathlib import Path

class TestConfigGeneration:
    def test_get_black_config_structure(self):
        config = get_black_config()
        assert isinstance(config, dict)
        assert "line_length" in config
        assert config["line_length"] == 88
        assert "target_version" in config
        assert config["target_version"] == "py310"

    def test_get_ruff_config_structure(self):
        config = get_ruff_config()
        assert isinstance(config, dict)
        assert "line-length" in config
        assert config["line-length"] == 88
        assert "select" in config
        assert isinstance(config["select"], list)
        assert "E" in config["select"]
        assert "F" in config["select"]

class TestEnvironmentValidation:
    @patch('code.linting_config.subprocess.run')
    def test_validate_environment_success(self, mock_run):
        # Mock successful execution for both tools
        mock_run.return_value = MagicMock(returncode=0)
        
        result = validate_environment()
        
        assert result is True
        assert mock_run.call_count == 2

    @patch('code.linting_config.subprocess.run')
    def test_validate_environment_failure(self, mock_run):
        # Mock failure for ruff
        mock_run.side_effect = [MagicMock(returncode=0), FileNotFoundError()]
        
        result = validate_environment()
        
        assert result is False

class TestRunners:
    @patch('code.linting_config.subprocess.run')
    def test_run_formatter_success(self, mock_run):
        # Mock Black returning 0 (already formatted) or 1 (changed)
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        result = run_formatter("code/config.py")
        
        assert result is True
        mock_run.assert_called_once()

    @patch('code.linting_config.subprocess.run')
    def test_run_linter_clean(self, mock_run):
        # Mock Ruff returning 0 (no issues)
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        
        result = run_linter("code/config.py")
        
        assert result is True

    @patch('code.linting_config.subprocess.run')
    def test_run_linter_issues(self, mock_run):
        # Mock Ruff returning 1 (issues found)
        mock_run.return_value = MagicMock(returncode=1, stdout="E501 Line too long", stderr="")
        
        result = run_linter("code/config.py")
        
        assert result is False
