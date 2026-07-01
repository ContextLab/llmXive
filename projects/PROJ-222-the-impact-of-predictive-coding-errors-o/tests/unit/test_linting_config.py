"""
Unit tests for the linting configuration module.
Verifies that the configuration constants and helper functions exist and return expected types.
"""
import sys
import os

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "code"))

def test_ruff_command_exists():
    """Test that RUFF_COMMAND is defined and is a list."""
    from config_linting import RUFF_COMMAND
    assert isinstance(RUFF_COMMAND, list), "RUFF_COMMAND must be a list"
    assert len(RUFF_COMMAND) > 0, "RUFF_COMMAND must not be empty"
    assert "ruff" in RUFF_COMMAND[0], "RUFF_COMMAND must start with 'ruff'"

def test_black_command_exists():
    """Test that BLACK_COMMAND is defined and is a list."""
    from config_linting import BLACK_COMMAND
    assert isinstance(BLACK_COMMAND, list), "BLACK_COMMAND must be a list"
    assert len(BLACK_COMMAND) > 0, "BLACK_COMMAND must not be empty"
    assert "black" in BLACK_COMMAND[0], "BLACK_COMMAND must start with 'black'"

def test_get_ruff_command():
    """Test that get_ruff_command returns a list."""
    from config_linting import get_ruff_command
    cmd = get_ruff_command()
    assert isinstance(cmd, list), "get_ruff_command must return a list"
    assert len(cmd) > 0

def test_get_black_command():
    """Test that get_black_command returns a list."""
    from config_linting import get_black_command
    cmd = get_black_command()
    assert isinstance(cmd, list), "get_black_command must return a list"
    assert len(cmd) > 0