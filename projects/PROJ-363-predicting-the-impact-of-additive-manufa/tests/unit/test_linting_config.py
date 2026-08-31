import pytest
import subprocess
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))
from linting_config import run_command, check_linting, check_formatting, fix_linting, fix_formatting

class TestRunCommand:
    """Tests for the run_command function"""

    def test_run_command_success(self):
        """Test that run_command returns True for successful command"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="Success output",
                stderr="",
                returncode=0
            )
            
            result = run_command(["echo", "hello"], "Test command")
            
            assert result is True
            mock_run.assert_called_once()

    def test_run_command_failure(self):
        """Test that run_command returns False for failed command"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "cmd", stderr="Error message")
            
            result = run_command(["false"], "Failing command")
            
            assert result is False

    def test_run_command_exception(self):
        """Test that run_command returns False for unexpected exceptions"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Unexpected error")
            
            result = run_command(["test"], "Exception command")
            
            assert result is False

class TestCheckLinting:
    """Tests for the check_linting function"""

    @patch('linting_config.run_command')
    def test_check_linting_ruff_not_installed(self, mock_run_command):
        """Test check_linting when ruff is not installed"""
        mock_run_command.return_value = False
        
        result = check_linting()
        
        assert result is False
        mock_run_command.assert_called()

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_check_linting_code_dir_not_exists(self, mock_path, mock_run_command):
        """Test check_linting when code directory does not exist"""
        mock_path.return_value.exists.return_value = False
        mock_run_command.return_value = True  # Ruff is available
        
        result = check_linting()
        
        assert result is True
        # Should not try to run ruff check on non-existent directory

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_check_linting_success(self, mock_path, mock_run_command):
        """Test successful linting check"""
        mock_path.return_value.exists.return_value = True
        mock_run_command.return_value = True  # Ruff check passes
        
        result = check_linting()
        
        assert result is True

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_check_linting_failure(self, mock_path, mock_run_command):
        """Test failed linting check"""
        mock_path.return_value.exists.return_value = True
        mock_run_command.return_value = False  # Ruff check fails
        
        result = check_linting()
        
        assert result is False

class TestCheckFormatting:
    """Tests for the check_formatting function"""

    @patch('linting_config.run_command')
    def test_check_formatting_black_not_installed(self, mock_run_command):
        """Test check_formatting when black is not installed"""
        mock_run_command.return_value = False
        
        result = check_formatting()
        
        assert result is False

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_check_formatting_code_dir_not_exists(self, mock_path, mock_run_command):
        """Test check_formatting when code directory does not exist"""
        mock_path.return_value.exists.return_value = False
        mock_run_command.return_value = True  # Black is available
        
        result = check_formatting()
        
        assert result is True

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_check_formatting_success(self, mock_path, mock_run_command):
        """Test successful formatting check"""
        mock_path.return_value.exists.return_value = True
        mock_run_command.return_value = True  # Black check passes
        
        result = check_formatting()
        
        assert result is True

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_check_formatting_failure(self, mock_path, mock_run_command):
        """Test failed formatting check"""
        mock_path.return_value.exists.return_value = True
        mock_run_command.return_value = False  # Black check fails
        
        result = check_formatting()
        
        assert result is False

class TestFixLinting:
    """Tests for the fix_linting function"""

    @patch('linting_config.run_command')
    def test_fix_linting_ruff_not_installed(self, mock_run_command):
        """Test fix_linting when ruff is not installed"""
        mock_run_command.return_value = False
        
        result = fix_linting()
        
        assert result is False

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_fix_linting_code_dir_not_exists(self, mock_path, mock_run_command):
        """Test fix_linting when code directory does not exist"""
        mock_path.return_value.exists.return_value = False
        mock_run_command.return_value = True  # Ruff is available
        
        result = fix_linting()
        
        assert result is True

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_fix_linting_success(self, mock_path, mock_run_command):
        """Test successful linting fix"""
        mock_path.return_value.exists.return_value = True
        mock_run_command.return_value = True  # Ruff fix succeeds
        
        result = fix_linting()
        
        assert result is True

class TestFixFormatting:
    """Tests for the fix_formatting function"""

    @patch('linting_config.run_command')
    def test_fix_formatting_black_not_installed(self, mock_run_command):
        """Test fix_formatting when black is not installed"""
        mock_run_command.return_value = False
        
        result = fix_formatting()
        
        assert result is False

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_fix_formatting_code_dir_not_exists(self, mock_path, mock_run_command):
        """Test fix_formatting when code directory does not exist"""
        mock_path.return_value.exists.return_value = False
        mock_run_command.return_value = True  # Black is available
        
        result = fix_formatting()
        
        assert result is True

    @patch('linting_config.run_command')
    @patch('linting_config.Path')
    def test_fix_formatting_success(self, mock_path, mock_run_command):
        """Test successful formatting fix"""
        mock_path.return_value.exists.return_value = True
        mock_run_command.return_value = True  # Black fix succeeds
        
        result = fix_formatting()
        
        assert result is True

@pytest.mark.integration
def test_integration_run_command():
    """Integration test for run_command with a real command"""
    result = run_command([sys.executable, "--version"], "Python version check")
    assert result is True