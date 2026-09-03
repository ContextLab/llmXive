"""
Tests for the linting and formatting verification script.

These tests verify that the run_lint_checks module functions correctly
and handles various scenarios.
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock
import pytest
from pathlib import Path
import os
import tempfile
import shutil

# Import the module under test
from code.run_lint_checks import run_command, main


class TestRunCommand:
    """Tests for the run_command function."""
    
    def test_successful_command(self):
        """Test that run_command returns True for successful commands."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout='',
                stderr='',
                returncode=0
            )
            
            result = run_command(['echo', 'test'], 'Test Command')
            
            assert result is True
            mock_run.assert_called_once()
    
    def test_failed_command(self):
        """Test that run_command returns False for failed commands."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                returncode=1,
                cmd=['test']
            )
            
            result = run_command(['false'], 'Test Command')
            
            assert result is False
    
    def test_file_not_found(self):
        """Test that run_command returns False when command is not found."""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            
            result = run_command(['nonexistent_command'], 'Test Command')
            
            assert result is False


class TestMain:
    """Tests for the main function."""
    
    def test_main_with_config(self, tmp_path):
        """Test main function when pyproject.toml exists."""
        # Create a temporary pyproject.toml
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.black]\nline-length = 88\n")
        
        # Change to the temp directory
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            with patch('code.run_lint_checks.run_command') as mock_run:
                # Mock both checks to succeed
                mock_run.return_value = True
                
                result = main()
                
                # Should return 0 (success) when both checks pass
                assert result == 0
                assert mock_run.call_count == 2
        finally:
            # Restore original directory
            os.chdir(original_cwd)
    
    def test_main_without_config(self, tmp_path):
        """Test main function when pyproject.toml is missing."""
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            result = main()
            
            # Should return 1 (failure) when config is missing
            assert result == 1
        finally:
            os.chdir(original_cwd)
    
    def test_main_with_failing_check(self, tmp_path):
        """Test main function when one check fails."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.black]\nline-length = 88\n")
        
        original_cwd = Path.cwd()
        os.chdir(tmp_path)
        
        try:
            with patch('code.run_lint_checks.run_command') as mock_run:
                # First check succeeds, second fails
                mock_run.side_effect = [True, False]
                
                result = main()
                
                # Should return 1 (failure) when any check fails
                assert result == 1
        finally:
            os.chdir(original_cwd)