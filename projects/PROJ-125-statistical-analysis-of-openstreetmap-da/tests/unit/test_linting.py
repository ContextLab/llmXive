"""
Unit tests for the linting script functionality.
"""
import subprocess
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.run_linting import run_command, main


class TestRunCommand:
    """Tests for the run_command function."""

    def test_run_command_success(self, caplog):
        """Test that run_command returns True on success."""
        with patch("scripts.run_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr=""
            )

            result = run_command(["echo", "test"], "Test command")

            assert result is True
            mock_run.assert_called_once()

    def test_run_command_failure(self, caplog):
        """Test that run_command returns False on failure."""
        with patch("scripts.run_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="Error output",
                stderr="Error details"
            )

            result = run_command(["bad_command"], "Test command")

            assert result is False
            mock_run.assert_called_once()

    def test_run_command_exception(self, caplog):
        """Test that run_command returns False on exception."""
        with patch("scripts.run_linting.subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Network error")

            result = run_command(["curl", "http://example.com"], "Test command")

            assert result is False


class TestMain:
    """Tests for the main function."""

    @patch("scripts.run_linting.run_command")
    def test_main_all_success(self, mock_run_command, caplog):
        """Test main returns 0 when all commands succeed."""
        mock_run_command.return_value = True

        result = main()

        assert result == 0
        assert mock_run_command.call_count == 3

    @patch("scripts.run_linting.run_command")
    def test_main_partial_failure(self, mock_run_command, caplog):
        """Test main returns 1 when some commands fail."""
        # Simulate first two succeed, last fails
        mock_run_command.side_effect = [True, True, False]

        result = main()

        assert result == 1

    @patch("scripts.run_linting.run_command")
    def test_main_all_failure(self, mock_run_command, caplog):
        """Test main returns 1 when all commands fail."""
        mock_run_command.return_value = False

        result = main()

        assert result == 1

    def test_main_missing_code_dir(self, caplog, tmp_path):
        """Test main returns 1 when code directory is missing."""
        with patch("scripts.run_linting.Path") as mock_path:
            mock_path.return_value.parent.parent.parent = tmp_path
            # Ensure code_dir doesn't exist
            mock_code_dir = tmp_path / "nonexistent_code"
            mock_code_dir.exists.return_value = False

            with patch("scripts.run_linting.Path.__truediv__", return_value=mock_code_dir):
                result = main()

                assert result == 1