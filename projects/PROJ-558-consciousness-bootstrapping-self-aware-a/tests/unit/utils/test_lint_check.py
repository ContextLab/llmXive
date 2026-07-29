"""
Unit tests for the lint_check module.

These tests verify that the lint and formatting check utilities
function correctly.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

from utils.lint_check import run_command, check_ruff, check_black

class TestRunCommand:
    """Tests for the run_command function."""
    
    def test_successful_command(self):
        """Test that a successful command returns correct values."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="success",
                stderr=""
            )
            
            code, stdout, stderr = run_command(["echo", "hello"], check=True)
            
            assert code == 0
            assert stdout == "success"
            assert stderr == ""
            mock_run.assert_called_once()
    
    def test_failed_command_no_check(self):
        """Test that a failed command with check=False returns error code."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="error output",
                stderr="error message"
            )
            
            code, stdout, stderr = run_command(["fail"], check=False)
            
            assert code == 1
            assert stdout == "error output"
            assert stderr == "error message"

class TestCheckRuff:
    """Tests for the check_ruff function."""
    
    def test_ruff_passed(self):
        """Test that check_ruff returns True when ruff passes."""
        with patch('utils.lint_check.run_command') as mock_run:
            mock_run.return_value = (0, "", "")
            
            result = check_ruff(Path("/fake/path"))
            
            assert result is True
            mock_run.assert_called_once()
    
    def test_ruff_failed(self):
        """Test that check_ruff returns False when ruff fails."""
        with patch('utils.lint_check.run_command') as mock_run:
            mock_run.return_value = (1, "lint error", "")
            
            result = check_ruff(Path("/fake/path"))
            
            assert result is False
            mock_run.assert_called_once()

class TestCheckBlack:
    """Tests for the check_black function."""
    
    def test_black_passed(self):
        """Test that check_black returns True when black passes."""
        with patch('utils.lint_check.run_command') as mock_run:
            mock_run.return_value = (0, "", "")
            
            result = check_black(Path("/fake/path"))
            
            assert result is True
            mock_run.assert_called_once()
    
    def test_black_failed(self):
        """Test that check_black returns False when black fails."""
        with patch('utils.lint_check.run_command') as mock_run:
            mock_run.return_value = (1, "format error", "")
            
            result = check_black(Path("/fake/path"))
            
            assert result is False
            mock_run.assert_called_once()