import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Import the module under test
from install_sra_toolkit import (
    run_command,
    ensure_ncbi_settings,
    verify_sra_toolkit,
    install_sra_toolkit,
    main
)


class TestRunCommand:
    """Tests for the run_command helper function."""

    def test_run_command_success(self):
        """Test that run_command returns CompletedProcess on success."""
        result = run_command(["echo", "hello"], check=True)
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_run_command_failure_with_check(self):
        """Test that run_command raises on failure when check=True."""
        with pytest.raises(subprocess.CalledProcessError):
            run_command(["sh", "-c", "exit 1"], check=True)

    def test_run_command_failure_without_check(self):
        """Test that run_command returns error on failure when check=False."""
        result = run_command(["sh", "-c", "exit 1"], check=False)
        assert result.returncode == 1


class TestEnsureNcbiSettings:
    """Tests for the ensure_ncbi_settings function."""

    def test_creates_directory_if_missing(self, tmp_path, monkeypatch):
        """Test that the function creates ~/.ncbi directory if it doesn't exist."""
        # Mock Path.home() to return tmp_path
        mock_ncbi_dir = tmp_path / ".ncbi"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = ensure_ncbi_settings()
        
        assert result is True
        assert mock_ncbi_dir.exists()
        assert (mock_ncbi_dir / "settings").exists()

    def test_creates_settings_file_if_missing(self, tmp_path, monkeypatch):
        """Test that the function creates settings file if it doesn't exist."""
        mock_ncbi_dir = tmp_path / ".ncbi"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        result = ensure_ncbi_settings()
        
        assert result is True
        settings_file = mock_ncbi_dir / "settings"
        assert settings_file.exists()
        content = settings_file.read_text()
        assert "[DEFAULT]" in content
        assert "[repository]" in content

    def test_does_not_overwrite_existing_settings(self, tmp_path, monkeypatch):
        """Test that the function doesn't overwrite existing settings."""
        mock_ncbi_dir = tmp_path / ".ncbi"
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        
        # Create existing settings
        mock_ncbi_dir.mkdir(parents=True, exist_ok=True)
        settings_file = mock_ncbi_dir / "settings"
        original_content = "CUSTOM_SETTING=value\n"
        settings_file.write_text(original_content)
        
        result = ensure_ncbi_settings()
        
        assert result is True
        assert settings_file.read_text() == original_content


class TestVerifySraToolkit:
    """Tests for the verify_sra_toolkit function."""

    @patch("install_sra_toolkit.run_command")
    def test_verification_success(self, mock_run_command):
        """Test successful verification when prefetch --help succeeds."""
        mock_run_command.return_value = MagicMock(
            returncode=0,
            stdout="prefetch help output",
            stderr=""
        )
        
        result = verify_sra_toolkit()
        
        assert result is True
        mock_run_command.assert_called_once_with(["prefetch", "--help"], check=False)

    @patch("install_sra_toolkit.run_command")
    def test_verification_failure_nonzero(self, mock_run_command):
        """Test verification fails when prefetch --help returns non-zero."""
        mock_run_command.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error message"
        )
        
        result = verify_sra_toolkit()
        
        assert result is False

    @patch("install_sra_toolkit.run_command")
    def test_verification_file_not_found(self, mock_run_command):
        """Test verification fails when prefetch is not found."""
        mock_run_command.side_effect = FileNotFoundError("prefetch not found")
        
        result = verify_sra_toolkit()
        
        assert result is False


class TestInstallSraToolkit:
    """Tests for the install_sra_toolkit function."""

    @patch("install_sra_toolkit.run_command")
    def test_install_success_with_conda(self, mock_run_command):
        """Test successful installation via conda."""
        # First call: check conda version (success)
        mock_run_command.side_effect = [
            MagicMock(returncode=0, stdout="conda 23.0"),  # conda --version
            MagicMock(returncode=0, stdout="installation complete")  # conda install
        ]
        
        result = install_sra_toolkit()
        
        assert result is True
        # Verify conda install was called with correct arguments
        install_call = mock_run_command.call_args_list[1]
        assert "sratoolkit" in install_call[0][0]
        assert "-c" in install_call[0][0]
        assert "bioconda" in install_call[0][0]

    @patch("install_sra_toolkit.run_command")
    def test_install_success_with_mamba(self, mock_run_command):
        """Test successful installation via mamba when conda is not found."""
        # First call: check conda (fail), second: check mamba (success)
        mock_run_command.side_effect = [
            FileNotFoundError("conda not found"),
            MagicMock(returncode=0, stdout="mamba 1.0"),  # mamba --version
            MagicMock(returncode=0, stdout="installation complete")  # mamba install
        ]
        
        result = install_sra_toolkit()
        
        assert result is True

    @patch("install_sra_toolkit.run_command")
    def test_install_failure_no_conda(self, mock_run_command):
        """Test installation fails when neither conda nor mamba is found."""
        mock_run_command.side_effect = [
            FileNotFoundError("conda not found"),
            FileNotFoundError("mamba not found")
        ]
        
        result = install_sra_toolkit()
        
        assert result is False

    @patch("install_sra_toolkit.run_command")
    def test_install_failure_conda_error(self, mock_run_command):
        """Test installation fails when conda install returns error."""
        mock_run_command.side_effect = [
            MagicMock(returncode=0, stdout="conda 23.0"),
            MagicMock(returncode=1, stdout="", stderr="install failed")
        ]
        
        result = install_sra_toolkit()
        
        assert result is False


class TestMain:
    """Tests for the main entry point."""

    @patch("install_sra_toolkit.verify_sra_toolkit")
    @patch("install_sra_toolkit.ensure_ncbi_settings")
    def test_main_already_installed(self, mock_ensure, mock_verify):
        """Test main returns 0 when SRA Toolkit is already installed."""
        mock_verify.return_value = True
        mock_ensure.return_value = True
        
        result = main()
        
        assert result == 0
        mock_ensure.assert_called_once()

    @patch("install_sra_toolkit.verify_sra_toolkit")
    @patch("install_sra_toolkit.install_sra_toolkit")
    @patch("install_sra_toolkit.ensure_ncbi_settings")
    def test_main_install_success(self, mock_ensure, mock_install, mock_verify):
        """Test main returns 0 after successful installation."""
        # First verify fails, then install succeeds
        mock_verify.side_effect = [False, True]
        mock_install.return_value = True
        mock_ensure.return_value = True
        
        result = main()
        
        assert result == 0
        mock_install.assert_called_once()

    @patch("install_sra_toolkit.verify_sra_toolkit")
    @patch("install_sra_toolkit.install_sra_toolkit")
    def test_main_install_failure(self, mock_install, mock_verify):
        """Test main returns 1 when installation fails."""
        mock_verify.side_effect = [False, False]
        mock_install.return_value = False
        
        result = main()
        
        assert result == 1
        mock_install.assert_called_once()