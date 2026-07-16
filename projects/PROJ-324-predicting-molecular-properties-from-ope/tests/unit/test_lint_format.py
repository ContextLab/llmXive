"""
Unit tests for linting and formatting utilities.

These tests verify the core functionality of the lint_format_config module
without requiring actual code to be linted.
"""

import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path

import pytest


class TestRunCommand:
    """Tests for the run_command function."""

    @pytest.fixture
    def mock_subprocess_run(self):
        """Mock subprocess.run to return controlled values."""
        with patch("lint_format_config.subprocess.run") as mock_run:
            yield mock_run

    def test_run_command_success(self, mock_subprocess_run):
        """Test successful command execution."""
        from lint_format_config import run_command

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_subprocess_run.return_value = mock_result

        return_code, stdout, stderr = run_command(["echo", "hello"])

        assert return_code == 0
        assert stdout == "success"
        assert stderr == ""
        mock_subprocess_run.assert_called_once()

    def test_run_command_failure(self, mock_subprocess_run):
        """Test command execution with non-zero exit code."""
        from lint_format_config import run_command

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"
        mock_subprocess_run.return_value = mock_result

        return_code, stdout, stderr = run_command(["false"])

        assert return_code == 1
        assert stdout == ""
        assert stderr == "error"

    def test_run_command_not_found(self, mock_subprocess_run):
        """Test command execution when command is not found."""
        from lint_format_config import run_command

        mock_subprocess_run.side_effect = FileNotFoundError("Command not found")

        return_code, stdout, stderr = run_command(["nonexistent_command"])

        assert return_code == -1
        assert "Command not found" in stderr


class TestCheckCode:
    """Tests for the check_code function."""

    @pytest.fixture
    def mock_run_command(self):
        """Mock run_command to return controlled values."""
        with patch("lint_format_config.run_command") as mock_run:
            yield mock_run

    def test_check_code_all_pass(self, mock_run_command):
        """Test when both ruff and black pass."""
        from lint_format_config import check_code

        mock_run_command.side_effect = [
            (0, "Ruff passed", ""),  # ruff check
            (0, "Black passed", ""),  # black check
        ]

        exit_code, message = check_code()

        assert exit_code == 0
        assert "Ruff check passed" in message
        assert "Black formatting check passed" in message

    def test_check_code_ruff_fails(self, mock_run_command):
        """Test when ruff fails but black passes."""
        from lint_format_config import check_code

        mock_run_command.side_effect = [
            (1, "Ruff errors", "Ruff stderr"),  # ruff check fails
            (0, "Black passed", ""),  # black check passes
        ]

        exit_code, message = check_code()

        assert exit_code == 1
        assert "Ruff check found issues" in message

    def test_check_code_black_fails(self, mock_run_command):
        """Test when black fails but ruff passes."""
        from lint_format_config import check_code

        mock_run_command.side_effect = [
            (0, "Ruff passed", ""),  # ruff check passes
            (1, "Black errors", "Black stderr"),  # black check fails
        ]

        exit_code, message = check_code()

        assert exit_code == 1
        assert "Black formatting check found issues" in message

    def test_check_code_both_fail(self, mock_run_command):
        """Test when both ruff and black fail."""
        from lint_format_config import check_code

        mock_run_command.side_effect = [
            (1, "Ruff errors", "Ruff stderr"),  # ruff check fails
            (1, "Black errors", "Black stderr"),  # black check fails
        ]

        exit_code, message = check_code()

        assert exit_code == 1
        assert "Ruff check found issues" in message
        assert "Black formatting check found issues" in message


class TestFixCode:
    """Tests for the fix_code function."""

    @pytest.fixture
    def mock_run_command(self):
        """Mock run_command to return controlled values."""
        with patch("lint_format_config.run_command") as mock_run:
            yield mock_run

    def test_fix_code_success(self, mock_run_command):
        """Test successful fix execution."""
        from lint_format_config import fix_code

        mock_run_command.side_effect = [
            (0, "Ruff fixed", ""),  # ruff fix
            (0, "Black fixed", ""),  # black fix
        ]

        exit_code, message = fix_code()

        assert exit_code == 0
        assert "Ruff fix completed" in message
        assert "Black formatting completed" in message

    def test_fix_code_ruff_fails(self, mock_run_command):
        """Test when ruff fix fails."""
        from lint_format_config import fix_code

        mock_run_command.side_effect = [
            (2, "", "Ruff error"),  # ruff fix fails
            (0, "Black fixed", ""),  # black fix succeeds
        ]

        exit_code, message = fix_code()

        assert exit_code == 2
        assert "Ruff fix encountered an error" in message