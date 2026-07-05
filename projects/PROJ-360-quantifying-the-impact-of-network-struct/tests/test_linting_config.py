"""
Tests for the linting and formatting configuration module.
"""
import subprocess
import sys
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from linting_config import run_command, setup_tools

class TestRunCommand:
    def test_successful_command(self):
        """Test run_command with a successful command."""
        code, out, err = run_command(["echo", "hello"])
        assert code == 0
        assert "hello" in out
        assert err == ""

    def test_failed_command(self):
        """Test run_command with a failing command."""
        code, out, err = run_command(["false"])
        assert code != 0

    def test_timeout_handling(self):
        """Test run_command with a timeout."""
        # Use a very short timeout to force timeout
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd=["sleep", "10"], timeout=1)
            code, out, err = run_command(["sleep", "10"])
            assert code == -1
            assert "timed out" in err.lower()

class TestSetupTools:
    @patch('linting_config.run_command')
    def test_all_tools_installed(self, mock_run):
        """Test setup_tools when all tools are already installed."""
        mock_run.return_value = (0, "black, 23.1.0", "")
        
        # Mock multiple calls for different tools
        side_effects = [
            (0, "black, 23.1.0", ""),
            (0, "isort, 5.12.0", ""),
            (0, "flake8, 6.0.0", ""),
            (0, "pylint, 2.17.0", ""),
        ]
        mock_run.side_effect = side_effects + [(0, "pip install output", "")]
        
        result = setup_tools()
        assert result is True

    @patch('linting_config.run_command')
    def test_missing_tools_installation(self, mock_run):
        """Test setup_tools when tools need to be installed."""
        # Simulate missing tools
        side_effects = [
            (1, "", "not found"),  # black
            (1, "", "not found"),  # isort
            (1, "", "not found"),  # flake8
            (1, "", "not found"),  # pylint
            (0, "Installed successfully", ""),  # pip install
        ]
        mock_run.side_effect = side_effects
        
        result = setup_tools()
        assert result is True

    @patch('linting_config.run_command')
    def test_installation_failure(self, mock_run):
        """Test setup_tools when installation fails."""
        side_effects = [
            (1, "", "not found"),  # black
            (1, "", "not found"),  # isort
            (1, "", "not found"),  # flake8
            (1, "", "not found"),  # pylint
            (1, "", "Installation failed"),  # pip install
        ]
        mock_run.side_effect = side_effects
        
        result = setup_tools()
        assert result is False