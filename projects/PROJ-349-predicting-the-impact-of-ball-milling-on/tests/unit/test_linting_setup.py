"""
Unit tests for linting setup functionality.
"""
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from code.setup_linting import check_tool, install_dev_dependencies, init_pre_commit


class TestCheckTool:
    def test_check_tool_installed(self):
        """Test that check_tool returns True for an installed tool."""
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = check_tool("flake8")
            assert result is True
            mock_run.assert_called_once()

    def test_check_tool_not_installed(self):
        """Test that check_tool returns False for a missing tool."""
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
            result = check_tool("nonexistent_tool")
            assert result is False

    def test_check_tool_file_not_found(self):
        """Test that check_tool returns False when command is not found."""
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = check_tool("missing_cmd")
            assert result is False


class TestInstallDevDependencies:
    def test_install_dev_dependencies_success(self):
        """Test successful installation of dev dependencies."""
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            install_dev_dependencies()
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "pip" in call_args
            assert "install" in call_args
            assert ".[dev]" in call_args

    def test_install_dev_dependencies_failure(self):
        """Test that RuntimeError is raised when installation fails."""
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            with pytest.raises(RuntimeError, match="Failed to install"):
                install_dev_dependencies()


class TestInitPreCommit:
    def test_init_pre_commit_success(self):
        """Test successful initialization of pre-commit hooks."""
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            init_pre_commit()
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "pre_commit" in call_args
            assert "install" in call_args

    def test_init_pre_commit_failure(self):
        """Test that RuntimeError is raised when initialization fails."""
        with patch("code.setup_linting.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            with pytest.raises(RuntimeError, match="Failed to initialize"):
                init_pre_commit()