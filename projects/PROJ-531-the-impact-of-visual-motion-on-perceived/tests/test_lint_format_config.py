"""
Tests to verify that linting and formatting tools are configured correctly.
These tests check the existence of configuration files and the ability to run the tools.
"""
import os
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

def test_pyproject_toml_exists():
    """Verify pyproject.toml exists at project root."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml not found at project root"

def test_black_config_in_pyproject():
    """Verify Black configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "line-length" in content, "Black line-length setting missing"

def test_ruff_config_in_pyproject():
    """Verify Ruff configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    content = pyproject_path.read_text()
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
    assert "select" in content, "Ruff select rules missing"

def test_run_lint_script_exists():
    """Verify code/run_lint.py exists."""
    lint_script = PROJECT_ROOT / "code" / "run_lint.py"
    assert lint_script.exists(), "code/run_lint.py not found"

def test_run_format_script_exists():
    """Verify code/run_format.py exists."""
    format_script = PROJECT_ROOT / "code" / "run_format.py"
    assert format_script.exists(), "code/run_format.py not found"

def test_run_lint_script_is_valid_python():
    """Verify run_lint.py is valid Python syntax."""
    lint_script = PROJECT_ROOT / "code" / "run_lint.py"
    try:
        compile(lint_script.read_text(), lint_script, "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in run_lint.py: {e}")

def test_run_format_script_is_valid_python():
    """Verify run_format.py is valid Python syntax."""
    format_script = PROJECT_ROOT / "code" / "run_format.py"
    try:
        compile(format_script.read_text(), format_script, "exec")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in run_format.py: {e}")