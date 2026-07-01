"""
Tests for the setup_hooks module.
Verifies that the hook installation logic works correctly.
"""
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.setup_hooks import main


class TestSetupHooks:
    """Tests for the pre-commit hook installation script."""

    @patch("code.setup_hooks.subprocess.run")
    @patch("code.setup_hooks.os.chdir")
    @patch("code.setup_hooks.Path")
    def test_pre_commit_installed_successfully(
        self, mock_path, mock_chdir, mock_run
    ):
        """Test that hooks are installed when pre-commit is available."""
        # Mock the pre-commit version check
        mock_run.side_effect = [
            MagicMock(returncode=0),  # pre-commit --version
            MagicMock(returncode=0),  # pre-commit install
        ]

        # Mock Path to return a valid project root
        mock_project_root = MagicMock()
        mock_project_root.parent = Path("/fake/project")
        mock_path.return_value = mock_project_root

        result = main()

        # Verify pre-commit install was called
        install_call = mock_run.call_args_list[1]
        assert install_call[0][0] == ["pre-commit", "install"]
        assert result == 0

    @patch("code.setup_hooks.subprocess.run")
    @patch("code.setup_hooks.os.chdir")
    @patch("code.setup_hooks.Path")
    def test_pre_commit_not_installed(self, mock_path, mock_chdir, mock_run):
        """Test behavior when pre-commit is not installed."""
        # Mock pre-commit --version to fail
        mock_run.side_effect = FileNotFoundError("pre-commit not found")

        # Mock Path to return a valid project root
        mock_project_root = MagicMock()
        mock_project_root.parent = Path("/fake/project")
        mock_path.return_value = mock_project_root

        result = main()

        # Should return 0 (no error) but skip installation
        assert result == 0

    @patch("code.setup_hooks.subprocess.run")
    @patch("code.setup_hooks.os.chdir")
    @patch("code.setup_hooks.Path")
    def test_pre_commit_install_fails(self, mock_path, mock_chdir, mock_run):
        """Test behavior when pre-commit install command fails."""
        # Mock pre-commit version check to succeed
        # Mock pre-commit install to fail
        mock_run.side_effect = [
            MagicMock(returncode=0),  # pre-commit --version
            subprocess.CalledProcessError(1, "pre-commit install"),
        ]

        # Mock Path to return a valid project root
        mock_project_root = MagicMock()
        mock_project_root.parent = Path("/fake/project")
        mock_path.return_value = mock_project_root

        with pytest.raises(subprocess.CalledProcessError):
            main()
