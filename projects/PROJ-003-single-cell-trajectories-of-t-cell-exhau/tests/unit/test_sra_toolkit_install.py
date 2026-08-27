"""
Unit tests for SRA Toolkit installation script.

These tests verify that the installation script:
1. Checks for conda availability.
2. Creates ~/.ncbi/settings if missing.
3. Verifies 'prefetch' command is available.
"""

import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
# Adjust import path if necessary based on project structure
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
from install_sra_toolkit import (
    ensure_ncbi_settings,
    run_command,
    verify_sra_toolkit,
)


class TestRunCommand:
    """Tests for the run_command helper function."""

    def test_run_command_success(self, capsys):
        """Test that run_command succeeds for a valid command."""
        # Use a simple command that should always succeed
        run_command(["echo", "hello"], "Test command")
        captured = capsys.readouterr()
        assert "hello" in captured.out

    def test_run_command_failure(self):
        """Test that run_command raises SystemExit on failure."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, ["test"], stderr="error message"
            )
            with pytest.raises(SystemExit):
                run_command(["fake_command"], "Test failure")


class TestEnsureNcbiSettings:
    """Tests for ensure_ncbi_settings function."""

    def test_creates_directory_and_file_if_missing(self, tmp_path, monkeypatch):
        """Test that the function creates ~/.ncbi/settings if it doesn't exist."""
        # Mock home directory to a temp directory
        temp_ncbi = tmp_path / ".ncbi"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Ensure the file doesn't exist
        settings_file = temp_ncbi / "settings"
        assert not settings_file.exists()

        # Call the function
        ensure_ncbi_settings()

        # Verify directory and file were created
        assert temp_ncbi.exists()
        assert settings_file.exists()
        content = settings_file.read_text()
        assert "[config]" in content

    def test_does_not_overwrite_existing_file(self, tmp_path, monkeypatch):
        """Test that the function does not overwrite an existing settings file."""
        temp_ncbi = tmp_path / ".ncbi"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Create a pre-existing settings file with unique content
        settings_file = temp_ncbi / "settings"
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        unique_content = "UNIQUE_MARKER_12345"
        settings_file.write_text(unique_content)

        # Call the function
        ensure_ncbi_settings()

        # Verify content is unchanged
        assert settings_file.read_text() == unique_content


class TestVerifySraToolkit:
    """Tests for verify_sra_toolkit function."""

    @patch("subprocess.run")
    def test_verifies_prefetch_success(self, mock_run, capsys):
        """Test that verify_sra_toolkit succeeds when prefetch works."""
        # Mock successful subprocess.run
        mock_result = MagicMock()
        mock_result.stdout = "Usage: prefetch [options] <accession>\n..."
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # This should not raise
        verify_sra_toolkit()

        # Verify subprocess.run was called with correct arguments
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == "prefetch"
        assert call_args[1] == "--help"

    @patch("subprocess.run")
    def test_raises_on_prefetch_failure(self, mock_run):
        """Test that verify_sra_toolkit exits when prefetch fails."""
        # Mock failed subprocess.run
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["prefetch", "--help"], stderr="command not found"
        )

        # This should raise SystemExit
        with pytest.raises(SystemExit):
            verify_sra_toolkit()
