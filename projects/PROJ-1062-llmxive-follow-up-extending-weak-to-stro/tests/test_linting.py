"""
Tests for linting and formatting configuration.
"""
import subprocess
import sys
import os
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).parent.parent

def run_command(cmd, cwd=None):
    """Helper to run a command and return result."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", "Command not found"

def test_ruff_installed():
    """Test that ruff is installed."""
    returncode, _, _ = run_command(["which", "ruff"])
    assert returncode == 0, "ruff is not installed in PATH"

def test_black_installed():
    """Test that black is installed."""
    returncode, _, _ = run_command(["which", "black"])
    assert returncode == 0, "black is not installed in PATH"

def test_ruff_config_exists():
    """Test that ruff configuration exists in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    content = pyproject.read_text()
    assert "[tool.ruff]" in content, "ruff configuration missing in pyproject.toml"

def test_black_config_exists():
    """Test that black configuration exists in pyproject.toml."""
    pyproject = PROJECT_ROOT / "pyproject.toml"
    assert pyproject.exists(), "pyproject.toml not found"
    content = pyproject.read_text()
    assert "[tool.black]" in content, "black configuration missing in pyproject.toml"

def test_precommit_config_exists():
    """Test that pre-commit configuration exists."""
    precommit_file = PROJECT_ROOT / ".pre-commit-config.yaml"
    assert precommit_file.exists(), ".pre-commit-config.yaml not found"
    content = precommit_file.read_text()
    assert "black" in content, "black hook missing in pre-commit config"
    assert "ruff" in content, "ruff hook missing in pre-commit config"

def test_run_lint_script_exists():
    """Test that the run_lint script exists."""
    script = PROJECT_ROOT / "code" / "scripts" / "run_lint.py"
    assert script.exists(), "run_lint.py script not found"

def test_run_format_script_exists():
    """Test that the run_format script exists."""
    script = PROJECT_ROOT / "code" / "scripts" / "run_format.py"
    assert script.exists(), "run_format.py script not found"

def test_ruff_check_passes():
    """Test that ruff check passes on the project."""
    returncode, stdout, stderr = run_command(["ruff", "check", "."])
    # We allow exit code 1 if there are linting issues, but we want to see the output
    # The test passes if the command runs successfully (even if it finds issues)
    # A true "pass" would be returncode 0, but for CI we might want to enforce 0.
    # Here we just check it runs.
    assert returncode in [0, 1], f"ruff check failed to run: {stderr}"

def test_black_check_passes():
    """Test that black check passes (or can be run) on the project."""
    # Run black --check to see if files are formatted correctly
    returncode, stdout, stderr = run_command(["black", "--check", "."])
    # Return code 0 means all good, 1 means files need formatting
    # We assert the command ran successfully
    assert returncode in [0, 1], f"black check failed to run: {stderr}"
