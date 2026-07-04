"""
Unit tests for linting and formatting configuration.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from code.config_linting import (
    run_command,
    check_flake8,
    check_black,
    fix_black,
    setup_config_files,
    PROJECT_ROOT,
)


class TestRunCommand:
    def test_run_command_success(self):
        """Test running a successful command."""
        exit_code, stdout, stderr = run_command(["echo", "hello"])
        assert exit_code == 0
        assert "hello" in stdout
        assert stderr == ""

    def test_run_command_not_found(self):
        """Test running a command that doesn't exist."""
        exit_code, stdout, stderr = run_command(["nonexistent_command_12345"])
        assert exit_code == -1
        assert stdout == ""
        assert "not found" in stderr.lower()

    def test_run_command_with_cwd(self):
        """Test running a command with a specific working directory."""
        exit_code, stdout, stderr = run_command(
            ["pwd"], cwd=Path("/tmp")
        )
        assert exit_code == 0
        assert "/tmp" in stdout


class TestCheckFlake8:
    @patch("code.config_linting.run_command")
    def test_flake8_passes(self, mock_run_command):
        """Test when flake8 passes."""
        mock_run_command.return_value = (0, "", "")
        result = check_flake8()
        assert result is True

    @patch("code.config_linting.run_command")
    def test_flake8_fails(self, mock_run_command):
        """Test when flake8 fails."""
        mock_run_command.return_value = (1, "E501 line too long", "")
        result = check_flake8()
        assert result is False


class TestCheckBlack:
    @patch("code.config_linting.run_command")
    def test_black_passes(self, mock_run_command):
        """Test when black formatting is correct."""
        mock_run_command.return_value = (0, "", "")
        result = check_black()
        assert result is True

    @patch("code.config_linting.run_command")
    def test_black_fails(self, mock_run_command):
        """Test when black formatting is incorrect."""
        mock_run_command.return_value = (1, "would reformat", "")
        result = check_black()
        assert result is False


class TestFixBlack:
    @patch("code.config_linting.run_command")
    def test_fix_black_success(self, mock_run_command):
        """Test successful black fix."""
        mock_run_command.return_value = (0, "All done! ✨", "")
        result = fix_black()
        assert result is True

    @patch("code.config_linting.run_command")
    def test_fix_black_failure(self, mock_run_command):
        """Test failed black fix."""
        mock_run_command.return_value = (1, "", "Error occurred")
        result = fix_black()
        assert result is False


class TestSetupConfigFiles:
    def test_setup_config_files_creates_files(self, tmp_path):
        """Test that setup_config_files creates configuration files."""
        # Create a temporary directory structure
        temp_root = tmp_path / "test_project"
        temp_root.mkdir()
        code_dir = temp_root / "code"
        code_dir.mkdir()

        # Temporarily override PROJECT_ROOT
        import code.config_linting as config_module

        original_root = config_module.PROJECT_ROOT
        config_module.PROJECT_ROOT = temp_root

        try:
            # Run setup
            setup_config_files()

            # Check that .flake8 was created
            flake8_path = temp_root / ".flake8"
            assert flake8_path.exists()

            # Check that pyproject.toml was created with black config
            pyproject_path = temp_root / "pyproject.toml"
            assert pyproject_path.exists()
            with open(pyproject_path) as f:
                content = f.read()
                assert "[tool.black]" in content
        finally:
            # Restore original PROJECT_ROOT
            config_module.PROJECT_ROOT = original_root


class TestIntegration:
    def test_linting_tools_installed(self):
        """Test that flake8 and black are installed."""
        try:
            import flake8  # noqa: F401
            import black  # noqa: F401
        except ImportError:
            pytest.skip("Linting tools not installed")

    def test_config_files_exist(self):
        """Test that configuration files exist in the project root."""
        flake8_path = PROJECT_ROOT / ".flake8"
        pyproject_path = PROJECT_ROOT / "pyproject.toml"

        assert flake8_path.exists(), ".flake8 configuration file should exist"
        assert pyproject_path.exists(), "pyproject.toml should exist"

        # Check content
        with open(flake8_path) as f:
            content = f.read()
            assert "max-line-length" in content
            assert "100" in content

        with open(pyproject_path) as f:
            content = f.read()
            assert "[tool.black]" in content
            assert "line-length" in content