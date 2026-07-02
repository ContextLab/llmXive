"""
Unit tests for the linting and formatting configuration module.

These tests verify that the lint_config module correctly constructs
commands and handles execution logic. They do not actually run the
linters (which would be integration tests), but verify the command
generation logic.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to import code/lint_config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from lint_config import (
    FLAKE8_CONFIG,
    BLACK_CONFIG,
    run_command,
    check_linting,
    run_formatting,
    fix_formatting
)

class TestLintConfig(unittest.TestCase):
    
    def test_flake8_config_defaults(self):
        """Verify flake8 configuration defaults."""
        self.assertEqual(FLAKE8_CONFIG["max-line-length"], 88)
        self.assertIn("E203", FLAKE8_CONFIG["extend-ignore"])
        self.assertIn("code/", FLAKE8_CONFIG["exclude"])
    
    def test_black_config_defaults(self):
        """Verify black configuration defaults."""
        self.assertEqual(BLACK_CONFIG["line-length"], 88)
        self.assertIn("py311", BLACK_CONFIG["target-version"])
    
    @patch('subprocess.run')
    def test_run_command_success(self, mock_run):
        """Test run_command with a successful execution."""
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        
        result = run_command(["echo", "hello"], "Test Action")
        
        self.assertTrue(result)
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_run_command_failure(self, mock_run):
        """Test run_command with a failed execution."""
        mock_run.return_value = MagicMock(returncode=1, stdout="Error message")
        
        result = run_command(["false"], "Test Action")
        
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_run_command_not_found(self, mock_run):
        """Test run_command when command is not found."""
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        result = run_command(["nonexistent_command"], "Test Action")
        
        self.assertFalse(result)
    
    @patch('lint_config.run_command')
    def test_check_linting_calls_run_command(self, mock_run):
        """Verify check_linting constructs the correct flake8 command."""
        mock_run.return_value = True
        
        check_linting()
        
        # Verify run_command was called
        mock_run.assert_called_once()
        # Get the command passed to run_command
        call_args = mock_run.call_args[0][0]
        
        # Check for key flake8 arguments
        self.assertIn("-m", call_args)
        self.assertIn("flake8", call_args)
        self.assertIn("--max-line-length", call_args)
        self.assertIn("88", call_args)
    
    @patch('lint_config.run_command')
    def test_run_formatting_calls_run_command(self, mock_run):
        """Verify run_formatting constructs the correct black command."""
        mock_run.return_value = True
        
        run_formatting()
        
        # Verify run_command was called
        mock_run.assert_called_once()
        # Get the command passed to run_command
        call_args = mock_run.call_args[0][0]
        
        # Check for key black arguments
        self.assertIn("-m", call_args)
        self.assertIn("black", call_args)
        self.assertIn("--check", call_args)
    
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_fix_formatting_calls_subprocess(self, mock_print, mock_run):
        """Verify fix_formatting calls isort and black subprocesses."""
        # Mock subprocess to avoid actual execution
        mock_run.return_value = MagicMock(returncode=0)
        
        fix_formatting()
        
        # Check that subprocess.run was called at least twice (isort + black)
        self.assertGreaterEqual(mock_run.call_count, 2)
        
        # Verify isort was called
        isort_calls = [c for c in mock_run.call_args_list if 'isort' in str(c)]
        self.assertTrue(len(isort_calls) > 0)
        
        # Verify black was called
        black_calls = [c for c in mock_run.call_args_list if 'black' in str(c)]
        self.assertTrue(len(black_calls) > 0)

if __name__ == '__main__':
    unittest.main()
