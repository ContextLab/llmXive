"""
Unit tests for the setup_tooling utility module.
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest

from code.utils.setup_tooling import run_command, main


class TestRunCommand:
    def test_run_command_success(self):
        """Test that run_command returns True on successful execution."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="ok", stderr="", returncode=0)
            result = run_command(["echo", "hello"], "Test command")
            assert result is True
            mock_run.assert_called_once()

    def test_run_command_failure(self):
        """Test that run_command returns False on CalledProcessError."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
            result = run_command(["bad_cmd"], "Failing command")
            assert result is False

    def test_run_command_not_found(self):
        """Test that run_command returns False on FileNotFoundError."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("cmd not found")
            result = run_command(["nonexistent"], "Missing command")
            assert result is False


class TestMain:
    def test_main_all_pass(self, capsys):
        """Test main() returns 0 when all tools pass."""
        # Mock all three tool checks to succeed
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
            with patch("sys.exit") as mock_exit:
                result = main()
                # Should call black, flake8, mypy
                assert mock_run.call_count >= 3
                assert result == 0

    def test_main_black_fails(self):
        """Test main() returns 1 when Black fails."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # First call is black
                raise subprocess.CalledProcessError(1, "black")
            return MagicMock(stdout="", stderr="", returncode=0)

        with patch("subprocess.run", side_effect=side_effect):
            result = main()
            assert result == 1