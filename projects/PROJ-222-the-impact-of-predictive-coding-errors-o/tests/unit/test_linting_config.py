"""
Unit tests for linting and formatting configuration.
"""
import sys
from code.config_linting import get_ruff_command, get_black_command

def test_get_ruff_command_check():
    """Test that get_ruff_command returns the correct command for checking."""
    cmd = get_ruff_command(action="check")
    assert "ruff" in " ".join(cmd)
    assert "check" in cmd
    assert "code/" in cmd

def test_get_ruff_command_fix():
    """Test that get_ruff_command returns the correct command for fixing."""
    cmd = get_ruff_command(action="check", fix=True)
    assert "--fix" in cmd

def test_get_black_command_check():
    """Test that get_black_command returns the correct command for checking."""
    cmd = get_black_command(check=True)
    assert "black" in " ".join(cmd)
    assert "--check" in cmd
    assert "code/" in cmd

def test_get_black_command_format():
    """Test that get_black_command returns the correct command for formatting."""
    cmd = get_black_command(check=False)
    assert "--check" not in cmd
    assert "code/" in cmd