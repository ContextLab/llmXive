import subprocess
import pytest
from unittest.mock import patch, MagicMock
from code.utils.lint_check import run_command, check_ruff, check_black, main
import sys
import os

@patch('code.utils.lint_check.subprocess.run')
def test_run_command_success(mock_run, capsys):
    """Test run_command returns True when exit code is 0"""
    mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
    
    result = run_command(["echo", "test"], "Test Command")
    
    assert result is True
    mock_run.assert_called_once()
    
@patch('code.utils.lint_check.subprocess.run')
def test_run_command_failure(mock_run, capsys):
    """Test run_command returns False when exit code is non-zero"""
    mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
    
    result = run_command(["false"], "Failing Command")
    
    assert result is False
    
@patch('code.utils.lint_check.subprocess.run')
def test_run_command_exception(mock_run):
    """Test run_command handles exceptions gracefully"""
    mock_run.side_effect = Exception("Process error")
    
    result = run_command(["bad"], "Bad Command")
    
    assert result is False

@patch('code.utils.lint_check.run_command')
def test_check_ruff(mock_run_command):
    """Test check_ruff calls run_command with correct arguments"""
    mock_run_command.return_value = True
    
    result = check_ruff()
    
    assert result is True
    mock_run_command.assert_called_once_with(
        ["ruff", "check", "code/"],
        "Ruff lint check"
    )

@patch('code.utils.lint_check.run_command')
def test_check_black(mock_run_command):
    """Test check_black calls run_command with correct arguments"""
    mock_run_command.return_value = True
    
    result = check_black()
    
    assert result is True
    mock_run_command.assert_called_once_with(
        ["black", "--check", "code/"],
        "Black format check"
    )

@patch('code.utils.lint_check.check_ruff')
@patch('code.utils.lint_check.check_black')
@patch('code.utils.lint_check.sys.exit')
def test_main_all_pass(mock_exit, mock_black, mock_ruff):
    """Test main exits with 0 when all checks pass"""
    mock_ruff.return_value = True
    mock_black.return_value = True
    
    main()
    
    mock_exit.assert_called_once_with(0)

@patch('code.utils.lint_check.check_ruff')
@patch('code.utils.lint_check.check_black')
@patch('code.utils.lint_check.sys.exit')
def test_main_ruff_fails(mock_exit, mock_black, mock_ruff):
    """Test main exits with 1 when ruff fails"""
    mock_ruff.return_value = False
    mock_black.return_value = True
    
    main()
    
    mock_exit.assert_called_once_with(1)

@patch('code.utils.lint_check.check_ruff')
@patch('code.utils.lint_check.check_black')
@patch('code.utils.lint_check.sys.exit')
def test_main_black_fails(mock_exit, mock_black, mock_ruff):
    """Test main exits with 1 when black fails"""
    mock_ruff.return_value = True
    mock_black.return_value = False
    
    main()
    
    mock_exit.assert_called_once_with(1)

@patch('code.utils.lint_check.check_ruff')
@patch('code.utils.lint_check.check_black')
@patch('code.utils.lint_check.sys.exit')
def test_main_both_fail(mock_exit, mock_black, mock_ruff):
    """Test main exits with 1 when both fail"""
    mock_ruff.return_value = False
    mock_black.return_value = False
    
    main()
    
    mock_exit.assert_called_once_with(1)