"""
Unit tests for the linting configuration script.
These tests verify that the configuration files are valid and the
helper functions behave as expected without actually running heavy linters.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest


# Add the project root to the path to import the script logic if needed
# However, for this task, we mostly test the existence and validity of config files
# and the structure of the helper function logic.

def test_ruff_config_exists():
    """Verify that ruff.toml exists in the project root."""
    ruff_config = Path("ruff.toml")
    assert ruff_config.exists(), "ruff.toml must exist in the project root"


def test_black_config_exists():
    """Verify that black configuration is present in pyproject.toml."""
    pyproject = Path("pyproject.toml")
    assert pyproject.exists(), "pyproject.toml must exist"

    content = pyproject.read_text()
    assert "[tool.black]" in content, "pyproject.toml must contain [tool.black] section"


def test_pyproject_dependencies():
    """Verify that dev dependencies include ruff and black."""
    pyproject = Path("pyproject.toml")
    content = pyproject.read_text()

    # Check for optional dependencies section
    assert "ruff" in content, "ruff should be listed in dependencies or optional-dependencies"
    assert "black" in content, "black should be listed in dependencies or optional-dependencies"


def test_linting_config_script_exists():
    """Verify that the helper script exists and is syntactically valid."""
    script_path = Path("code/linting_config.py")
    assert script_path.exists(), "code/linting_config.py must exist"

    # Compile check
    try:
        with open(script_path) as f:
            compile(f.read(), script_path, 'exec')
    except SyntaxError as e:
        pytest.fail(f"Syntax error in code/linting_config.py: {e}")


def test_run_command_logic():
    """
    Test the logic of run_command with a harmless command.
    We mock the subprocess call to ensure the logic flow is correct.
    """
    from code.linting_config import run_command

    # Test with a command that should succeed (echo)
    # Note: On Windows 'echo' is a built-in, on Unix it's a binary.
    # We use 'true' for Unix-like and 'cmd /c exit 0' for Windows,
    # but for simplicity in this test, we rely on the fact that
    # run_command handles exceptions. We will test the success path
    # with a known working command if possible, or just verify structure.

    # Since we can't easily guarantee 'echo' availability in all test envs
    # without shelling out, let's just verify the function signature and
    # that it returns a boolean.
    import subprocess
    from unittest.mock import patch, MagicMock

    with patch('code.linting_config.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        result = run_command(["echo", "test"], "Test Description")
        assert result is True
        mock_run.assert_called_once()

    with patch('code.linting_config.subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "cmd")
        result = run_command(["bad_cmd"], "Test Description")
        assert result is False

    with patch('code.linting_config.subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        result = run_command(["missing"], "Test Description")
        assert result is False
