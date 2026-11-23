"""
Unit tests for the linting and formatting tool runner.
"""
import subprocess
from unittest.mock import patch, MagicMock
import pytest

import sys
import os

# Add parent directory to path to import code.tools
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from tools.lint_format import run_command, check_dependencies, run_lint, run_format


class TestRunCommand:
    def test_run_command_success(self):
        """Test that run_command returns True on success."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = run_command(["echo", "hello"], "Test Command")
            assert result is True
            mock_run.assert_called_once()

    def test_run_command_failure(self):
        """Test that run_command returns False on failure."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
            result = run_command(["bad_cmd"], "Test Command")
            assert result is False

    def test_run_command_not_found(self):
        """Test that run_command returns False if command not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("cmd not found")
            result = run_command(["nonexistent_cmd"], "Test Command")
            assert result is False


class TestCheckDependencies:
    def test_check_dependencies_success(self):
        """Test check_dependencies when tools are installed."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = check_dependencies()
            assert result is True
            assert mock_run.call_count == 2  # ruff and black

    def test_check_dependencies_missing(self):
        """Test check_dependencies when a tool is missing."""
        with patch('subprocess.run') as mock_run:
            # First call succeeds (ruff), second fails (black)
            mock_run.side_effect = [
                MagicMock(returncode=0),
                FileNotFoundError("black not found")
            ]
            result = check_dependencies()
            assert result is False


class TestRunLint:
    def test_run_lint(self):
        """Test that run_lint calls ruff correctly."""
        with patch('tools.lint_format.run_command') as mock_run:
            mock_run.return_value = True
            result = run_lint()
            assert result is True
            mock_run.assert_called_once()
            # Verify the command contains 'ruff'
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "ruff"
            assert "check" in call_args


class TestRunFormat:
    def test_run_format(self):
        """Test that run_format calls black correctly."""
        with patch('tools.lint_format.run_command') as mock_run:
            mock_run.return_value = True
            result = run_format()
            assert result is True
            mock_run.assert_called_once()
            # Verify the command contains 'black'
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "black"