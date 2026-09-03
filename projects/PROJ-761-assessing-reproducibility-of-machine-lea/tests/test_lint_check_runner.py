"""
Tests for the lint check runner script.
Verifies that the runner correctly identifies success/failure states.
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock
from code.run_lint_checks import run_command, main

def test_run_command_success():
    """Test that run_command returns True for exit code 0."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        # Mock print to suppress output during test
        with patch('builtins.print'):
            result = run_command(["echo", "test"], "Test Check")
            assert result is True

def test_run_command_failure():
    """Test that run_command returns False for non-zero exit code."""
    with patch('subprocess.run') as mock_run:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        with patch('builtins.print'):
            result = run_command(["false"], "Test Check")
            assert result is False

def test_run_command_not_found():
    """Test that run_command returns False if command is not found."""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError("Command not found")
        
        with patch('builtins.print'):
            result = run_command(["nonexistent_cmd"], "Test Check")
            assert result is False

def test_main_exits_correctly_on_success():
    """Test that main exits with 0 if all checks pass."""
    # Mock run_command to always return True
    with patch('code.run_lint_checks.run_command', return_value=True):
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print'):
                with patch('os.chdir'):
                    main()
                    mock_exit.assert_called_with(0)

def test_main_exits_correctly_on_failure():
    """Test that main exits with 1 if any check fails."""
    # Mock run_command to fail on the second check
    with patch('code.run_lint_checks.run_command') as mock_run:
        mock_run.side_effect = [True, False]
        with patch('sys.exit') as mock_exit:
            with patch('builtins.print'):
                with patch('os.chdir'):
                    main()
                    mock_exit.assert_called_with(1)