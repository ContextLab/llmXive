"""
Unit tests for linting_setup.py
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from linting_setup import (
    ensure_ruff_black_installed,
    create_pyproject_config,
    check_config_files,
    run_lint_check,
    run_format_check,
    PROJECT_ROOT
)

class TestLintingSetup(unittest.TestCase):

    @patch('linting_setup.subprocess.run')
    def test_ensure_ruff_black_installed_success(self, mock_run):
        """Test that the function returns True when tools are already installed."""
        mock_run.side_effect = [
            MagicMock(returncode=0), # ruff check
            MagicMock(returncode=0)  # black check
        ]
        # Should not raise
        ensure_ruff_black_installed()
        self.assertEqual(mock_run.call_count, 2)

    @patch('linting_setup.subprocess.run')
    def test_ensure_ruff_black_installed_install(self, mock_run):
        """Test that the function installs tools if missing."""
        # First two calls fail (tools missing)
        mock_run.side_effect = [
            FileNotFoundError(), # ruff
            FileNotFoundError(), # black
            MagicMock(returncode=0) # pip install
        ]
        ensure_ruff_black_installed()
        # Should have called pip install
        self.assertTrue(any("pip" in str(call) for call in mock_run.call_args_list))

    @patch('linting_setup.Path.exists')
    @patch('linting_setup.Path.open')
    def test_create_pyproject_config_creates_file(self, mock_open, mock_exists):
        """Test that config file is created if it doesn't exist."""
        mock_exists.return_value = False
        create_pyproject_config()
        mock_open.assert_called_once_with("w")
        
    @patch('linting_setup.Path.exists')
    def test_create_pyproject_config_skips_existing(self, mock_exists):
        """Test that config file is not overwritten if it exists."""
        mock_exists.return_value = True
        # Should not raise and should not create new file
        create_pyproject_config()

    @patch('linting_setup.create_pyproject_config')
    @patch('linting_setup.ensure_ruff_black_installed')
    def test_check_config_files(self, mock_ensure, mock_create):
        """Test the main check configuration function."""
        result = check_config_files()
        self.assertTrue(result)
        mock_ensure.assert_called_once()
        mock_create.assert_called_once()

    @patch('linting_setup.subprocess.run')
    def test_run_lint_check_success(self, mock_run):
        """Test lint check returns True when no issues found."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = run_lint_check()
        self.assertTrue(result)

    @patch('linting_setup.subprocess.run')
    def test_run_lint_check_failure(self, mock_run):
        """Test lint check returns False when issues found."""
        mock_run.return_value = MagicMock(
            returncode=1, 
            stdout="E501 line too long", 
            stderr=""
        )
        result = run_lint_check()
        self.assertFalse(result)

    @patch('linting_setup.subprocess.run')
    def test_run_format_check_success(self, mock_run):
        """Test format check returns True when no issues found."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        result = run_format_check()
        self.assertTrue(result)

    @patch('linting_setup.subprocess.run')
    def test_run_format_check_failure(self, mock_run):
        """Test format check returns False when issues found."""
        mock_run.return_value = MagicMock(
            returncode=1, 
            stdout="Would reformat: file.py", 
            stderr=""
        )
        result = run_format_check()
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()