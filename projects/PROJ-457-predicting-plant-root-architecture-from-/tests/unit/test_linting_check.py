"""
Unit tests for the linting_check module.
"""
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from code.linting_check import run_command

def test_run_command_success():
    """Test that run_command returns True for a successful command."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = run_command(["echo", "hello"])
        assert result is True
        mock_run.assert_called_once()

def test_run_command_failure():
    """Test that run_command returns False for a failed command."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=1)
        result = run_command(["false"])
        assert result is False

def test_run_command_file_not_found():
    """Test that run_command returns False when command is not found."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("Command not found")
        result = run_command(["nonexistent_command"])
        assert result is False