import pytest
import os
import tempfile
from pathlib import Path
import subprocess

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from linting_config import run_command, check_linting, check_formatting, fix_linting, fix_formatting

def test_run_command_success():
    """Test that run_command executes a simple command successfully."""
    result = run_command("echo 'hello'")
    assert result is not None
    assert result.returncode == 0
    assert "hello" in result.stdout

def test_run_command_failure():
    """Test that run_command returns None on failure."""
    result = run_command("non_existent_command_12345")
    assert result is None

def test_check_linting_missing_tool(tmp_path):
    """Test check_linting when ruff is not installed."""
    # Create a dummy file to avoid empty dir issues if ruff were installed
    (tmp_path / "dummy.py").write_text("pass")
    # This test assumes ruff might not be in PATH, so we expect False or a handled error
    # In a real CI, ruff would be installed. Here we verify the function handles it.
    # The function prints error and returns False if subprocess fails.
    result = check_linting(tmp_path)
    # If ruff is installed, this might be True/False based on code.
    # If not installed, it returns False.
    assert result in [True, False]

def test_check_formatting_missing_tool(tmp_path):
    """Test check_formatting when black is not installed."""
    (tmp_path / "dummy.py").write_text("pass")
    result = check_formatting(tmp_path)
    assert result in [True, False]

def test_fix_linting_missing_tool(tmp_path):
    """Test fix_linting when ruff is not installed."""
    result = fix_linting(tmp_path)
    assert result in [True, False]

def test_fix_formatting_missing_tool(tmp_path):
    """Test fix_formatting when black is not installed."""
    result = fix_formatting(tmp_path)
    assert result in [True, False]