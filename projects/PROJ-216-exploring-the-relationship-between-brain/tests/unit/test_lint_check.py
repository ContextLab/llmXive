"""
Unit tests for the linting configuration and script.
"""
import subprocess
import sys
from pathlib import Path

def test_ruff_installed():
    """Verify ruff is installed and executable."""
    result = subprocess.run(
        ["ruff", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Ruff is not installed or not in PATH"
    assert "ruff" in result.stdout.lower()

def test_black_installed():
    """Verify black is installed and executable."""
    result = subprocess.run(
        ["black", "--version"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Black is not installed or not in PATH"
    assert "black" in result.stdout.lower()

def test_ruff_config_exists():
    """Verify ruff configuration file exists."""
    config_path = Path(__file__).parent.parent.parent / "code" / ".ruff.toml"
    assert config_path.exists(), "Ruff configuration file (.ruff.toml) not found"

def test_black_config_exists():
    """Verify black configuration file exists."""
    config_path = Path(__file__).parent.parent.parent / "code" / ".black.toml"
    assert config_path.exists(), "Black configuration file (.black.toml) not found"

def test_lint_check_script_exists():
    """Verify the lint check script exists."""
    script_path = Path(__file__).parent.parent.parent / "code" / "lint_check.py"
    assert script_path.exists(), "Lint check script (lint_check.py) not found"

def test_lint_check_script_syntax():
    """Verify the lint check script has valid Python syntax."""
    script_path = Path(__file__).parent.parent.parent / "code" / "lint_check.py"
    try:
        with open(script_path, "r") as f:
            compile(f.read(), script_path, "exec")
    except SyntaxError as e:
        assert False, f"Syntax error in lint_check.py: {e}"