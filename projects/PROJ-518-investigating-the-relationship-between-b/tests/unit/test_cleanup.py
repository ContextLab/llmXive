"""
Unit tests for cleanup_and_format module.

These tests verify that the cleanup and formatting functions
work correctly and handle edge cases properly.
"""
import pytest
import subprocess
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from cleanup_and_format import run_command, format_code_with_black, check_with_flake8


class TestRunCommand:
    """Tests for the run_command function."""
    
    def test_run_command_success(self):
        """Test that run_command returns True for successful commands."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="",
                stderr=""
            )
            
            result = run_command(["echo", "hello"], "Test command")
            
            assert result is True
            mock_run.assert_called_once()
    
    def test_run_command_failure(self):
        """Test that run_command returns False for failed commands."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="Output",
                stderr="Error"
            )
            
            result = run_command(["false"], "Failing command")
            
            assert result is False
    
    def test_run_command_exception(self):
        """Test that run_command handles exceptions gracefully."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Test exception")
            
            result = run_command(["invalid"], "Exception test")
            
            assert result is False


class TestFormatCodeWithBlack:
    """Tests for the format_code_with_black function."""
    
    @patch('cleanup_and_format.run_command')
    @patch('subprocess.run')
    def test_format_code_with_black_success(self, mock_subprocess, mock_run_command):
        """Test successful black formatting."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_run_command.return_value = True
        
        result = format_code_with_black()
        
        assert result is True
    
    @patch('cleanup_and_format.run_command')
    @patch('subprocess.run')
    def test_format_code_with_black_install_needed(self, mock_subprocess, mock_run_command):
        """Test black formatting when black needs to be installed."""
        # First call raises error (black not installed), second succeeds
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, "black"),
            MagicMock(returncode=0)
        ]
        mock_run_command.return_value = True
        
        result = format_code_with_black()
        
        assert result is True
        # Verify pip install was called
        assert mock_subprocess.call_count >= 2


class TestCheckWithFlake8:
    """Tests for the check_with_flake8 function."""
    
    @patch('cleanup_and_format.run_command')
    @patch('subprocess.run')
    def test_check_with_flake8_success(self, mock_subprocess, mock_run_command):
        """Test successful flake8 check."""
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_run_command.return_value = True
        
        result = check_with_flake8()
        
        assert result is True
    
    @patch('cleanup_and_format.run_command')
    @patch('subprocess.run')
    def test_check_with_flake8_install_needed(self, mock_subprocess, mock_run_command):
        """Test flake8 check when flake8 needs to be installed."""
        mock_subprocess.side_effect = [
            subprocess.CalledProcessError(1, "flake8"),
            MagicMock(returncode=0)
        ]
        mock_run_command.return_value = True
        
        result = check_with_flake8()
        
        assert result is True


def test_module_imports():
    """Test that all required imports are available."""
    import cleanup_and_format
    
    # Verify public names exist
    assert hasattr(cleanup_and_format, 'run_command')
    assert hasattr(cleanup_and_format, 'main')
    
    # Verify imports work
    assert callable(cleanup_and_format.run_command)