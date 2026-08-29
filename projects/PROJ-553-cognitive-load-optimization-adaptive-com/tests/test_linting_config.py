"""
Tests for the linting configuration utilities.

These tests verify that the command generation functions produce
the expected command structures and that the main entry point
behaves correctly when tools are missing.
"""
import subprocess
import sys
from unittest.mock import patch, MagicMock
from pathlib import Path

# Import the module under test
from code.linting_config import (
    get_ruff_command,
    get_black_command,
    get_format_check_command,
    get_lint_check_command,
    run_formatter,
    run_linter,
    main,
    PROJECT_ROOT
)

def test_get_ruff_command_check():
    """Test that get_ruff_command generates the correct check command."""
    cmd = get_ruff_command(check=True)
    assert "ruff" in cmd
    assert "check" in cmd
    assert "--exit-non-zero-on-fix" in cmd
    assert str(PROJECT_ROOT) in cmd

def test_get_ruff_command_fix():
    """Test that get_ruff_command generates the correct fix command."""
    cmd = get_ruff_command(check=False)
    assert "ruff" in cmd
    assert "check" in cmd
    assert "--fix" in cmd
    assert "--exit-non-zero-on-fix" not in cmd
    assert str(PROJECT_ROOT) in cmd

def test_get_black_command_check():
    """Test that get_black_command generates the correct check command."""
    cmd = get_black_command(check=True)
    assert "black" in cmd
    assert "--check" in cmd
    assert "--diff" in cmd
    assert str(PROJECT_ROOT) in cmd

def test_get_black_command_format():
    """Test that get_black_command generates the correct format command."""
    cmd = get_black_command(check=False)
    assert "black" in cmd
    assert "--check" not in cmd
    assert "--diff" not in cmd
    assert str(PROJECT_ROOT) in cmd

def test_get_format_check_command():
    """Test that get_format_check_command returns the black check command."""
    cmd = get_format_check_command()
    assert cmd == get_black_command(check=True)

def test_get_lint_check_command():
    """Test that get_lint_check_command returns the ruff check command."""
    cmd = get_lint_check_command()
    assert cmd == get_ruff_command(check=True)

@patch('subprocess.run')
def test_run_formatter_success(mock_run):
    """Test run_formatter when subprocess succeeds."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    exit_code = run_formatter(check=True)
    assert exit_code == 0
    mock_run.assert_called_once()

@patch('subprocess.run')
def test_run_formatter_failure(mock_run):
    """Test run_formatter when subprocess fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_run.return_value = mock_result
    
    exit_code = run_formatter(check=True)
    assert exit_code == 1

@patch('subprocess.run')
def test_run_formatter_not_found(mock_run):
    """Test run_formatter when black is not found."""
    mock_run.side_effect = FileNotFoundError("black not found")
    
    exit_code = run_formatter(check=True)
    assert exit_code == 1

@patch('subprocess.run')
def test_run_linter_success(mock_run):
    """Test run_linter when subprocess succeeds."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    exit_code = run_linter(check=True)
    assert exit_code == 0
    mock_run.assert_called_once()

@patch('subprocess.run')
def test_run_linter_failure(mock_run):
    """Test run_linter when subprocess fails."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_run.return_value = mock_result
    
    exit_code = run_linter(check=True)
    assert exit_code == 1

@patch('subprocess.run')
def test_run_linter_not_found(mock_run):
    """Test run_linter when ruff is not found."""
    mock_run.side_effect = FileNotFoundError("ruff not found")
    
    exit_code = run_linter(check=True)
    assert exit_code == 1

@patch('code.linting_config.run_linter')
@patch('code.linting_config.run_formatter')
def test_main_success(mock_format, mock_lint):
    """Test main() when both checks pass."""
    mock_lint.return_value = 0
    mock_format.return_value = 0
    
    with patch('sys.exit') as mock_exit:
        main()
        mock_exit.assert_called_once_with(0)

@patch('code.linting_config.run_linter')
@patch('code.linting_config.run_formatter')
def test_main_lint_failure(mock_format, mock_lint):
    """Test main() when linter fails."""
    mock_lint.return_value = 1
    mock_format.return_value = 0
    
    with patch('sys.exit') as mock_exit:
        main()
        mock_exit.assert_called_once_with(1)

@patch('code.linting_config.run_linter')
@patch('code.linting_config.run_formatter')
def test_main_format_failure(mock_format, mock_lint):
    """Test main() when formatter fails."""
    mock_lint.return_value = 0
    mock_format.return_value = 1
    
    with patch('sys.exit') as mock_exit:
        main()
        mock_exit.assert_called_once_with(1)

@patch('code.linting_config.run_linter')
@patch('code.linting_config.run_formatter')
def test_main_both_failure(mock_format, mock_lint):
    """Test main() when both checks fail."""
    mock_lint.return_value = 1
    mock_format.return_value = 1
    
    with patch('sys.exit') as mock_exit:
        main()
        mock_exit.assert_called_once_with(1)