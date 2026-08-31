"""
Tests for linting configuration and runner utilities.
"""
import subprocess
from pathlib import Path

import pytest

from code.linting_config import (
    get_ruff_command,
    get_black_command,
    get_format_check_command,
    get_lint_check_command,
    run_formatter,
    run_linter,
)


def test_get_ruff_command():
    """Verify ruff command structure."""
    cmd = get_ruff_command()
    assert "ruff" in cmd
    assert "check" in cmd
    assert "pyproject.toml" in cmd


def test_get_black_command():
    """Verify black command structure."""
    cmd = get_black_command()
    assert "black" in cmd
    assert "pyproject.toml" in cmd
    assert "--line-length=88" in cmd


def test_get_format_check_command():
    """Verify black check command structure."""
    cmd = get_format_check_command()
    assert "black" in cmd
    assert "--check" in cmd


def test_get_lint_check_command():
    """Verify ruff check command matches get_ruff_command."""
    cmd_check = get_lint_check_command()
    cmd_ruff = get_ruff_command()
    assert cmd_check == cmd_ruff


def test_run_linter_executable_exists():
    """
    Verify that the linter command can be invoked (even if it fails due to code issues).
    We expect a return code, not a FileNotFoundError.
    """
    # We don't assert success (return code 0) because the codebase might have lint errors.
    # We only assert that the command runs and returns an integer exit code.
    exit_code = run_linter()
    assert isinstance(exit_code, int)


def test_run_formatter_executable_exists():
    """
    Verify that the formatter command can be invoked.
    """
    exit_code = run_formatter()
    assert isinstance(exit_code, int)
